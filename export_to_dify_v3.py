# -*- coding: utf-8 -*-
"""
Flow CS Hub JSON → Dify KB CSV v3 (자립형 청크 최적화)

핵심 변경 (v2 대비):
- 반형태·수익코드 제외 (실제 상담 미사용)
- 각 행을 「완결형 자연어 단락」으로 재구성 (Dify 자동 분할 억제)
- Dify 청킹 설정 권장: 최대 4000 토큰 · 청크 식별자 없음(단일)
- 결과: 356행 → 약 220행 · 1행=1청크 유도

CSV 컬럼: 제목, 본문 (2컬럼 축소, 분류는 본문 첫 줄에 인라인)
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

# ==================================================
# 1) 연락처 (33행 · 자연어 완결형)
# ==================================================
for c in contacts:
    ct = c['content']
    camp = c['campus']
    gwan = c['gwan']
    sub = c['subcategory']

    body_lines = [f"[카테고리] 연락처 · {sub}"]

    if sub == '캠퍼스 대표':
        body_lines.append(f"{camp} 캠퍼스 대표번호는 {ct.get('직통번호','')}입니다.")
        if ct.get('위치'):
            body_lines.append(f"위치: {ct['위치']}")
        if ct.get('비고'):
            body_lines.append(f"참고: {ct['비고']}")
    elif sub == '본사':
        body_lines.append(f"본사 {gwan} 부서 연락처 정보입니다.")
        if ct.get('담당자'):
            body_lines.append(f"담당자: {ct['담당자']}")
        if ct.get('내선'):
            body_lines.append(f"내선번호: {ct['내선']}")
        if ct.get('위치'):
            body_lines.append(f"위치: {ct['위치']}")
    else:  # 관/시설
        body_lines.append(f"{camp} 캠퍼스 {gwan}의 연락처 및 담당자 정보입니다.")
        if ct.get('위치'):
            body_lines.append(f"위치: {ct['위치']}")
        if ct.get('직통번호'):
            body_lines.append(f"직통번호: {ct['직통번호']}")
        if ct.get('대표번호'):
            body_lines.append(f"캠퍼스 대표번호: {ct['대표번호']}")
        if ct.get('담당자'):
            body_lines.append(f"담당자 및 내선: {ct['담당자']}")
        if ct.get('학원등록번호'):
            body_lines.append(f"학원등록번호: {ct['학원등록번호']}")
        if ct.get('비고'):
            body_lines.append(f"참고: {ct['비고']}")

    rows.append({
        '제목': c['title'],
        '본문': " ".join(body_lines),
    })

# ==================================================
# 2) 수강료 (66행 · 자연어 완결형)
# ==================================================
for t in tuitions:
    ct = t['content']
    camp = t['campus']
    sub = t['subcategory']

    body_lines = [f"[카테고리] 수강료 · {sub}"]
    body_lines.append(f"{camp} 캠퍼스 {sub} 브랜드의 26년 수강료 정보입니다.")

    if ct.get('브랜드'):
        body_lines.append(f"브랜드: {ct['브랜드']}")
    if ct.get('회당'):
        body_lines.append(f"수업 회수: {ct['회당']}")
    if ct.get('과정'):
        body_lines.append(f"과정: {ct['과정']}")
    if ct.get('26년_수강료'):
        body_lines.append(f"26년 수강료: {ct['26년_수강료']:,}원.")
    if ct.get('25년_수강료') and ct.get('인상액') is not None:
        up = ct['인상액']
        if up > 0:
            body_lines.append(f"25년 수강료는 {ct['25년_수강료']:,}원이었으며 {up:,}원 인상되었습니다.")
        elif up < 0:
            body_lines.append(f"25년 수강료는 {ct['25년_수강료']:,}원이었으며 {abs(up):,}원 인하되었습니다.")
        else:
            body_lines.append(f"25년과 동일한 {ct['25년_수강료']:,}원입니다.")
    if ct.get('비고'):
        body_lines.append(f"참고: {ct['비고']}")

    rows.append({
        '제목': t['title'],
        '본문': " ".join(body_lines),
    })

# ==================================================
# 3) 행정 매뉴얼 (Ⅰ, Ⅱ series만 · 반형태·수익코드 제외)
# ==================================================
for a in admins:
    sub = a['subcategory']
    # 반형태·수익코드 제외
    if sub.startswith('Ⅲ') or sub.startswith('Ⅳ'):
        continue

    c = a['content']
    body = c.get('본문') or c.get('markdown') or " ".join(f"{k}: {v}" for k,v in c.items() if v)

    body_lines = [f"[카테고리] 행정 매뉴얼 · {sub}"]
    body_lines.append(f"제목: {a['title']}")
    body_lines.append(body)

    rows.append({
        '제목': a['title'],
        '본문': "\n\n".join(body_lines),
    })

# ==================================================
# 4) 학부모 응대 매뉴얼
# ==================================================
for p in pr:
    c = p['content']
    body_lines = [f"[카테고리] 학부모 응대 매뉴얼 · {p['subcategory']}"]
    body_lines.append(f"주제: {p['title']}")

    if c.get('markdown'):
        body_lines.append(c['markdown'])
    if c.get('recommended'):
        body_lines.append(f"[권장 응대]\n{c['recommended']}")
    if c.get('avoid'):
        body_lines.append(f"[피해야 할 응대]\n{c['avoid']}")

    rows.append({
        '제목': p['title'],
        '본문': "\n\n".join(body_lines),
    })

# ==================================================
# 5) CS 감탄 매뉴얼
# ==================================================
for x in ca:
    c = x['content']
    body_lines = [f"[카테고리] CS 감탄 매뉴얼 · {x['subcategory']}"]
    body_lines.append(f"주제: {x['title']}")

    if c.get('markdown'):
        body_lines.append(c['markdown'])
    if c.get('recommended'):
        body_lines.append(f"[권장]\n{c['recommended']}")
    if c.get('avoid'):
        body_lines.append(f"[지양]\n{c['avoid']}")

    rows.append({
        '제목': x['title'],
        '본문': "\n\n".join(body_lines),
    })

# ==================================================
# 6) 캠퍼스별 상담자료
# ==================================================
for x in cg:
    c = x['content']
    body_lines = [f"[카테고리] 캠퍼스별 상담자료 · {x['subcategory']}"]
    body_lines.append(f"주제: {x['title']}")

    if c.get('markdown'):
        body_lines.append(c['markdown'])
    if c.get('recommended'):
        body_lines.append(f"[권장]\n{c['recommended']}")
    if c.get('avoid'):
        body_lines.append(f"[지양]\n{c['avoid']}")

    rows.append({
        '제목': x['title'],
        '본문': "\n\n".join(body_lines),
    })

# ==================================================
# CSV 출력
# ==================================================
out_csv = OUT / "flow-cs-hub-kb-v3.csv"
with out_csv.open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['제목', '본문'])
    w.writeheader()
    for r in rows:
        w.writerow(r)

# ==================================================
# 요약
# ==================================================
lengths = [len(r['본문']) for r in rows]
print(f"생성: {out_csv}")
print(f"총 행: {len(rows)}건 (v2 대비 {len(rows) - 356}건)")
print(f"평균 본문 길이: {sum(lengths)//len(lengths)} chars")
print(f"최대 본문 길이: {max(lengths)} chars")
print(f"최소 본문 길이: {min(lengths)} chars")

# 카테고리별
cat_ct = {}
for r in rows:
    cat = r['본문'].split(']')[0][1:].split('·')[0].strip() if '[' in r['본문'] else '기타'
    cat_ct[cat] = cat_ct.get(cat, 0) + 1
print(f"\n카테고리별 행수:")
for k, v in cat_ct.items():
    print(f"  · {k}: {v}건")

size_kb = out_csv.stat().st_size / 1024
print(f"\n파일 크기: {size_kb:.1f} KB")

# Dify 업로드 권장 설정
print("\n" + "=" * 60)
print("Dify 업로드 권장 설정")
print("=" * 60)
print("  - 청크 사양: 사용자 지정")
print("  - 청크 식별자: (없음 or 빈칸)")
print("  - 최대 청크 크기: 4000 토큰")
print("  - 청크 중복: 0")
print("  - 임베딩: jina-embeddings-v3 (기존 유지)")
print(f"\n예상 청크 수: 약 {len(rows)}개 (1행=1청크)")
