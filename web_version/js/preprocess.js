// 그림판 이미지를 MNIST 데이터와 같은 형식(28x28, 가운데 정렬, 정규화)으로 바꾸는 전처리.
// desktop_version/app.py 의 MNIST형식으로_변환() 과 같은 과정을 순수 자바스크립트로 구현함.
// 화면(DOM)을 쓰지 않으므로 테스트 페이지에서도 그대로 불러 씀.
// 전처리나 정규화 값을 바꾸면 app.py 도 함께 고치고 export_web_weights.py 를 다시 실행해야 함.

const MNIST평균 = 0.1307;      // 학습 때와 같은 정규화 값 (train.py, app.py 와 같아야 함)
const MNIST표준편차 = 0.3081;

/** 파이썬 round() 와 같은 은행가 반올림: 정확히 .5 이면 짝수 쪽으로 (2.5 → 2, 3.5 → 4) */
function 파이썬식_반올림(x) {
  const 내림 = Math.floor(x);
  const 차이 = x - 내림;
  if (차이 < 0.5) return 내림;
  if (차이 > 0.5) return 내림 + 1;
  return 내림 % 2 === 0 ? 내림 : 내림 + 1;
}

/** sinc 함수: sin(πx) / (πx) */
function 싱크(x) {
  if (x === 0) return 1;
  x *= Math.PI;
  return Math.sin(x) / x;
}

/** Lanczos3 필터 (Pillow 의 lanczos_filter 와 같음) */
function 란초시3(x) {
  return x >= -3 && x < 3 ? 싱크(x) * 싱크(x / 3) : 0;
}

/**
 * 한 축 방향 재표본화 계수 계산 (Pillow 의 precompute_coeffs 와 같은 방식).
 * 출력 픽셀마다 { 시작: 첫 입력 위치, 가중: 입력 픽셀별 가중치 배열 } 을 돌려줌.
 * 축소할 때는 필터 폭을 배율만큼 넓혀서 여러 픽셀을 고르게 섞음.
 */
function 재표본화_계수(입력길이, 출력길이) {
  const 배율 = 입력길이 / 출력길이;
  const 필터배율 = Math.max(배율, 1);
  const 반경 = 3 * 필터배율;
  const 계수목록 = [];
  for (let i = 0; i < 출력길이; i++) {
    const 중심 = (i + 0.5) * 배율;
    const 시작 = Math.max(0, Math.trunc(중심 - 반경 + 0.5));
    const 끝 = Math.min(입력길이, Math.trunc(중심 + 반경 + 0.5));
    const 가중 = [];
    let 합 = 0;
    for (let j = 시작; j < 끝; j++) {
      const w = 란초시3((j - 중심 + 0.5) / 필터배율);
      가중.push(w);
      합 += w;
    }
    if (합 !== 0) for (let k = 0; k < 가중.length; k++) 가중[k] /= 합;
    계수목록.push({ 시작, 가중 });
  }
  return 계수목록;
}

/** 0~255 로 자르고 반올림 (Pillow 가 8비트 결과를 만들 때처럼) */
function 바이트로_자르기(값) {
  return Math.min(255, Math.max(0, Math.floor(값 + 0.5)));
}

/** Lanczos 로 흑백 이미지 크기 바꾸기 — Pillow 처럼 가로 방향 → 세로 방향 순서, 크기가 같은 방향은 건너뜀 */
function 크기_바꾸기(픽셀, 가로, 세로, 새가로, 새세로) {
  let 현재 = 픽셀;
  if (새가로 !== 가로) {
    const 계수 = 재표본화_계수(가로, 새가로);
    const 결과 = new Uint8Array(새가로 * 세로);
    for (let y = 0; y < 세로; y++) {
      for (let x = 0; x < 새가로; x++) {
        const { 시작, 가중 } = 계수[x];
        let 합 = 0;
        for (let k = 0; k < 가중.length; k++) 합 += 현재[y * 가로 + 시작 + k] * 가중[k];
        결과[y * 새가로 + x] = 바이트로_자르기(합);
      }
    }
    현재 = 결과;
  }
  if (새세로 !== 세로) {
    const 계수 = 재표본화_계수(세로, 새세로);
    const 결과 = new Uint8Array(새가로 * 새세로);
    for (let y = 0; y < 새세로; y++) {
      const { 시작, 가중 } = 계수[y];
      for (let x = 0; x < 새가로; x++) {
        let 합 = 0;
        for (let k = 0; k < 가중.length; k++) 합 += 현재[(시작 + k) * 새가로 + x] * 가중[k];
        결과[y * 새가로 + x] = 바이트로_자르기(합);
      }
    }
    현재 = 결과;
  }
  return 현재;
}

