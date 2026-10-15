# -*- coding: utf-8 -*-
"""
Priority 1 데이터 수정 스크립트 (9건)
"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"C:\Users\flowedu1\신사업전략팀\03_AI_TF\03_CS상담플랫폼\챗봇 만들기\cs-db-v2\webapp-mockup")
DATA = BASE / "data"

contacts = json.loads((DATA / "contacts.json").read_text(encoding='utf-8'))

def find_by_id(cid):
    for c in contacts:
        if c['id'] == cid: return c
    return None

fixes_applied = []

# ============ FIX 1 & 2: 정자 고등관 - 조병룡 부원장 내선 3140 · 백궁프라자 추가 ============
c = find_by_id('contact-정자-고등관')
if c:
    c['content']['위치'] = '백궁프라자 8층 · 시그마타워 6층'
    c['content']['직통번호'] = '031-698-3400 (연결 1, 3)'
    c['content']['담당자'] = '조병룡 부원장 (내선 3140 · 6704)'
    c['content']['내선'] = '3140 · 6704'
    c['content']['비고'] = '수내 고등관 겸 정자 관할 · 백궁프라자 (메이저의대관) + 시그마타워'
    fixes_applied.append('FIX 1·2: 정자 고등관 조병룡 부원장 내선·위치 통합')

# ============ FIX 3: 수내 중등관 고수정 과장 중복 제거 (3002 유지, 3001은 이보림과 중복이라 제거) ============
c = find_by_id('contact-수내-중등관-중등영재관-중등-사이언스카이')
if c:
    # 원본에 고수정과장 3002 · 고수정 과장 3001 두 개 있음. 실제로는 3001은 이보림 대리와 중복.
    # 3002를 정확한 내선으로 판단하고, 3001 항목만 제거
    c['content']['담당자'] = '이보림대리 (내선 3001) · 고수정과장 (내선 3002 · 직통 031-607-3400) · 김미숙주임 (내선 9001) · 중등영재/조인완실장 (내선 5001) · 최진영팀장(대리) (내선 5013)'
    c['content']['내선'] = '3001 · 3002 · 9001 · 5001 · 5013'
    c['content']['비고'] = '중등관·중등영재관·중등사스 통합 상담실'
    fixes_applied.append('FIX 3: 수내 중등관 고수정 과장 중복 제거 · 직통 명시')

# ============ FIX 4·5: 수내 고등관 - 메이저의대관 → 조병룡, 학원등록 정정 ============
c = find_by_id('contact-수내-고등관')
if c:
    # 조병룡부원장 6704 (시그마타워)와 메이저의대관 3140 (백궁프라자)은 실제 조병룡 부원장이 관할
    # 표기를 명확히 하고 학원등록번호 오입력 수정
    c['content']['담당자'] = '조병룡부원장 (내선 6704 · 시그마타워 6층) · 조병룡부원장 (내선 3140 · 백궁프라자 8층 메이저의대관) · 이현숙주임 (내선 1348) · 김영주주임 (내선 3206) · 김세희팀장 (내선 3286 · 다운타운 8층 고3관)'
    c['content']['내선'] = '6704 · 3140 · 1348 · 3206 · 3286'
    c['content']['위치'] = '시그마타워 6층 · 백궁프라자 8층 · 다운타운 8층'
    c['content']['학원등록번호'] = '제5948호(다운타운 8층 고3관)'
    c['content']['비고'] = '3곳 분산 운영 · 일·월 휴관'
    fixes_applied.append('FIX 4·5: 수내 고등관 메이저의대관→조병룡 · 학원등록 정정 · 위치 통합')

# ============ FIX 6: 수내 고등사이언스카이 학원등록 정정 ============
c = find_by_id('contact-수내-고등사이언스카이')
if c:
    c['content']['학원등록번호'] = ''
    c['content']['비고'] = '화·수 휴관'
    fixes_applied.append('FIX 6: 수내 고등사스 학원등록→비고로 이동')

# ============ FIX 7: 이매 위치 채우기 (반형태 시트 기준) ============
c = find_by_id('contact-이매-초등관')
if c:
    c['content']['위치'] = '정민빌딩 3층'
    fixes_applied.append('FIX 7a: 이매 초등관 위치 추가 · 정민빌딩 3층')

c = find_by_id('contact-이매-중등관')
if c:
    c['content']['위치'] = '한화빌딩 2층'
    fixes_applied.append('FIX 7b: 이매 중등관 위치 추가 · 한화빌딩 2층')

c = find_by_id('contact-이매-고등관')
if c:
    c['content']['위치'] = '금강프라자 4층'
    fixes_applied.append('FIX 7c: 이매 고등관 위치 추가 · 금강프라자 4층')

# ============ FIX 8: 최원선 대리 근무 요일 별도 표기 ============
c = find_by_id('contact-광교-초등-사이언스카이')
if c:
    c['content']['담당자'] = '최원선대리 (내선 8958)'
    c['content']['비고'] = '최원선대리 근무일: 수·목·토'
    fixes_applied.append('FIX 8a: 광교 초등 사스 최원선 근무일 분리')

c = find_by_id('contact-영통-중등-사이언스카이')
if c:
    c['content']['담당자'] = '최원선대리 (내선 8400)'
    c['content']['비고'] = '최원선대리 근무일: 화·금'
    fixes_applied.append('FIX 8b: 영통 중등 사스 최원선 근무일 분리')

# ============ FIX 9: 본사 인사기획팀 김정은 과장 소속 분리 ============
c = find_by_id('contact-본사-인사기획팀')
if c:
    c['content']['담당자'] = '조경숙 팀장 (내선 1342 · 직통 031-606-1342) · 김정은 과장 (직통 031-625-6178 · 디키친 잠실 소속) · 류지영 과장 (내선 1340 · 직통 031-606-1340) · 주현주 사원 (내선 1344 · 직통 031-606-1344)'
    fixes_applied.append('FIX 9: 본사 인사기획팀 김정은 과장 소속 분리')

# ============ 저장 ============
(DATA / 'contacts.json').write_text(json.dumps(contacts, ensure_ascii=False, indent=2), encoding='utf-8')

print('=' * 60)
print(f'적용된 수정: {len(fixes_applied)}건')
print('=' * 60)
for f in fixes_applied:
    print(f'  ✅ {f}')
