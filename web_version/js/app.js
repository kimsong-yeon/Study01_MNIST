// 그림판 화면: 그린 숫자를 전처리(preprocess.js)한 뒤 CNN(model.js)으로 인식해 결과를 보여 줌.
// 데스크톱 버전과 달리 화면의 캔버스 픽셀을 그대로 읽어 인식하므로 이미지를 두 벌 관리하지 않음.

const 캔버스크기 = 280;  // 그림판 내부 해상도 (데스크톱 앱과 같음, 화면에 보이는 크기는 CSS 가 정함)
const 붓두께 = 18;

const 그림판 = document.getElementById("그림판");
const 붓 = 그림판.getContext("2d", { willReadFrequently: true });
const 인식버튼 = document.getElementById("인식버튼");
const 지우기버튼 = document.getElementById("지우기버튼");
const 결과숫자 = document.getElementById("결과숫자");
const 확신도 = document.getElementById("확신도");
const 오류안내 = document.getElementById("오류안내");

let 앱가중치 = null;    // 해독한 모델 가중치 (불러오기에 실패하면 null)
let 이전좌표 = null;    // 선을 이을 직전 위치
let 활성포인터 = null;  // 지금 그리고 있는 포인터(손가락·마우스) ID — 두 번째 손가락은 무시
const 막대들 = [];      // [{ 막대, 값 }] 숫자 0~9

/** 숫자 0~9 확률 막대 그래프 줄을 만듦 */
function 막대_만들기() {
  const 목록 = document.getElementById("막대목록");
  for (let 숫자 = 0; 숫자 < 10; 숫자++) {
    const 줄 = document.createElement("li");
    줄.className = "막대줄";
    줄.innerHTML = `<span>${숫자}</span><div class="막대배경"><div class="막대"></div></div><span class="막대값">0.0%</span>`;
    목록.appendChild(줄);
    막대들.push({ 막대: 줄.querySelector(".막대"), 값: 줄.querySelector(".막대값") });
  }
}

/** 확률 막대 그래프를 다시 그림 (가장 큰 값은 파란색) */
function 막대_갱신(확률) {
  const 최대 = Math.max(...확률);
  확률.forEach((p, i) => {
    막대들[i].막대.style.width = `${p * 100}%`;
    막대들[i].막대.classList.toggle("최대", p === 최대 && p > 0);
    막대들[i].값.textContent = `${(p * 100).toFixed(1)}%`;
  });
}

/** 그림판을 검은색으로 채우고 붓을 흰색으로 준비 */
function 그림판_초기화() {
  붓.fillStyle = "#000";
  붓.fillRect(0, 0, 캔버스크기, 캔버스크기);
  붓.fillStyle = "#fff";
  붓.strokeStyle = "#fff";
  붓.lineWidth = 붓두께;
  붓.lineCap = "round";
  붓.lineJoin = "round";
}

/** 화면 좌표를 그림판 내부 좌표(0~280)로 변환 — CSS 로 크기가 줄어든 휴대폰 화면에서도 맞도록 */
function 그림판_좌표(이벤트) {
  const 영역 = 그림판.getBoundingClientRect();
  return {
    x: ((이벤트.clientX - 영역.left) * 캔버스크기) / 영역.width,
    y: ((이벤트.clientY - 영역.top) * 캔버스크기) / 영역.height,
  };
}

/** 한 점에 둥근 붓 자국을 찍음 (클릭만 해도 점이 보이도록) */
function 점_찍기({ x, y }) {
  붓.beginPath();
  붓.arc(x, y, 붓두께 / 2, 0, Math.PI * 2);
  붓.fill();
}

/** 두 점을 둥근 끝 선으로 이음 */
function 선_긋기(시작, 끝) {
  붓.beginPath();
  붓.moveTo(시작.x, 시작.y);
  붓.lineTo(끝.x, 끝.y);
  붓.stroke();
}

/**
 * 캔버스 픽셀을 읽어 흑백 배열(0~255)로 만듦 — 흰 글씨이므로 빨강 채널 값만 쓰면 됨.
 * 아주 흐린 픽셀(잡음기준 미만)은 0으로 버림: 일부 브라우저는 개인정보 보호를 위해 캔버스를 읽을 때
 * 작은 잡음을 섞는데, 구석의 흐린 점 하나만 있어도 글씨 영역 자르기가 망가지기 때문.
 * (선 가장자리의 흐린 안티앨리어싱도 함께 빠져서 데스크톱의 PIL 그림과 더 비슷해짐)
 */
const 잡음기준 = 16;
function 흑백_픽셀_읽기() {
  const 데이터 = 붓.getImageData(0, 0, 캔버스크기, 캔버스크기).data;
  const 흑백 = new Uint8Array(캔버스크기 * 캔버스크기);
  for (let i = 0; i < 흑백.length; i++) {
    const 값 = 데이터[i * 4];
    흑백[i] = 값 < 잡음기준 ? 0 : 값;
  }
  return 흑백;
}

