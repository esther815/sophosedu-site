"""입시 노트 갱신: data/news.json → brief.html 다시 만들기 + index.html 첫 화면 '입시 노트' 미리보기(최신 3건) 교체.
실행: 저장소 맨 위 폴더에서  python3 tools/update_brief.py"""
import os, re, sys, subprocess, json, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
B = os.path.join(ROOT, 'tools', 'brief.py')
CATS = ['수능', '논술', '서·논술형', '대입', '고입', '내신', '교육정책']

# 1) news.json 점검
items = json.load(open(os.path.join(ROOT, 'data', 'news.json'), encoding='utf8'))
need = ['id', 'date', 'cat', 'source', 'url', 'title', 'deck', 'points', 'note']
ids, urls, bad, warn = set(), set(), [], []
for x in items:
    for k in need:
        if not x.get(k): bad.append(f"{x.get('id','?')}: '{k}' 비어 있음")
    if x.get('cat') not in CATS: bad.append(f"{x.get('id')}: 분류 '{x.get('cat')}'는 쓸 수 없음 ({', '.join(CATS)})")
    if len(x.get('points', [])) != 3: bad.append(f"{x.get('id')}: 세 줄 요약은 정확히 3개")
    try: datetime.date.fromisoformat(x.get('date', ''))
    except Exception: bad.append(f"{x.get('id')}: 날짜는 YYYY-MM-DD")
    if x.get('id') in ids: bad.append(f"id 중복: {x.get('id')}")
    if x.get('url') in urls: warn.append(f"같은 원문을 두 건으로 나눔: {x.get('id')} — 의도한 것인지 확인")
    ids.add(x.get('id')); urls.add(x.get('url'))
for w in warn: print('참고:', w)
if bad:
    print('고칠 곳:\n- ' + '\n- '.join(bad)); sys.exit(1)

# 2) brief.html
page = subprocess.run([sys.executable, B, 'page-file', 'index.html'], capture_output=True, text=True, check=True).stdout
open(os.path.join(ROOT, 'brief.html'), 'w', encoding='utf8').write(page)

# 3) index.html 미리보기 조각
teaser = subprocess.run([sys.executable, B, 'teaser', 'brief.html'], capture_output=True, text=True, check=True).stdout.strip()
ip = os.path.join(ROOT, 'index.html'); s = open(ip, encoding='utf8').read()
new, n = re.subn(r'(<!--BRIEF:START-->).*?(<!--BRIEF:END-->)', lambda m: m.group(1) + teaser + m.group(2), s, flags=re.S)
if n != 1: print('index.html에서 <!--BRIEF:START--> 표시를 찾지 못했습니다.'); sys.exit(1)
open(ip, 'w', encoding='utf8').write(new)
print(f'완료: 기사 {len(items)}건 · brief.html · 첫 화면 미리보기 갱신')
