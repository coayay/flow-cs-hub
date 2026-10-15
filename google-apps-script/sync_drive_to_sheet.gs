/**
 * Flow CS Hub · 공유 드라이브 「CS 행정 자료」 → 구글 시트 「행정자료」 탭 자동 동기화
 *
 * 역할:
 * - 지정된 공유 드라이브(또는 폴더)의 파일 전체를 스캔
 * - 파일명·분류(폴더명)·드라이브 링크·다운로드 링크·수정일·MIME 자동 추출
 * - 「행정자료」 시트에 자동 기록
 * - 기존 행의 '설명'과 '키워드'는 보존 (수동 입력 유지)
 *
 * 설치 방법:
 * 1. Flow CS Hub 데이터 시트 열기 → 하단 "+" 눌러 「행정자료」 탭 신규 생성
 * 2. 상단 「확장 프로그램」 → 「Apps Script」
 * 3. 기본 코드 전체 삭제 → 이 파일 내용 전체 붙여넣기
 * 4. 좌측 「서비스」(+) → "Drive API" 추가 (공유 드라이브 스캔에 필요)
 * 5. 상단 「프로젝트 저장」
 * 6. 함수 선택 → syncDriveToSheet → 실행 (최초 1회 권한 승인)
 * 7. 좌측 「트리거」 → "트리거 추가":
 *    - 실행할 함수: syncDriveToSheet
 *    - 이벤트 소스: 시간 기반
 *    - 트리거 유형: 일 단위 타이머 → 오전 8~9시
 * 8. 테스트: 시트 열고 「행정자료」 탭 확인 → 파일 목록 자동 채워짐
 */

// ====== 설정 ======
const DRIVE_CONFIG = {
  // 공유 드라이브 ID (0A로 시작) 또는 일반 폴더 ID (1로 시작)
  // 「컴퓨터 > 03_CS상담플랫폼 > 자료 > CS 행정 자료」 폴더 (2026-10-15 이동, 플로우교육 그룹 뷰어 공유)
  DRIVE_ID: '18EmHVzVXSDsZWph5wWFxAqS3WJ5OUq4b',

  // 공유 드라이브 전체 스캔 시 true, 일반 폴더 스캔 시 false
  IS_SHARED_DRIVE: false,

  // 결과 기록 시트 이름
  SHEET_NAME: '행정자료',

  // 포함할 MIME 타입 (빈 배열 = 전체)
  // 폴더(application/vnd.google-apps.folder)는 자동 제외
  ALLOWED_MIMES: [],  // 예: ['application/pdf', 'image/png']

  // 제외할 파일명 패턴 (정규식)
  EXCLUDE_PATTERN: /^(\.|~\$|_temp)/,  // 숨김/임시 파일 제외

  // 최대 스캔 깊이 (하위 폴더 재귀)
  MAX_DEPTH: 5,
};

// ====== 메인 동기화 함수 ======
function syncDriveToSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(DRIVE_CONFIG.SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(DRIVE_CONFIG.SHEET_NAME);

  // 기존 데이터 읽기 (설명·키워드 보존용)
  const existingData = readExistingData(sheet);

  // 드라이브 스캔
  const files = scanDrive();
  Logger.log(`스캔 완료: ${files.length}건`);

  // 시트에 기록
  writeToSheet(sheet, files, existingData);

  // 완료 알림 (옵션)
  Logger.log('동기화 완료: ' + new Date().toLocaleString('ko-KR'));
}

// ====== 공유 드라이브 or 폴더 스캔 ======
function scanDrive() {
  const results = [];
  if (DRIVE_CONFIG.IS_SHARED_DRIVE) {
    // 공유 드라이브: Drive API v3 사용 (DriveApp은 공유 드라이브 재귀 불안정)
    scanSharedDriveFolder(DRIVE_CONFIG.DRIVE_ID, '', results, 0);
  } else {
    scanFolder(DriveApp.getFolderById(DRIVE_CONFIG.DRIVE_ID), '', results, 0);
  }
  return results;
}

// 공유 드라이브 폴더 재귀 스캔
function scanSharedDriveFolder(folderId, pathPrefix, results, depth) {
  if (depth > DRIVE_CONFIG.MAX_DEPTH) return;

  let pageToken = null;
  do {
    const response = Drive.Files.list({
      q: `'${folderId}' in parents and trashed = false`,
      fields: 'nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime, size)',
      supportsAllDrives: true,
      includeItemsFromAllDrives: true,
      driveId: DRIVE_CONFIG.DRIVE_ID,
      corpora: 'drive',
      pageSize: 100,
      pageToken: pageToken,
    });

    (response.files || []).forEach(file => {
      if (DRIVE_CONFIG.EXCLUDE_PATTERN.test(file.name)) return;

      if (file.mimeType === 'application/vnd.google-apps.folder') {
        const subPath = pathPrefix ? pathPrefix + ' / ' + file.name : file.name;
        scanSharedDriveFolder(file.id, subPath, results, depth + 1);
      } else {
        if (DRIVE_CONFIG.ALLOWED_MIMES.length && DRIVE_CONFIG.ALLOWED_MIMES.indexOf(file.mimeType) === -1) return;
        results.push(buildFileRecord(file, pathPrefix));
      }
    });

    pageToken = response.nextPageToken;
  } while (pageToken);
}