/**
 * 그림판 흑백 픽셀(검은 배경 0, 흰 글씨 255)을 MNIST 형식의 정규화된 28x28 입력(길이 784)으로 변환.
 * 아무것도 그리지 않았으면 null.
 */
function MNIST형식으로_변환(흑백픽셀, 가로, 세로) {
  // 1) 글씨가 있는 영역(0이 아닌 픽셀)만 잘라내기
  let 왼 = 가로, 위 = 세로, 오른 = -1, 아래 = -1;
  for (let y = 0; y < 세로; y++) {
    for (let x = 0; x < 가로; x++) {
      if (흑백픽셀[y * 가로 + x] !== 0) {
        if (x < 왼) 왼 = x;
        if (x > 오른) 오른 = x;
        if (y < 위) 위 = y;
        if (y > 아래) 아래 = y;
      }
    }
  }
  if (오른 < 0) return null;  // 아무것도 그리지 않은 경우
  const 자른가로 = 오른 - 왼 + 1;
  const 자른세로 = 아래 - 위 + 1;
  const 자른 = new Uint8Array(자른가로 * 자른세로);
  for (let y = 0; y < 자른세로; y++) {
    for (let x = 0; x < 자른가로; x++) 자른[y * 자른가로 + x] = 흑백픽셀[(위 + y) * 가로 + 왼 + x];
  }

  // 2) 가로세로 비율을 유지하며 긴 쪽을 20픽셀로 맞추기
  const 배율 = 20 / Math.max(자른가로, 자른세로);
  const 새가로 = Math.max(1, 파이썬식_반올림(자른가로 * 배율));
  const 새세로 = Math.max(1, 파이썬식_반올림(자른세로 * 배율));
  const 숫자 = 크기_바꾸기(자른, 자른가로, 자른세로, 새가로, 새세로);

  // 3) 28x28 검은 배경의 가운데에 붙이기
  const 배경 = new Uint8Array(28 * 28);
  const 왼여백 = Math.floor((28 - 새가로) / 2);
  const 위여백 = Math.floor((28 - 새세로) / 2);
  for (let y = 0; y < 새세로; y++) {
    for (let x = 0; x < 새가로; x++) 배경[(위여백 + y) * 28 + 왼여백 + x] = 숫자[y * 새가로 + x];
  }

  // 4) 무게중심이 정중앙(14, 14)에 오도록 정수 칸만큼 옮기기
  let 전체 = 0, 합x = 0, 합y = 0;
  for (let y = 0; y < 28; y++) {
    for (let x = 0; x < 28; x++) {
      const 값 = 배경[y * 28 + x];
      전체 += 값;
      합x += x * 값;
      합y += y * 값;
    }
  }
  if (전체 === 0) return null;  // 축소하면서 흐린 점이 모두 사라진 경우
  const 이동x = 파이썬식_반올림(14 - 합x / 전체);
  const 이동y = 파이썬식_반올림(14 - 합y / 전체);

  // 5) 옮긴 이미지를 0~1 로 바꾸고 학습 때와 같은 방식으로 정규화
  const 결과 = new Float32Array(28 * 28);
  for (let y = 0; y < 28; y++) {
    for (let x = 0; x < 28; x++) {
      const 원래x = x - 이동x;
      const 원래y = y - 이동y;
      const 값 = 원래x >= 0 && 원래x < 28 && 원래y >= 0 && 원래y < 28 ? 배경[원래y * 28 + 원래x] : 0;
      결과[y * 28 + x] = (값 / 255 - MNIST평균) / MNIST표준편차;
    }
  }
  return 결과;
}
