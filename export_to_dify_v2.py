# -*- coding: utf-8 -*-
"""
Flow CS Hub JSON → Dify KB CSV export v2

v1 대비 확장:
- 연락처 신규 스키마 대응 (담당자, 내선, 담당자직통, 학원등록번호)
- 본사 6부서 포함
- 학부모 응대·CS 감탄·캠퍼스별 상담자료 추가
- 반형태 68건 + 수익코드 68건 추가
- 행정 매뉴얼의 본문/markdown 구조 통합

총 예상: 356건 (연락처 33 + 수강료 66 + 행정 182 + 학부모 16 + CS감탄 53 + 캠퍼스별 6)
"""
import sys, csv, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\flowedu1\신사업전략팀\03_AI_TF\03_CS상담플랫폼\챗봇 만들기\cs-db-v2\webapp-mockup")
DATA = BASE / "data"
OUT = BASE / "dify-kb"
OUT.mkdir(exist_ok=True)

contacts = json.loads((DATA / "contacts.json").read_text(encoding='utf-8'))
tuitions = json.loads((DATA / "tuition.json").read_text(encoding='utf-8'))
admins = json.loads((DATA / "admin.json").read_text(encoding='utf-8'))
pr = json.loads((DATA / "parent-response.json").read_text(encoding='utf-8'))
ca = json.loads((DATA / "cs-appreciation.json").read_text(encoding='utf-8'))
cg = json.loads((DATA / "campus-guide.json").read_text(encoding='utf-8'))

rows = []

# ============ 1) 연락처 ============
for c in contacts:
    ct = c['content']
    parts = []
    if ct.get('위치'):        parts.append(f"위치: {ct['위치']}")
    if ct.get('직통번호'):    parts.append(f"직통번호: {ct['직통번호']}")
    if ct.get('대표번호'):    parts.append(f"대표번호: {ct['대표번호']}")
    if ct.get('담당자'):      parts.append(f"담당자: {ct['담당자']}")
    if ct.get('내선'):        parts.append(f"내선: {ct['내선']}")
    if ct.get('내선번호'):    parts.append(f"내선번호: {ct['내선번호']}")
    if ct.get('담당자직통'):  parts.append(f"담당자직통: {ct['담당자직통']}")
    if ct.get('학원등록번호'): parts.append(f"학원등록번호: {ct['학원등록번호']}")
    if ct.get('비고'):        parts.append(f"비고: {ct['비고']}")
    rows.append({
        '분류': f"연락처 · {c['subcategory']}",
        '제목': c['title'],
        '본문': " | ".join(parts),
    })

# ============ 2) 수강료 ============
for t in tuitions:
    ct = t['content']
    parts = []
    if ct.get('26년_수강료'):
        parts.append(f"26년 수강료: {ct['26년_수강료']:,}원")
    if ct.get('25년_수강료') and ct.get('인상액') is not None:
        up = ct['인상액']
        if up > 0:   parts.append(f"25년 대비 {up:,}원 인상 (25년: {ct['25년_수강료']:,}원)")
        elif up < 0: parts.append(f"25년 대비 {abs(up):,}원 인하 (25년: {ct['25년_수강료']:,}원)")
        else:        parts.append(f"25년과 동일 ({ct['25년_수강료']:,}원)")
    if ct.get('사업부'): parts.append(f"사업부: {ct['사업부']}")
    if ct.get('브랜드'): parts.append(f"브랜드: {ct['브랜드']}")
    if ct.get('회당'):   parts.append(f"회당: {ct['회당']}")
    if ct.get('과정'):   parts.append(f"과정: {ct['과정']}")
    if ct.get('비고'):   parts.append(f"비고: {ct['비고']}")
    rows.append({
        '분류': f"수강료 · {t['subcategory']}",
        '제목': t['title'],
        '본문': " | ".join(parts),
    })

