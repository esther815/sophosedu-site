// 입시 노트 · 교육 노트 알림톡 발송 (Supabase Edge Function: news-dispatch)
//
// 호출하는 곳
//  1) GitHub Actions — 기사가 main 에 올라가면 새 기사를 넘긴다.  헤더 x-dispatch-secret
//  2) GitHub Actions — 매일 08:00(KST) 야간 대기분을 보낸다.    {flush:true}
//  3) 원장실 '시험 발송' 버튼 — 원장 로그인 토큰.               {test:true, site}
//
// 비밀값 (Supabase > Edge Functions > Secrets) — 저장소에 넣지 않는다
//  DISPATCH_SECRET          GitHub Actions 와 같은 임의의 긴 문자열
//  ALIMTALK_MODE            off | test | live   (처음에는 test)
//  TEST_PHONE               시험 발송 받을 원장님 휴대폰 (숫자만)
//  SOLAPI_API_KEY, SOLAPI_API_SECRET
//  SOPHOS_PFID,  SOPHOS_TEMPLATE_ID    소포스 카카오 채널 발신프로필 · 승인된 템플릿
//  SOLOMON_PFID, SOLOMON_TEMPLATE_ID   주니어솔로몬 (준비되면)
//  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY 는 Supabase 가 자동으로 넣는다.

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

type Site = "sophos" | "solomon";
type Item = { id: string; title: string; points: string[]; note: string };

const env = (k: string) => Deno.env.get(k) ?? "";
const SITES: Site[] = ["sophos", "solomon"];
const db = createClient(env("SUPABASE_URL"), env("SUPABASE_SERVICE_ROLE_KEY"));
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-dispatch-secret",
};
const json = (b: unknown, s = 200) =>
  new Response(JSON.stringify(b), { status: s, headers: { ...CORS, "content-type": "application/json" } });

// 21:00~07:59 (KST) 에는 보내지 않고 대기열에 둔다
function quietHours(): boolean {
  const h = (new Date().getUTCHours() + 9) % 24;
  return h >= 21 || h < 8;
}

// 템플릿 변수 — 카카오에 심사받은 템플릿의 #{변수} 이름과 똑같아야 한다
function variables(it: Item): Record<string, string> {
  return {
    "#{제목}": it.title,
    "#{요약}": it.points.map((p, i) => `${i + 1}. ${p}`).join("\n"),
    "#{노트}": it.note,
  };
}

async function hmacHex(secret: string, data: string): Promise<string> {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(data));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

// 솔라피 알림톡 발송. 대행사를 바꾸면 이 함수만 바꾼다.
// 반환: 번호별 결과 { to: {ok, id?, error?} }
async function sendAlimtalk(site: Site, it: Item, phones: string[]) {
  const pfId = env(site === "sophos" ? "SOPHOS_PFID" : "SOLOMON_PFID");
  const templateId = env(site === "sophos" ? "SOPHOS_TEMPLATE_ID" : "SOLOMON_TEMPLATE_ID");
  if (!pfId || !templateId) throw new Error(`${site}: 발신프로필·템플릿 비밀값이 없습니다`);
  const out: Record<string, { ok: boolean; id?: string; error?: string }> = {};
  for (let i = 0; i < phones.length; i += 1000) {
    const chunk = phones.slice(i, i + 1000);
    const date = new Date().toISOString();
    const salt = crypto.randomUUID().replace(/-/g, "");
    const signature = await hmacHex(env("SOLAPI_API_SECRET"), date + salt);
    const res = await fetch("https://api.solapi.com/messages/v4/send-many/detail", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `HMAC-SHA256 apiKey=${env("SOLAPI_API_KEY")}, date=${date}, salt=${salt}, signature=${signature}`,
      },
      body: JSON.stringify({
        messages: chunk.map((to) => ({
          to,
          type: "ATA",
          kakaoOptions: { pfId, templateId, variables: variables(it), disableSms: true },
        })),
      }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = `HTTP ${res.status} ${body?.errorMessage ?? body?.message ?? ""}`.trim();
      chunk.forEach((to) => (out[to] = { ok: false, error: msg }));
      continue;
    }
    const failed = new Map<string, string>(
      (body?.failedMessageList ?? []).map((f: any) => [String(f.to), `${f.statusCode ?? ""} ${f.statusMessage ?? ""}`.trim()]),
    );
    const ids = new Map<string, string>((body?.messageList ?? []).map((m: any) => [String(m.to), String(m.messageId ?? "")]));
    chunk.forEach((to) => (out[to] = failed.has(to) ? { ok: false, error: failed.get(to) } : { ok: true, id: ids.get(to) }));
  }
  return out;
}