/** 현재 그림을 모델에 넣어 숫자를 예측하고 화면에 표시 */
function 인식하기() {
  if (앱가중치 === null) return;
  const 입력 = MNIST형식으로_변환(흑백_픽셀_읽기(), 캔버스크기, 캔버스크기);
  if (입력 === null) {
    확신도.textContent = "먼저 숫자를 그려 주세요";
    return;
  }
  const 확률 = 숫자인식CNN_추론(입력, 앱가중치);
  const 예측 = 가장_큰_위치(확률);
  결과숫자.textContent = String(예측);
  확신도.textContent = `확신도: ${(확률[예측] * 100).toFixed(1)}%`;
  막대_갱신(확률);
}

/** 그림판과 결과를 모두 초기화 */
function 지우기() {
  그림판_초기화();
  결과숫자.textContent = "?";
  확신도.textContent = "";
  막대_갱신(new Array(10).fill(0));
}

function 붓_대기(이벤트) {
  if (앱가중치 === null) return;
  // 그리는 중에 들어온 두 번째 손가락(주 포인터가 아님)은 무시.
  // 주 포인터가 새로 눌렸다면 이전 획의 떼기 이벤트를 놓친 것이므로 새 획으로 넘어감 (그림판이 멈추지 않도록)
  if (활성포인터 !== null && !이벤트.isPrimary) return;
  이벤트.preventDefault();
  // preventDefault 때문에 초점이 옮겨지지 않으므로, 버튼에 남은 초점을 직접 풀어 Esc·Enter 단축키가 그림판 기준으로 동작하게 함
  if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  활성포인터 = 이벤트.pointerId;
  이전좌표 = 그림판_좌표(이벤트);
  try {
    그림판.setPointerCapture(이벤트.pointerId);  // 그림판 밖으로 나가도 계속 이벤트를 받음
  } catch {
    // 캡처는 편의 기능일 뿐이므로, 브라우저가 거부해도(이미 사라진 포인터 등) 그리기는 계속함
  }
  점_찍기(이전좌표);
}

function 붓_움직임(이벤트) {
  if (이벤트.pointerId !== 활성포인터) return;
  // 버튼이 이미 모두 떼어졌는데 떼기 이벤트를 놓친 경우(창 전환 등) 선을 더 긋지 않고 획을 끝냄
  if (이벤트.buttons === 0) {
    붓_떼기(이벤트);
    return;
  }
  const 좌표 = 그림판_좌표(이벤트);
  선_긋기(이전좌표, 좌표);
  이전좌표 = 좌표;
}

/** 손을 떼면 선을 끊고 바로 인식 */
function 붓_떼기(이벤트) {
  if (이벤트.pointerId !== 활성포인터) return;
  활성포인터 = null;
  이전좌표 = null;
  인식하기();
}

/** 가중치를 불러오고 이벤트를 연결. 실패하면 안내를 보여 주고 그림판을 막음 */
function 시작하기() {
  막대_만들기();
  그림판_초기화();
  막대_갱신(new Array(10).fill(0));
  try {
    if (typeof 가중치데이터 === "undefined") throw new Error("weights.js 를 불러오지 못했습니다");
    앱가중치 = 가중치_해독(가중치데이터);
  } catch (오류) {
    오류안내.textContent = `모델 가중치를 불러오지 못했습니다 (${오류.message}). ` +
      "desktop_version 폴더에서 export_web_weights.py 를 실행해 weights.js 를 만들어 주세요.";
    오류안내.hidden = false;
    인식버튼.disabled = true;
    지우기버튼.disabled = true;
    그림판.classList.add("비활성");
    return;
  }
  그림판.addEventListener("pointerdown", 붓_대기);
  그림판.addEventListener("pointermove", 붓_움직임);
  // 손을 떼는 이벤트는 창 전체에서 받음: 포인터 캡처가 안 된 경우 그림판 밖에서 손을 떼도 획이 끝나도록
  window.addEventListener("pointerup", 붓_떼기);
  window.addEventListener("pointercancel", 붓_떼기);
  인식버튼.addEventListener("click", 인식하기);
  지우기버튼.addEventListener("click", 지우기);
  // 키보드 단축키: Enter = 다시 인식, Esc / Delete = 지우기
  // (버튼에 초점이 있을 때의 Enter 는 브라우저가 버튼을 누르므로 두 번 처리되지 않도록 제외)
  document.addEventListener("keydown", (이벤트) => {
    if (이벤트.key === "Escape" || 이벤트.key === "Delete") 지우기();
    else if (이벤트.key === "Enter" && !(이벤트.target instanceof HTMLButtonElement)) 인식하기();
  });
}

시작하기();
