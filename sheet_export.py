"""
Flow CS Hub · JSON → Google Sheet용 CSV 변환
연락처 (33건) + 수강료 (66건)
"""
import json, csv
from pathlib import Path

BASE = Path(r"C:\Users\flowedu1\신사업전략팀\03_AI_TF\03_CS상담플랫폼\챗봇 만들기\cs-db-v2\webapp-mockup")
DATA = BASE / "data"
OUT = BASE / "sheet-export"
OUT.mkdir(exist_ok=True)

# ============ 연락처 ============
contacts = json.loads((DATA / "contacts.json").read_text(encoding='utf-8'))
with (OUT / "contacts.csv").open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    # 헤더: 구글 시트에서 편집할 컬럼
    w.writerow(['id', '분류', '캠퍼스', '관/시설', '직통번호', '대표번호', '위치', '비고'])
    for c in contacts:
        w.writerow([
            c['id'],
            c['subcategory'],
            c['campus'] or '',
            c['gwan'] or '',
            c['content'].get('직통번호', ''),
            c['content'].get('대표번호', ''),
            c['content'].get('위치', ''),
            c['content'].get('비고', ''),
        ])
print(f"연락처 CSV: {OUT / 'contacts.csv'}")

# ============ 수강료 ============
tuitions = json.loads((DATA / "tuition.json").read_text(encoding='utf-8'))
with (OUT / "tuition.csv").open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['id', '구분', '캠퍼스', '사업부', '브랜드', '회당', '과정', '25년_수강료', '26년_수강료', '비고'])
    for t in tuitions:
        c = t['content']
        w.writerow([
            t['id'],
            t['subcategory'],
            t['campus'] or '',
            c.get('사업부', ''),
            c.get('브랜드', ''),
            c.get('회당', ''),
            c.get('과정', ''),
            c.get('25년_수강료', ''),
            c.get('26년_수강료', ''),
            c.get('비고', ''),
        ])
print(f"수강료 CSV: {OUT / 'tuition.csv'}")
print(f"\n✅ 총 2개 CSV 생성 완료")
print(f"위치: {OUT}")
