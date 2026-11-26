-- 소포스 저널 · 교육 노트 알림톡 구독 발송 설정
-- Supabase 대시보드 > SQL Editor 에 통째로 붙여 넣고 한 번 실행한다. 여러 번 실행해도 안전하다.
-- 소포스(site='sophos')와 주니어솔로몬(site='solomon')이 같은 표를 함께 쓴다.
-- 전제: public.sp_profiles(id, nickname, role, grade, school) 와 public.is_admin() 이 이미 있다.

-- 1) 재원생 가족 승인 (원장만 바꾼다)
create table if not exists public.ns_enrolled (
  user_id     uuid not null references auth.users(id) on delete cascade,
  site        text not null check (site in ('sophos','solomon')),
  approved_by uuid references auth.users(id),
  approved_at timestamptz not null default now(),
  primary key (user_id, site)
);

-- 2) 구독 (본인이 켜고 끈다, 동의 기록 보관)
create table if not exists public.ns_subscriptions (
  user_id      uuid not null references auth.users(id) on delete cascade,
  site         text not null check (site in ('sophos','solomon')),
  phone        text not null check (phone ~ '^01[016789][0-9]{7,8}$'),
  is_on        boolean not null default true,
  consent_text text not null,
  consent_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  primary key (user_id, site)
);

-- 3) 보낼 기사 대기열 (야간 게시분은 아침 8시에 발송)
create table if not exists public.ns_outbox (
  news_id    text not null,
  site       text not null check (site in ('sophos','solomon')),
  payload    jsonb not null,
  created_at timestamptz not null default now(),
  sent_at    timestamptz,
  primary key (news_id, site)
);

-- 4) 발송 기록 (같은 기사·같은 사람에게 두 번 보내지 않는다)
create table if not exists public.ns_deliveries (
  news_id    text not null,
  site       text not null,
  user_id    uuid not null references auth.users(id) on delete cascade,
  status     text not null check (status in ('sent','failed','test')),
  vendor_id  text,
  error      text,
  created_at timestamptz not null default now(),
  primary key (news_id, site, user_id)
);

-- 표는 직접 읽고 쓰지 못하게 막고, 아래 함수로만 다룬다. 발송 함수는 service_role 로 접근한다.
alter table public.ns_enrolled      enable row level security;
alter table public.ns_subscriptions enable row level security;
alter table public.ns_outbox        enable row level security;
alter table public.ns_deliveries    enable row level security;
revoke all on public.ns_enrolled, public.ns_subscriptions, public.ns_outbox, public.ns_deliveries from anon, authenticated;

-- 회원: 내 상태 (재원 승인 여부 · 구독 여부 · 가린 번호)
create or replace function public.ns_my_status(p_site text)
returns jsonb language sql security definer set search_path = public stable as $$
  select jsonb_build_object(
    'enrolled', exists(select 1 from ns_enrolled e where e.user_id = auth.uid() and e.site = p_site),
    'on',       coalesce((select s.is_on from ns_subscriptions s where s.user_id = auth.uid() and s.site = p_site), false),
    'phone',    (select regexp_replace(s.phone, '^(\d{3})\d+(\d{4})$', '\1-****-\2') from ns_subscriptions s where s.user_id = auth.uid() and s.site = p_site)
  );
$$;

-- 회원: 구독 켜기·끄기 (재원 승인된 회원만)
create or replace function public.ns_subscribe(p_site text, p_phone text, p_on boolean, p_consent text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare v_phone text := regexp_replace(coalesce(p_phone,''), '[^0-9]', '', 'g');
begin
  if auth.uid() is null then raise exception 'login required'; end if;
  if not exists(select 1 from ns_enrolled where user_id = auth.uid() and site = p_site) then
    raise exception 'not enrolled';
  end if;
  if not p_on then
    update ns_subscriptions set is_on = false, updated_at = now() where user_id = auth.uid() and site = p_site;
    return ns_my_status(p_site);
  end if;
  if v_phone = '' then
    select phone into v_phone from ns_subscriptions where user_id = auth.uid() and site = p_site;
  end if;
  if v_phone is null or v_phone !~ '^01[016789][0-9]{7,8}$' then raise exception 'bad phone'; end if;
  if coalesce(p_consent,'') = '' then raise exception 'consent required'; end if;
  insert into ns_subscriptions(user_id, site, phone, is_on, consent_text, consent_at, updated_at)
  values (auth.uid(), p_site, v_phone, true, p_consent, now(), now())
  on conflict (user_id, site) do update
    set phone = excluded.phone, is_on = true, consent_text = excluded.consent_text, consent_at = now(), updated_at = now();
  return ns_my_status(p_site);
end $$;

-- 원장: 회원 명단 + 재원·구독 상태
create or replace function public.ns_admin_members(p_site text)
returns table(user_id uuid, nickname text, role text, grade text, school text, enrolled boolean, subscribed boolean)
language plpgsql security definer set search_path = public stable as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return query
    select p.id, p.nickname::text, p.role::text, p.grade::text, p.school::text,
           exists(select 1 from ns_enrolled e where e.user_id = p.id and e.site = p_site),
           exists(select 1 from ns_subscriptions s where s.user_id = p.id and s.site = p_site and s.is_on)
    from sp_profiles p
    order by 6 desc, p.nickname;
end $$;

-- 원장: 재원생 가족 승인·해제 (해제하면 구독도 꺼진다)
create or replace function public.ns_admin_set_enrolled(p_user uuid, p_site text, p_on boolean)
returns void language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  if p_on then
    insert into ns_enrolled(user_id, site, approved_by) values (p_user, p_site, auth.uid())
    on conflict (user_id, site) do nothing;
  else
    delete from ns_enrolled where user_id = p_user and site = p_site;
    update ns_subscriptions set is_on = false, updated_at = now() where user_id = p_user and site = p_site;
  end if;
end $$;

-- 원장: 발송 현황
create or replace function public.ns_admin_stats(p_site text)
returns jsonb language plpgsql security definer set search_path = public stable as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'enrolled',   (select count(*) from ns_enrolled where site = p_site),
    'subscribed', (select count(*) from ns_subscriptions s where s.site = p_site and s.is_on
                     and exists(select 1 from ns_enrolled e where e.user_id = s.user_id and e.site = p_site)),
    'pending',    (select count(*) from ns_outbox where site = p_site and sent_at is null),
    'recent', coalesce((select jsonb_agg(x order by x.at desc) from (
        select d.news_id, max(d.created_at) as at,
               count(*) filter (where d.status = 'sent')   as sent,
               count(*) filter (where d.status = 'failed') as failed,
               count(*) filter (where d.status = 'test')   as test
        from ns_deliveries d where d.site = p_site group by d.news_id
        order by max(d.created_at) desc limit 10) x), '[]'::jsonb)
  );
end $$;

revoke all on function public.ns_my_status(text), public.ns_subscribe(text,text,boolean,text),
  public.ns_admin_members(text), public.ns_admin_set_enrolled(uuid,text,boolean), public.ns_admin_stats(text) from public, anon;
grant execute on function public.ns_my_status(text), public.ns_subscribe(text,text,boolean,text),
  public.ns_admin_members(text), public.ns_admin_set_enrolled(uuid,text,boolean), public.ns_admin_stats(text) to authenticated;
