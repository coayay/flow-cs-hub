# Flow CS Hub 챗봇 — 블랙요원 2차 레드팀 리포트

**실행일**: 2026-10-15
**검토자**: Opus 4.7 (블랙요원 / 1차 반증)
**검토 범위**: `index.html` L700~1910 (searchLocal·detectIntent·evaluateAnswerQuality·formatAnswer·csvToFiles·renderDetail·innerHTML 전수)

---

## 1. 1차 발견 반증

| 1차 결함 | 검증 결과 | 코멘트 |
|---|---|---|
| CRIT-1 캠퍼스 무시 | ✅ **더 심각**. L1677-1683의 campus 재정렬은 `allHits`(이미 Fuse·intent 혼합) 전체에만 작동. intent-category 단계(L1642-1652)는 캠퍼스 보너스만 주고 **"캠퍼스 미매칭 항목을 제외하지 않는다"**. 따라서 "정자" 질의가 수내 수강료로 가는 건 가중치 부족이 아니라 **대안 폴백 로직 자체가 없는 설계 결함** | 과소평가 |
| CRIT-2 "원" 1글자 오탐 | ✅ L1721 그대로 `/수강료\|비용\|가격\|얼마\|원/`. 재현 100% | 정확 |
| CRIT-3 파일명 매칭 실패 | ⚠️ 부분 반증. detectIntent files 패턴(L1709)에 **"학원"·"N타워"·"제N학원"·"빌딩" 전혀 없음**. 1차가 지적한 "통상명으로 검색"이 아니라 **키워드가 아예 files 라우터에 등록 안 됨**. "증빙 파일"은 라우팅은 성공(패턴 매칭)하지만 **search_text에 "증빙" 토큰이 없는 파일 데이터와 미스매치** | 원인 설명 보강 필요 |
| CRIT-4 무의미 질의 | ✅ 정확. 추가로 Fuse `minMatchCharLength: 1`(L809) + `threshold: 0.35`(L807)라 "ㄱㄱ"에도 반드시 결과가 나옴 | 정확·악화 |
| CRIT-5 감정 질의 | ✅ 정확. L1723 `/응대\|스크립트\|환불\|클레임\|문의\|대응/`은 "비싸요"·"왜" 토큰 없음 | 정확 |
| CRIT-6 담당자명 오매칭 | ⚠️ 과장. "고수정" 단독 질의는 intent=null → Fuse 폴백. search_text에 담당자 full name이 없으면 Fuse 매칭률 0이 되어 아무 데나 꽂힘. **1차의 "contacts 우선"보다 search_text 데이터 결함이 본질** | 데이터 결함 |

---

## 2. 새로 발견한 결함 TOP 5

### 🔴 NEW-1. XSS 벡터 — Google Sheet CSV 경유 코드 실행 (치명)
- **위치**: `index.html` L1251, L1257, L1324-1333, L1409
  - L1251 `<h2>${item.title}</h2>` (renderDetail)
  - L1257 `onclick="copyItem('${item.id}')"` (단일따옴표 interpolation)
  - L1328 `onclick="goDetail('${item.id}'); hideSearchResults();"` + L1329 `${title}` (highlightText는 escapeHtml 미호출)
  - L1409 `srcEl.innerHTML = ... sources.map(s => \`• ${s}\`).join('<br>')` — 소스명(=hit.title) 직접 삽입
- **재현**: 공유 시트 「행정자료」 탭 파일명 셀에 `<img src=x onerror="alert(document.cookie)">` 입력 → 다음 동기화 후 홈/검색/상세 어디서든 JS 실행. 시트는 **사내 공유 편집 가능 상태**이므로 내부자(또는 계정 탈취) 공격 벡터.
- **영향**: `_debug` 노출(L1904) + XSS 조합으로 전체 데이터 셀 enumeration + sessionStorage 탈취. 사내용이라도 Google 로그인 쿠키가 Drive 폴더 열람 권한을 품으므로 노출 범위 큼.

### 🔴 NEW-2. `csvToFiles` id 생성 — 북마크·상세 URL 영구 깨짐 리스크 (고)
- **위치**: `index.html` L721 `id: fileId ? ('file-' + fileId) : (r.id || ('file-sheet-' + idx))`
- **재현**: 「행정자료」 시트에서 ① 파일ID 열이 빈 행이 있으면 `file-sheet-0`, `file-sheet-1`… 로 인덱스에 묶임 → 행 재정렬·중간 행 삭제 시 **모든 폴백 id가 1칸씩 이동** → 과거 공유된 `#/detail/file-sheet-3` 링크가 다른 파일을 가리킴. ② 반대로 파일ID가 채워져 있어도 Drive에서 파일 교체(새 ID 발급) 시 북마크 끊김.
- **영향**: CS 실장이 Slack·메모장에 저장한 챗봇 상세 링크가 조용히 틀린 파일로 안내. 틀렸는지 확인 수단 없음.