# ============ 3) 행정 매뉴얼 (3종 스키마 통합) ============
for a in admins:
    c = a['content']
    sub = a['subcategory']
    if sub.startswith('Ⅲ'):  # 반형태
        parts = [
            f"고유번호 {c.get('고유번호','')}",
            f"교육관 {c.get('교육관','')}",
            f"브랜드 {c.get('브랜드','')}",
            f"캠퍼스 {c.get('캠퍼스','')}",
            f"관리자 {c.get('관리자','')}" if c.get('관리자') else '',
            f"반형태: {c.get('반형태','')}" if c.get('반형태') else '',
            f"담당 CS: {c.get('담당 CS','')}" if c.get('담당 CS') else '',
            f"건물: {c.get('건물명','')}" if c.get('건물명') else '',
            f"층: {c.get('층수','')}" if c.get('층수') else '',
            f"학원등록번호: {c.get('학원등록번호','')}" if c.get('학원등록번호') else '',
        ]
        body = " | ".join([p for p in parts if p])
    elif sub.startswith('Ⅳ'):  # 수익코드
        parts = [
            f"고유번호 {c.get('고유번호','')}",
            f"경로: {c.get('수익경로','')}",
            f"교육관 {c.get('교육관','')}",
            f"브랜드 {c.get('브랜드','')}",
            f"캠퍼스 {c.get('캠퍼스','')}",
            f"세부 {c.get('세부캠퍼스','')}" if c.get('세부캠퍼스') else '',
            f"비고 {c.get('비고','')}" if c.get('비고') else '',
        ]
        body = " | ".join([p for p in parts if p])
    else:  # 기존 매뉴얼 (본문 or markdown)
        body = c.get('본문') or c.get('markdown') or " | ".join(f"{k}: {v}" for k,v in c.items() if v)
    rows.append({
        '분류': f"매뉴얼 · {sub}",
        '제목': a['title'],
        '본문': body,
    })

# ============ 4) 학부모 응대 매뉴얼 ============
for p in pr:
    c = p['content']
    parts = []
    if c.get('markdown'):
        parts.append(c['markdown'])
    if c.get('recommended'):
        parts.append(f"[권장 답변] {c['recommended']}")
    if c.get('avoid'):
        parts.append(f"[피해야 할 응대] {c['avoid']}")
    rows.append({
        '분류': f"학부모응대 · {p['subcategory']}",
        '제목': p['title'],
        '본문': "\n\n".join(parts) if parts else "",
    })

# ============ 5) CS 감탄 매뉴얼 ============
for x in ca:
    c = x['content']
    parts = []
    if c.get('markdown'):
        parts.append(c['markdown'])
    if c.get('recommended'):
        parts.append(f"[권장] {c['recommended']}")
    if c.get('avoid'):
        parts.append(f"[지양] {c['avoid']}")
    rows.append({
        '분류': f"CS감탄 · {x['subcategory']}",
        '제목': x['title'],
        '본문': "\n\n".join(parts) if parts else "",
    })

# ============ 6) 캠퍼스별 상담자료 ============
for x in cg:
    c = x['content']
    parts = []
    if c.get('markdown'):
        parts.append(c['markdown'])
    if c.get('recommended'):
        parts.append(f"[권장] {c['recommended']}")
    if c.get('avoid'):
        parts.append(f"[지양] {c['avoid']}")
    rows.append({
        '분류': f"캠퍼스별상담 · {x['subcategory']}",
        '제목': x['title'],
        '본문': "\n\n".join(parts) if parts else "",
    })

# ============ CSV 출력 ============
out_csv = OUT / "flow-cs-hub-kb-v2.csv"
with out_csv.open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['분류', '제목', '본문'])
    w.writeheader()
    for r in rows:
        w.writerow(r)

# ============ 요약 ============
from collections import Counter
by_cat = Counter(r['분류'].split(' · ')[0] for r in rows)
print(f"생성: {out_csv}")
print(f"총 청크: {len(rows)}건")
for k, v in by_cat.items():
    print(f"  · {k}: {v}건")
size_kb = out_csv.stat().st_size / 1024
print(f"\n파일 크기: {size_kb:.1f} KB")
