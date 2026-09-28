// 숫자인식CNN(desktop_version/model.py)과 같은 계산을 순수 자바스크립트로 구현한 추론 엔진.
// 화면(DOM)을 전혀 쓰지 않으므로 테스트 페이지에서도 그대로 불러 씀.
// 특징 맵은 [채널][세로][가로] 순서를 1차원 배열로 펼쳐서 다룸 (PyTorch 텐서와 같은 순서).
// 중간 계산은 오차가 쌓이지 않도록 Float64Array(배정밀도)로 함.

const 배치정규화_엡실론 = 1e-5;  // PyTorch BatchNorm2d 기본값

/** base64 문자열을 바이트 배열로 변환 */
function base64를_바이트로(문자열) {
  const 이진 = atob(문자열);
  const 바이트 = new Uint8Array(이진.length);
  for (let i = 0; i < 이진.length; i++) 바이트[i] = 이진.charCodeAt(i);
  return 바이트;
}

/** base64 문자열을 float32 배열로 변환 (리틀엔디언으로 저장되어 있음) */
function base64를_실수배열로(문자열) {
  return new Float32Array(base64를_바이트로(문자열).buffer);
}

/** weights.js 의 가중치데이터를 { 층이름: { 형태, 값 } } 객체로 풀어 줌 */
function 가중치_해독(데이터) {
  const 전체 = base64를_실수배열로(데이터.base64);
  const 가중치 = {};
  for (const 항목 of 데이터.목록) {
    if (항목.시작 + 항목.개수 > 전체.length) {
      throw new Error(`가중치 파일이 손상되었습니다 (${항목.이름})`);
    }
    가중치[항목.이름] = { 형태: 항목.형태, 값: 전체.subarray(항목.시작, 항목.시작 + 항목.개수) };
  }
  return 가중치;
}

/** 3x3 합성곱 (padding 1, stride 1): [입력채널][크기][크기] → [출력채널][크기][크기] */
function 합성곱(입력, 입력채널, 크기, 가중치, 편향) {
  const 출력채널 = 편향.length;
  const 면적 = 크기 * 크기;
  const 출력 = new Float64Array(출력채널 * 면적);
  for (let oc = 0; oc < 출력채널; oc++) {
    const 출력시작 = oc * 면적;
    출력.fill(편향[oc], 출력시작, 출력시작 + 면적);
    for (let ic = 0; ic < 입력채널; ic++) {
      const 입력시작 = ic * 면적;
      const 커널시작 = (oc * 입력채널 + ic) * 9;
      for (let ky = 0; ky < 3; ky++) {
        for (let kx = 0; kx < 3; kx++) {
          const w = 가중치[커널시작 + ky * 3 + kx];
          // 가장자리 밖(패딩 부분)은 0 이므로 건너뜀
          for (let y = Math.max(0, 1 - ky); y < Math.min(크기, 크기 + 1 - ky); y++) {
            const 입력줄 = 입력시작 + (y + ky - 1) * 크기 + (kx - 1);
            const 출력줄 = 출력시작 + y * 크기;
            for (let x = Math.max(0, 1 - kx); x < Math.min(크기, 크기 + 1 - kx); x++) {
              출력[출력줄 + x] += w * 입력[입력줄 + x];
            }
          }
        }
      }
    }
  }
  return 출력;
}

/** 배치정규화 (추론 모드: 학습 때 저장된 평균·분산 사용) */
function 배치정규화(입력, 채널, 감마, 베타, 이동평균, 이동분산) {
  const 면적 = 입력.length / 채널;
  const 출력 = new Float64Array(입력.length);
  for (let c = 0; c < 채널; c++) {
    const 배율 = 감마[c] / Math.sqrt(이동분산[c] + 배치정규화_엡실론);
    const 더할값 = 베타[c] - 이동평균[c] * 배율;
    for (let i = c * 면적; i < (c + 1) * 면적; i++) 출력[i] = 입력[i] * 배율 + 더할값;
  }
  return 출력;
}

