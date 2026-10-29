/**
 * Flow CS Hub — 사용 로그 수집 (Apps Script Web App)
 *
 * 역할: 웹앱에서 fetch POST 로 보낸 사용 로그를 「기록」 시트에 append.
 * 익명 수집, 개인정보 없음, visitor_id는 브라우저 localStorage UUID.
 *
 * 배포 방법 (팀장 1회):
 *  1. 시트 확장 → Apps Script 열기
 *  2. 이 파일 전체 복사 → 새 파일 "log_usage.gs" 생성 후 붙여넣기
 *  3. 상단 메뉴 「배포」 → 「새 배포」 → 유형 「웹 앱」
 *     - 실행: 나
 *     - 액세스: 모든 사용자 (익명 접근 허용 — 로그 수집용)
 *  4. 발급된 Web App URL 복사 → index.html FLOW_LOG_URL 상수에 붙여넣기
 *  5. 「기록」 시트 1행에 헤더 자동 생성됨 (첫 로그 수신 시)
 */

const SHEET_NAME = '기록';
const HEADERS = ['timestamp', 'event', 'visitor_id', 'session_id', 'query', 'result_quality', 'target_id', 'target_url', 'category', 'ua_summary', 'referrer', 'raw'];
const MAX_QUERY_LEN = 500;
const MAX_URL_LEN = 500;

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    appendLog(data);
    return ContentService
      .createTextOutput(JSON.stringify({ok: true}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ok: false, error: String(err)}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  // Preflight·health check 용 — GET 은 ping 응답만
  return ContentService
    .createTextOutput(JSON.stringify({ok: true, service: 'flow-cs-hub-log'}))
    .setMimeType(ContentService.MimeType.JSON);
}

function appendLog(data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(HEADERS);
    sh.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold').setBackground('#FEF3E6');
    sh.setFrozenRows(1);
  }
  // 헤더가 비었거나 다르면 보강
  const firstCell = sh.getRange(1, 1).getValue();
  if (!firstCell) {
    sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold').setBackground('#FEF3E6');
    sh.setFrozenRows(1);
  }

  // 민감정보 자동 마스킹 (전화·주민번호 패턴)
  const mask = s => {
    if (!s) return '';
    let v = String(s);
    v = v.replace(/\d{6}-\d{7}/g, '[주민번호]');
    v = v.replace(/01[016789]-?\d{3,4}-?\d{4}/g, '[휴대폰]');
    v = v.replace(/0\d{1,2}-?\d{3,4}-?\d{4}/g, '[전화]');
    return v.slice(0, MAX_QUERY_LEN);
  };

  const row = [
    new Date(),
    data.event || '',
    data.visitor_id || '',
    data.session_id || '',
    mask(data.query || ''),
    data.result_quality || '',
    data.target_id || '',
    (data.target_url || '').slice(0, MAX_URL_LEN),
    data.category || '',
    data.ua_summary || '',
    data.referrer || '',
    JSON.stringify(data).slice(0, 1000)
  ];
  sh.appendRow(row);
}

/** 테스트: Apps Script 에디터에서 수동 실행 */
function _test() {
  appendLog({
    event: 'test',
    visitor_id: 'v-test-' + Date.now(),
    session_id: 's-test',
    query: '테스트 쿼리입니다',
    result_quality: 'GOOD',
    ua_summary: 'PC·Chrome',
  });
  Logger.log('OK: 「기록」 시트 확인');
}
