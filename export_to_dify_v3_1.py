# -*- coding: utf-8 -*-
"""
v3.1: 개행 완전 제거 · 단일 라인 강제
- Dify가 자동 분할할 곳 자체를 제거
- 모든 \n \r을 공백으로 치환
- 각 행 최대 900자 이내 목표 (1024 청크 안전)
"""
import sys, csv, json, re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\flowedu1\신사업전략팀\03_AI_TF\03_CS상담플랫폼\챗봇 만들기\cs-db-v2\webapp-mockup")
DATA = BASE / "data"
OUT = BASE / "dify-kb"
OUT.mkdir(exist_ok=True)

def flat(s):
    """개행·연속 공백 제거, 단일 라인 강제"""
    if not s: return ''
    s = str(s).replace('\r', ' ').replace('\n', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def truncate(s, maxlen=900):
    if len(s) <= maxlen: return s
    return s[:maxlen-3] + '...'

contacts = json.loads((DATA / "contacts.json").read_text(encoding='utf-8'))
tuitions = json.loads((DATA / "tuition.json").read_text(encoding='utf-8'))
admins = json.loads((DATA / "admin.json").read_text(encoding='utf-8'))
pr = json.loads((DATA / "parent-response.json").read_text(encoding='utf-8'))
ca = json.loads((DATA / "cs-appreciation.json").read_text(encoding='utf-8'))
cg = json.loads((DATA / "campus-guide.json").read_text(encoding='utf-8'))

rows = []

# 연락처
for c in contacts:
    ct = c['content']
    camp, gwan, sub = c['campus'], c['gwan'], c['subcategory']
    parts = [f"[연락처·{sub}]"]
    if sub == '캠퍼스 대표':
        parts.append(f"{camp} 캠퍼스 대표번호 {flat(ct.get('직통번호',''))}.")
        if ct.get('위치'): parts.append(f"위치 {flat(ct['위치'])}.")
        if ct.get('비고'): parts.append(f"{flat(ct['비고'])}.")
    elif sub == '본사':
        parts.append(f"본사 {gwan} 부서.")
        if ct.get('담당자'): parts.append(f"담당자 {flat(ct['담당자'])}.")
        if ct.get('내선'): parts.append(f"내선 {flat(ct['내선'])}.")
        if ct.get('위치'): parts.append(f"위치 {flat(ct['위치'])}.")
    else:
        parts.append(f"{camp} 캠퍼스 {gwan}.")
        if ct.get('위치'): parts.append(f"위치 {flat(ct['위치'])}.")
        if ct.get('직통번호'): parts.append(f"직통 {flat(ct['직통번호'])}.")
        if ct.get('대표번호'): parts.append(f"대표 {flat(ct['대표번호'])}.")
        if ct.get('담당자'): parts.append(f"담당자 {flat(ct['담당자'])}.")
        if ct.get('학원등록번호'): parts.append(f"학원등록번호 {flat(ct['학원등록번호'])}.")
        if ct.get('비고'): parts.append(f"{flat(ct['비고'])}.")
    body = flat(' '.join(parts))
    rows.append({'제목': flat(c['title']), '본문': truncate(body)})

# 수강료
for t in tuitions:
    ct = t['content']
    parts = [f"[수강료·{t['subcategory']}]", f"{t['campus']} {t['subcategory']}."]
    if ct.get('브랜드'): parts.append(f"브랜드 {ct['브랜드']}.")
    if ct.get('회당'): parts.append(f"회당 {ct['회당']}.")
    if ct.get('과정'): parts.append(f"과정 {ct['과정']}.")
    if ct.get('26년_수강료'): parts.append(f"26년 수강료 {ct['26년_수강료']:,}원.")
    if ct.get('25년_수강료') and ct.get('인상액') is not None:
        up = ct['인상액']
        if up > 0: parts.append(f"25년 {ct['25년_수강료']:,}원에서 {up:,}원 인상.")
        elif up < 0: parts.append(f"25년 {ct['25년_수강료']:,}원에서 {abs(up):,}원 인하.")
        else: parts.append(f"25년과 동일 {ct['25년_수강료']:,}원.")
    if ct.get('비고'): parts.append(f"{flat(ct['비고'])}.")
    body = flat(' '.join(parts))
    rows.append({'제목': flat(t['title']), '본문': truncate(body)})

# 행정 매뉴얼 (Ⅰ, Ⅱ만)
for a in admins:
    sub = a['subcategory']
    if sub.startswith('Ⅲ') or sub.startswith('Ⅳ'): continue
    c = a['content']
    body_raw = c.get('본문') or c.get('markdown') or ' '.join(f"{k} {v}" for k,v in c.items() if v)
    body = flat(f"[행정·{sub}] {a['title']}. {body_raw}")
    rows.append({'제목': flat(a['title']), '본문': truncate(body)})

# 학부모 응대
for p in pr:
    c = p['content']
    body_parts = [f"[학부모응대·{p['subcategory']}]", f"{p['title']}."]
    if c.get('markdown'): body_parts.append(c['markdown'])
    if c.get('recommended'): body_parts.append(f"권장: {c['recommended']}")
    if c.get('avoid'): body_parts.append(f"지양: {c['avoid']}")
    body = flat(' '.join(body_parts))
    rows.append({'제목': flat(p['title']), '본문': truncate(body)})

# CS 감탄
for x in ca:
    c = x['content']
    body_parts = [f"[CS감탄·{x['subcategory']}]", f"{x['title']}."]
    if c.get('markdown'): body_parts.append(c['markdown'])
    if c.get('recommended'): body_parts.append(f"권장: {c['recommended']}")
    if c.get('avoid'): body_parts.append(f"지양: {c['avoid']}")
    body = flat(' '.join(body_parts))
    rows.append({'제목': flat(x['title']), '본문': truncate(body)})

# 캠퍼스별 상담자료
for x in cg:
    c = x['content']
    body_parts = [f"[캠퍼스상담·{x['subcategory']}]", f"{x['title']}."]
    if c.get('markdown'): body_parts.append(c['markdown'])
    if c.get('recommended'): body_parts.append(f"권장: {c['recommended']}")
    if c.get('avoid'): body_parts.append(f"지양: {c['avoid']}")
    body = flat(' '.join(body_parts))
    rows.append({'제목': flat(x['title']), '본문': truncate(body)})

out_csv = OUT / "flow-cs-hub-kb-v3-1.csv"
with out_csv.open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['제목', '본문'])
    w.writeheader()
    for r in rows: w.writerow(r)

lens = [len(r['본문']) for r in rows]
print(f'파일: {out_csv}')
print(f'총 행: {len(rows)}')
print(f'평균 본문: {sum(lens)//len(lens)} chars')
print(f'최대 본문: {max(lens)} chars')
print(f'최소 본문: {min(lens)} chars')
print(f'900자 초과: {sum(1 for l in lens if l > 900)}건')
print(f'파일 크기: {out_csv.stat().st_size/1024:.1f} KB')