/** ReLU: 음수를 0으로 (배열을 직접 바꾸고 그대로 반환) */
function 렐루(입력) {
  for (let i = 0; i < 입력.length; i++) if (입력[i] < 0) 입력[i] = 0;
  return 입력;
}

/** 2x2 최대 풀링 (stride 2): [채널][크기][크기] → [채널][크기/2][크기/2] */
function 최대풀링(입력, 채널, 크기) {
  const 반 = 크기 / 2;
  const 출력 = new Float64Array(채널 * 반 * 반);
  for (let c = 0; c < 채널; c++) {
    for (let y = 0; y < 반; y++) {
      for (let x = 0; x < 반; x++) {
        const 왼위 = c * 크기 * 크기 + 2 * y * 크기 + 2 * x;
        출력[c * 반 * 반 + y * 반 + x] = Math.max(
          입력[왼위], 입력[왼위 + 1], 입력[왼위 + 크기], 입력[왼위 + 크기 + 1]);
      }
    }
  }
  return 출력;
}

/** 완전 연결 층: 가중치 형태는 [출력수][입력수] (PyTorch Linear 와 같음) */
function 완전연결(입력, 가중치, 편향) {
  const 출력수 = 편향.length;
  const 입력수 = 입력.length;
  const 출력 = new Float64Array(출력수);
  for (let o = 0; o < 출력수; o++) {
    let 합 = 편향[o];
    const 시작 = o * 입력수;
    for (let i = 0; i < 입력수; i++) 합 += 가중치[시작 + i] * 입력[i];
    출력[o] = 합;
  }
  return 출력;
}

/** 소프트맥스: 점수를 합이 1인 확률로 변환 (최댓값을 빼서 넘침 방지) */
function 소프트맥스(로짓) {
  const 최대 = Math.max(...로짓);
  const 지수 = Array.from(로짓, (값) => Math.exp(값 - 최대));
  const 합 = 지수.reduce((a, b) => a + b, 0);
  return 지수.map((값) => 값 / 합);
}

/** 배열에서 가장 큰 값의 위치 (예측한 숫자) */
function 가장_큰_위치(배열) {
  let 위치 = 0;
  for (let i = 1; i < 배열.length; i++) if (배열[i] > 배열[위치]) 위치 = i;
  return 위치;
}

/** 정규화된 28x28 입력(길이 784)을 받아 0~9 각 숫자의 점수(로짓)를 계산 — model.py 의 forward 와 같은 순서 */
function 숫자인식CNN_로짓(입력, 가중치) {
  const 값 = (이름) => 가중치[이름].값;
  // 첫 번째 합성곱 블록: 1x28x28 → 32x28x28 → 32x14x14
  let x = 합성곱(입력, 1, 28, 값("합성곱1.weight"), 값("합성곱1.bias"));
  x = 배치정규화(x, 32, 값("정규화1.weight"), 값("정규화1.bias"),
    값("정규화1.running_mean"), 값("정규화1.running_var"));
  x = 최대풀링(렐루(x), 32, 28);
  // 두 번째 합성곱 블록: 32x14x14 → 64x14x14 → 64x7x7
  x = 합성곱(x, 32, 14, 값("합성곱2.weight"), 값("합성곱2.bias"));
  x = 배치정규화(x, 64, 값("정규화2.weight"), 값("정규화2.bias"),
    값("정규화2.running_mean"), 값("정규화2.running_var"));
  x = 최대풀링(렐루(x), 64, 14);
  // 드롭아웃1: 추론할 때는 아무 일도 하지 않으므로 생략
  // 펼치기: 이미 [채널][세로][가로] 순서의 1차원 배열(3136개)이므로 그대로 사용
  x = 렐루(완전연결(x, 값("완전연결1.weight"), 값("완전연결1.bias")));
  // 드롭아웃2: 추론할 때는 생략
  return 완전연결(x, 값("완전연결2.weight"), 값("완전연결2.bias"));
}

/** 정규화된 28x28 입력으로 0~9 각 숫자의 확률을 계산 */
function 숫자인식CNN_추론(입력, 가중치) {
  return 소프트맥스(숫자인식CNN_로짓(입력, 가중치));
}
