/**
 * Flow CS Hub · 자료 업데이트 요청 알림 자동화
 *
 * 역할: "자료 업데이트 요청" 시트에 신규 행 추가 시
 *       팀장님(f004a@flowedu.ai.kr)에게 이메일 자동 발송
 *
 * 설치 방법:
 * 1. Google Sheet 열기 → 상단 「확장 프로그램」 → 「Apps Script」
 * 2. 기본 코드 전체 삭제 → 이 파일 내용 전체 붙여넣기
 * 3. 상단 「프로젝트 저장」 (프로젝트 이름: Flow CS Hub Notifier)
 * 4. 좌측 「트리거」 메뉴 → 「트리거 추가」:
 *    - 실행할 함수: onNewUpdateRequest
 *    - 이벤트 소스: 스프레드시트
 *    - 이벤트 유형: 수정 시(On edit)
 *    - 실패 알림: 즉시 (옵션)
 * 5. 권한 승인 (Google 계정으로 이메일 전송 허용)
 * 6. 테스트: 「자료 업데이트 요청」 시트에 신규 행 추가 → 이메일 수신 확인
 *
 * 사용 쿼터:
 * - Gmail: 무료 계정 100통/일, Workspace 1,500통/일
 * - Apps Script: 트리거 실행 90분/일 (충분)
 */

// ====== 설정 ======
const CONFIG = {
  SHEET_NAME: '자료 업데이트 요청',   // 알림 대상 시트 이름
  NOTIFY_EMAIL: 'f004a@flowedu.ai.kr', // 알림 받을 이메일 (팀장님)
  CC_EMAILS: '',                       // CC (쉼표 구분, 없으면 빈 문자열)
  SUBJECT_PREFIX: '[Flow CS Hub] 자료 업데이트 요청',
};

// ====== 트리거 함수 (수정 시 자동 호출) ======
function onNewUpdateRequest(e) {
  if (!e || !e.range) return;
  const sheet = e.range.getSheet();
  if (sheet.getName() !== CONFIG.SHEET_NAME) return;

  const row = e.range.getRow();
  if (row <= 1) return; // 헤더 행 제외

  // 신규 행 전체 데이터 읽기 (A~J 10컬럼)
  const data = sheet.getRange(row, 1, 1, 10).getValues()[0];
  const [일시, 요청자, 캠퍼스, 카테고리, 요청유형, 상세내용, 긴급도, 상태, 반영일, 메모] = data;

  // 최소 요건: 요청자 또는 상세내용 중 하나는 있어야 발송
  if (!요청자 && !상세내용) return;

  // 중복 발송 방지: K열에 발송 완료 플래그 체크
  const sentFlag = sheet.getRange(row, 11).getValue();
  if (sentFlag === '발송완료') return;

  // 이메일 본문 생성
  const sheetUrl = e.source.getUrl() + '?gid=' + sheet.getSheetId() + '#gid=' + sheet.getSheetId();
  const body = `
새 자료 업데이트 요청이 접수되었습니다.

━━━━━━━━━━━━━━━━━━━━━━━━
📅 요청일시: ${formatDate(일시)}
👤 요청자: ${요청자 || '(미기재)'}
🏫 캠퍼스: ${캠퍼스 || '(미기재)'}
📁 카테고리: ${카테고리 || '(미기재)'}
🔧 요청유형: ${요청유형 || '(미기재)'}
🚨 긴급도: ${긴급도 || '보통'}

📝 상세 내용:
${상세내용 || '(미기재)'}
━━━━━━━━━━━━━━━━━━━━━━━━

👉 시트에서 확인·반영: ${sheetUrl}
👉 Flow CS Hub: https://coayay.github.io/flow-cs-hub/
  `.trim();

  const urgent = String(긴급도).trim() === '높음' ? '🚨 긴급 · ' : '';
  const subject = `${CONFIG.SUBJECT_PREFIX} · ${urgent}${카테고리 || '요청'} (${캠퍼스 || '-'})`;

  try {
    MailApp.sendEmail({
      to: CONFIG.NOTIFY_EMAIL,
      cc: CONFIG.CC_EMAILS,
      subject: subject,
      body: body,
    });
    // 발송 완료 플래그 기록 (중복 방지)
    sheet.getRange(row, 11).setValue('발송완료');
    sheet.getRange(row, 12).setValue(new Date());
  } catch (err) {
    sheet.getRange(row, 11).setValue('발송실패: ' + err.message);
  }
}

// ====== 날짜 포맷 ======
function formatDate(d) {
  if (!d) return '-';
  if (d instanceof Date) {
    return Utilities.formatDate(d, 'Asia/Seoul', 'yyyy-MM-dd HH:mm');
  }
  return String(d);
}

// ====== 수동 테스트 함수 (초기 1회 실행 권장) ======
function testNotification() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) {
    throw new Error('시트 "' + CONFIG.SHEET_NAME + '"를 찾을 수 없습니다');
  }
  // 2번째 행(샘플)을 가지고 이메일 발송 테스트
  onNewUpdateRequest({
    source: SpreadsheetApp.getActiveSpreadsheet(),
    range: sheet.getRange(2, 1),
  });
}

// ====== 주 1회 요약 리포트 (옵션) ======
// 트리거 추가 시 "시간 기반 트리거 · 주 단위 타이머 · 매주 월요일 오전 9시" 설정
function weeklyDigest() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) return;

  const data = sheet.getDataRange().getValues();
  if (data.length <= 1) return;

  const pending = [];
  const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

  for (let i = 1; i < data.length; i++) {
    const [일시, 요청자, 캠퍼스, 카테고리, 요청유형, 상세내용, 긴급도, 상태] = data[i];
    if (!요청자 && !상세내용) continue;
    if (상태 === '반영완료' || 상태 === '반려') continue;
    const d = (일시 instanceof Date) ? 일시 : null;
    if (!d || d < oneWeekAgo) continue;
    pending.push(`• [${카테고리}] ${캠퍼스} · ${요청자}: ${상세내용}`);
  }

  if (pending.length === 0) return;

  const body = `지난 7일간 접수된 미반영 자료 업데이트 요청 ${pending.length}건:\n\n${pending.join('\n')}\n\n👉 ${SpreadsheetApp.getActiveSpreadsheet().getUrl()}`;

  MailApp.sendEmail({
    to: CONFIG.NOTIFY_EMAIL,
    subject: `${CONFIG.SUBJECT_PREFIX} · 주간 요약 (${pending.length}건 대기 중)`,
    body: body,
  });
}