### 🟠 NEW-3. `csvToFiles` 컬럼 변경 시 조용한 전면 실패 (고)
- **위치**: L716-717 `rows.filter(r => (r['파일명'] || r.title))`
- **재현**: 시트 편집자가 「파일명」을 「파일 이름」으로 바꾸면 모든 행이 filter에서 제거 → files 배열 빈 상태로 로드. L746 `parsed.errors.length && !parsed.data.length`도 통과(data는 있음, 다만 모든 키가 다름). 챗봇은 "자료 없음"만 반복, 원인 불명.
- **영향**: 콘솔 로그 없음, 사용자 눈에 안 보이는 데이터 유실. 복구는 시트 되돌리기만 가능.

### 🟠 NEW-4. Fuse 설정 — `minMatchCharLength: 1` + 캠퍼스 하드코딩 (중)
- **위치**: L800-811, L1696-1702 `extractCoreKeywords`
- **재현**: ① `minMatchCharLength: 1`이라 Fuse가 1글자 토큰("원"·"관")도 유효 매칭 → threshold 0.35 하에서 거의 모든 질의가 비어 돌아오지 않음(CRIT-4 뿌리). ② `extractCoreKeywords`에 `['이매','수내','수지','광교','영통','정자','본사']`만. "**잠실**"은 L1728 detectIntent에는 있지만 extractCoreKeywords엔 **빠짐** → 캠퍼스 폴백 재검색 시 잠실 질의는 캠퍼스 키워드 소실.
- **영향**: 잠실 캠퍼스 추가분 묻는 CS 질의가 랜덤 매칭.

### 🟠 NEW-5. `_debug` production 노출 + 내부 전수 데이터 추출 (중)
- **위치**: L1904 `return { toggle, clear, send, ask, init, _debug: { searchLocal, detectIntent, formatAnswer, evaluateAnswerQuality, cleanQuery, extractCoreKeywords } };`
- **재현**: 브라우저 콘솔에서 `FlowBot._debug.searchLocal('')` + Fuse index 접근 → 담당자 **직통번호·내선·학원등록번호** 전수 추출 가능. 사이트는 공개 GitHub Pages(라이브). 접근 제어는 **URL 비공개 가정**뿐.
- **영향**: 링크 유출 시 외부에서 사내 연락처 DB 전수 조회. §9-1 「공용 문서에 개인정보 미기재」 규칙과 어긋남.

(추가 관찰 — 지면 관계상 요약) ⓐ 모바일 챗봇 창 L555 `.open { display:flex }` width 540px 하드코딩 → 375px 뷰포트 가로 스크롤. ⓑ `_ts=Math.floor(Date.now()/60000)`(L741)은 **1분** 캐시 — 시트 수정 후 다음 분까지 반영 안 되는데 UX상 "시트 저장했는데 왜 안 바뀌지" 혼선 상시. ⓒ L927 Drive 폴더 ID 하드코딩 2곳(L927·L1031) — 폴더 교체 시 두 군데 수정 필요.

---

## 3. 최우선 조치 2건

### 패치 ①. XSS 차단 — escapeHtml 전수 적용
- **파일**: `index.html`
- **라인**: L1251, L1257, L1328-1329, L1409-1410
- **수정**:
  - L1251 `<h2>${escapeHtml(item.title)}</h2>`
  - L1257 `onclick="copyItem('${encodeURIComponent(item.id)}')"` (+ copyItem 쪽 decodeURIComponent)
  - L1328 `onclick="goDetail('${encodeURIComponent(item.id)}'); ...">${chosungMode ? escapeHtml(item.title) : highlightText(escapeHtml(item.title), raw)}`
  - L1410 `sources.map(s => '• ' + escapeHtml(s)).join('<br>')`
- **효과**: 시트 공격·사고성 입력(`&`, `<`, `'`) 모두 차단. 공수 10분.

### 패치 ②. detectIntent 수강료 regex 교체 + 캠퍼스 폴백 분기
- **파일**: `index.html`
- **라인**: L1721, L1626-1652
- **수정**:
  - L1721 `/수강료|비용|얼마|\d+\s*원|만\s*원|천\s*원/`
  - L1652 뒤에 **"intent.campus 지정됐는데 pool에 campus 일치 항목이 0건이면 scored = []로 두고 showNotFoundMessage 흐름으로"** 분기 (searchLocal 반환값에 플래그 추가 또는 send()에서 체크)
- **효과**: CRIT-2 완전 해소 + CRIT-1 "정답인 척 틀린 답" 치명 유형 제거. 공수 20분.

---

**결론**: 1차의 품질 결함 6건은 모두 유효하되 CRIT-1·CRIT-6은 원인 해석이 과장/과소. 추가로 **XSS·id 안정성·조용한 데이터 유실**이라는 **운영·보안 축의 결함 3건**을 지적한다. 체감 품질(패치 ②)과 운영 안전(패치 ①)을 각각 1건씩 선조치 권장.