// 일반 폴더 스캔 (DriveApp)
function scanFolder(folder, pathPrefix, results, depth) {
  if (depth > DRIVE_CONFIG.MAX_DEPTH) return;

  const subFolders = folder.getFolders();
  while (subFolders.hasNext()) {
    const sub = subFolders.next();
    const subPath = pathPrefix ? pathPrefix + ' / ' + sub.getName() : sub.getName();
    scanFolder(sub, subPath, results, depth + 1);
  }

  const files = folder.getFiles();
  while (files.hasNext()) {
    const f = files.next();
    if (DRIVE_CONFIG.EXCLUDE_PATTERN.test(f.getName())) continue;
    const mime = f.getMimeType();
    if (DRIVE_CONFIG.ALLOWED_MIMES.length && DRIVE_CONFIG.ALLOWED_MIMES.indexOf(mime) === -1) continue;
    results.push(buildFileRecord({
      id: f.getId(),
      name: f.getName(),
      mimeType: mime,
      webViewLink: f.getUrl(),
      modifiedTime: f.getLastUpdated().toISOString(),
    }, pathPrefix));
  }
}

// 파일 → 시트 행 매핑
function buildFileRecord(file, pathPrefix) {
  const fileType = mimeToType(file.mimeType);
  const category = pathPrefix || '미분류';
  // Google Docs/Sheets/Slides는 다운로드 URL 생성 불가 → 열람 링크만
  const isGoogleDoc = /google-apps\.(document|spreadsheet|presentation|form)/.test(file.mimeType);
  const downloadUrl = isGoogleDoc ? '' : `https://drive.google.com/uc?id=${file.id}&export=download`;
  return {
    id: file.id,
    name: file.name,
    category: category,
    driveUrl: file.webViewLink || `https://drive.google.com/file/d/${file.id}/view`,
    downloadUrl: downloadUrl,
    modified: formatDate(file.modifiedTime),
    fileType: fileType,
  };
}

function mimeToType(mime) {
  if (!mime) return '';
  if (mime.includes('pdf')) return 'PDF';
  if (mime.includes('spreadsheet') || mime.includes('excel')) return '엑셀';
  if (mime.includes('document') || mime.includes('word')) return '워드';
  if (mime.includes('presentation') || mime.includes('powerpoint')) return 'PPT';
  if (mime.includes('image')) return '이미지';
  if (mime.includes('hwp')) return '한글';
  if (mime.includes('zip') || mime.includes('compressed')) return '압축';
  if (mime.includes('video')) return '동영상';
  return '기타';
}

function formatDate(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return Utilities.formatDate(d, 'Asia/Seoul', 'yyyy-MM-dd');
  } catch (e) {
    return String(iso);
  }
}

// 기존 데이터 읽기 (id → {설명, 키워드})
function readExistingData(sheet) {
  const map = {};
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return map;
  const data = sheet.getRange(2, 1, lastRow - 1, 9).getValues();
  data.forEach(row => {
    const id = row[8]; // I열 = 파일ID
    if (id) {
      map[id] = { 설명: row[2] || '', 키워드: row[6] || '' };
    }
  });
  return map;
}

// 시트에 기록 (전체 재작성, 기존 설명·키워드 머지)
function writeToSheet(sheet, files, existingData) {
  sheet.clear();
  const headers = ['파일명', '분류', '설명', '드라이브 링크', '다운로드 링크', '수정일', '키워드', '파일 종류', '파일ID'];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold').setBackground('#0f766e').setFontColor('#ffffff');

  if (!files.length) return;

  // 분류 → 이름 순 정렬
  files.sort((a, b) => {
    if (a.category !== b.category) return a.category < b.category ? -1 : 1;
    return a.name < b.name ? -1 : 1;
  });

  const rows = files.map(f => {
    const existing = existingData[f.id] || {};
    return [
      f.name,
      f.category,
      existing.설명 || '',
      f.driveUrl,
      f.downloadUrl,
      f.modified,
      existing.키워드 || '',
      f.fileType,
      f.id,
    ];
  });

  sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);

  // 열 너비 자동 조정
  sheet.setColumnWidth(1, 300); // 파일명
  sheet.setColumnWidth(2, 180); // 분류
  sheet.setColumnWidth(3, 280); // 설명
  sheet.setColumnWidth(4, 100); // 드라이브
  sheet.setColumnWidth(5, 100); // 다운로드
  sheet.setColumnWidth(6, 100); // 수정일
  sheet.setColumnWidth(7, 220); // 키워드
  sheet.setColumnWidth(8, 80);  // 파일 종류
  sheet.setColumnWidth(9, 300); // 파일ID

  // 마지막 동기화 시각을 J1에 기록
  sheet.getRange(1, 10).setValue('마지막 동기화: ' + new Date().toLocaleString('ko-KR')).setFontColor('#666666');
}

// ====== 수동 테스트 함수 ======
function testScan() {
  const files = scanDrive();
  Logger.log('총 ' + files.length + '건');
  files.slice(0, 5).forEach(f => Logger.log(JSON.stringify(f)));
}