// 대기열에서 아직 안 보낸 기사를 보낸다
async function flush(sites: Site[]) {
  const mode = env("ALIMTALK_MODE") || "off";
  const report: unknown[] = [];
  // 개인정보 처리방침: 발송 결과는 1년이 지나면 지운다
  await db.from("ns_deliveries").delete().lt("created_at", new Date(Date.now() - 365 * 864e5).toISOString());
  const { data: rows } = await db.from("ns_outbox").select("*").in("site", sites).is("sent_at", null).order("created_at");
  for (const row of rows ?? []) {
    const site = row.site as Site, it = row.payload as Item;
    if (mode === "off") { report.push({ id: it.id, site, skipped: "ALIMTALK_MODE=off" }); continue; }
    if (mode === "test") {
      const r = env("TEST_PHONE") ? await sendAlimtalk(site, it, [env("TEST_PHONE")]) : {};
      report.push({ id: it.id, site, test: r });
      await db.from("ns_outbox").update({ sent_at: new Date().toISOString() }).eq("news_id", row.news_id).eq("site", site);
      continue;
    }
    // live: 재원 승인 + 구독 켬 + 아직 안 받은 사람
    const { data: subs } = await db.from("ns_subscriptions").select("user_id, phone").eq("site", site).eq("is_on", true);
    const { data: enr } = await db.from("ns_enrolled").select("user_id").eq("site", site);
    const { data: done } = await db.from("ns_deliveries").select("user_id").eq("site", site).eq("news_id", it.id);
    const ok = new Set((enr ?? []).map((e) => e.user_id)), sent = new Set((done ?? []).map((d) => d.user_id));
    const targets = (subs ?? []).filter((s) => ok.has(s.user_id) && !sent.has(s.user_id));
    const byPhone = new Map<string, string>(targets.map((t: any) => [String(t.phone), String(t.user_id)]));
    const result = targets.length ? await sendAlimtalk(site, it, [...byPhone.keys()]) : {};
    const recs = Object.entries(result).map(([to, r]) => ({
      news_id: it.id, site, user_id: byPhone.get(to), status: r.ok ? "sent" : "failed", vendor_id: r.id ?? null, error: r.error ?? null,
    }));
    if (recs.length) await db.from("ns_deliveries").upsert(recs, { onConflict: "news_id,site,user_id" });
    await db.from("ns_outbox").update({ sent_at: new Date().toISOString() }).eq("news_id", row.news_id).eq("site", site);
    report.push({ id: it.id, site, sent: recs.filter((r) => r.status === "sent").length, failed: recs.filter((r) => r.status === "failed").length });
  }
  return report;
}

function clean(x: any): Item | null {
  if (!x || typeof x.id !== "string" || typeof x.title !== "string" || !Array.isArray(x.points) || x.points.length !== 3) return null;
  return { id: x.id, title: String(x.title), points: x.points.map(String), note: String(x.note ?? "") };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  const body = await req.json().catch(() => ({}));
  const fromAction = !!env("DISPATCH_SECRET") && req.headers.get("x-dispatch-secret") === env("DISPATCH_SECRET");

  // 원장실 시험 발송: 원장 계정만, 가장 최근 기사 1건을 TEST_PHONE 으로
  if (body.test) {
    const user = createClient(env("SUPABASE_URL"), env("SUPABASE_ANON_KEY"), {
      global: { headers: { Authorization: req.headers.get("authorization") ?? "" } },
    });
    const { data: adm } = await user.rpc("is_admin");
    if (adm !== true) return json({ error: "admin only" }, 403);
    const site: Site = SITES.includes(body.site) ? body.site : "sophos";
    if (!env("TEST_PHONE")) return json({ error: "TEST_PHONE 비밀값이 없습니다" }, 400);
    const it = clean(body.item) ?? (await db.from("ns_outbox").select("payload").eq("site", site).order("created_at", { ascending: false }).limit(1).maybeSingle()).data?.payload;
    if (!it) return json({ error: "보낼 기사가 아직 없습니다" }, 400);
    try { return json({ test: await sendAlimtalk(site, it, [env("TEST_PHONE")]) }); }
    catch (e) { return json({ error: String((e as Error).message) }, 500); }
  }

  if (!fromAction) return json({ error: "forbidden" }, 403);

  // 새 기사 등록 → 낮이면 바로 발송, 밤이면 대기
  if (Array.isArray(body.items)) {
    const site: Site = SITES.includes(body.site) ? body.site : "sophos";
    const items = body.items.map(clean).filter(Boolean) as Item[];
    if (items.length) {
      await db.from("ns_outbox").upsert(items.map((it) => ({ news_id: it.id, site, payload: it })), { onConflict: "news_id,site", ignoreDuplicates: true });
    }
    if (quietHours()) return json({ queued: items.map((i) => i.id), note: "야간이라 08:00 에 발송" });
    try { return json({ report: await flush([site]) }); }
    catch (e) { return json({ error: String((e as Error).message) }, 500); }
  }

  if (body.flush) {
    if (quietHours()) return json({ note: "야간 — 보내지 않음" });
    try { return json({ report: await flush(SITES) }); }
    catch (e) { return json({ error: String((e as Error).message) }, 500); }
  }
  return json({ error: "nothing to do" }, 400);
});
