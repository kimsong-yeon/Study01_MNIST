# 손글씨 인식기 웹/데스크톱 분리 설계

- 작성일: 2026-09-28
- 상태: 승인됨

## 1. 목적과 범위

손글씨 숫자 인식 프로그램을 두 버전으로 나눈다.

- **desktop_version/**: 기존 PyTorch + tkinter 앱을 그대로 옮긴다 (코드 동작 변경 없음).
- **web_version/**: 새로 작성한다. 외부 라이브러리 없이 순수 자바스크립트로 추론하며, 폴더 내용을 그대로 GitHub Pages에 정적으로 올릴 수 있어야 한다.
- 루트와 두 폴더에 각각 `CLAUDE.md` 를 둔다.

### 사용자가 정한 사항
- 배포: **정적 파일만 준비**한다. git 저장소 생성·GitHub Actions·배포 설정은 하지 않는다.
- 가상환경: `desktop_version/.venv` 를 **새로 만들고** 기존 루트 `.venv` 는 삭제한다.
- 가중치 전달: **B안** — base64로 인코딩한 `weights.js` 를 `<script>` 로 읽는다 (`file://` 과 GitHub Pages 모두 동작).

### 범위 밖
- git 저장소 생성, 배포 자동화
- 모델 구조 변경·재학습
- PWA, 오프라인 캐시 등 부가 기능

### 성공 기준
1. `desktop_version/.venv/Scripts/python desktop_version/app.py` 로 기존과 똑같이 앱이 실행되고, 새로 만든 바탕 화면 바로가기로도 실행된다.
2. `web_version/index.html` 을 더블클릭(`file://`)하거나 정적 서버로 열면 그림판에서 숫자를 그려 인식할 수 있다 (마우스·터치).
3. `web_version/tests/test.html` 의 모든 검사가 통과한다: JS 모델 추론이 PyTorch와 일치하고, JS 전처리가 파이썬 전처리와 거의 일치한다.
4. 웹 버전은 외부 라이브러리·CDN·빌드 도구를 전혀 쓰지 않는다.

## 2. 폴더 구조

```
study01_minist/
├─ CLAUDE.md                  두 버전 요약·공유 계약·폴더 안내 (다시 작성)
├─ README.md                  전체 소개 + 두 버전 링크 (짧게 다시 작성)
├─ docs/superpowers/          설계·계획 문서
├─ desktop_version/
│  ├─ CLAUDE.md               새로 작성
│  ├─ README.md               기존 README 이동 + 가중치 내보내기 절 추가
│  ├─ app.py model.py train.py make_shortcut.py   (수정 없이 이동)
│  ├─ app.ico mnist_cnn.pt data/                   (이동)
│  ├─ export_web_weights.py   새 파일
│  └─ .venv/                  새로 생성
└─ web_version/               이 폴더 내용이 곧 GitHub Pages 사이트
   ├─ CLAUDE.md  README.md
   ├─ index.html  style.css
   ├─ weights.js              생성 파일 (export_web_weights.py)
   ├─ js/model.js             추론 엔진 (DOM 없음)
   ├─ js/preprocess.js        전처리 (DOM 없음)
   ├─ js/app.js               화면·그림판 (DOM)
   └─ tests/
      ├─ test.html            브라우저 테스트 페이지
      ├─ tests.js             검사 코드
      └─ reference.js         생성 파일 (export_web_weights.py)
```

파일 이름은 영어로 둔다 (한글 파일명은 GitHub Pages URL에서 퍼센트 인코딩되므로). 코드 안의 식별자·주석은 한글로 작성한다.

## 3. 데스크톱 버전 이동 절차

1. `desktop_version/.venv` 생성 (Microsoft Store판 Python 3.13) 후 `torch torchvision` (CPU 인덱스), `pillow`, `numpy` 설치.
2. `app.py model.py train.py make_shortcut.py app.ico mnist_cnn.pt data/ README.md` 를 `desktop_version/` 로 이동.
3. `app.py` 실행 확인 (가중치 로드·전처리·추론까지 스크립트로 확인하고, 창도 한 번 띄워 확인).
4. 루트의 기존 `.venv/`, `__pycache__/` 삭제.
5. `desktop_version/.venv/Scripts/python desktop_version/make_shortcut.py` 재실행 → 같은 이름의 바탕 화면 바로가기를 새 경로로 덮어씀. 앱 ID(`DSMP.HandwritingDigitRecognizer`)는 그대로.

참고:
- `app.py` · `make_shortcut.py` 는 이미 파일 위치 기준으로 경로를 계산하므로 수정하지 않는다.
- `train.py` 는 상대 경로(`"data"`, `"mnist_cnn.pt"`)를 쓰므로 `desktop_version/` 을 작업 폴더로 하여 실행해야 한다 (CLAUDE.md에 명시, 코드는 수정하지 않음).

## 4. 가중치 내보내기: `desktop_version/export_web_weights.py`

- `mnist_cnn.pt` 의 `state_dict` 를 읽어 `num_batches_tracked` 를 제외한 모든 텐서를 float32 리틀엔디언으로 이어 붙인 뒤 base64로 인코딩한다.
- 출력 `../web_version/weights.js`:
  ```js
  // 자동 생성 파일 — 직접 수정하지 마세요 (desktop_version/export_web_weights.py)
  const 가중치데이터 = {
    목록: [ { 이름: "합성곱1.weight", 형태: [32,1,3,3], 시작: 0, 개수: 288 }, ... ],  // 시작·개수는 float 단위
    base64: "...",
  };
  ```
- 출력 `../web_version/tests/reference.js` (`const 기준데이터 = {...}`):
  - `모델사례`: MNIST 시험 데이터 앞 20장의 정규화된 입력(784) · PyTorch 로짓(10) · 정답.
  - `전처리사례`: 합성 손글씨 5장 (세로선, 7, 0, 작은 점, 아래 가장자리 가로선). 280x280 PIL 이미지에 `ImageDraw` 로 선/원을 그려 만든 원본 픽셀(0~255, 길이 78400)과, `app.py` 의 `MNIST형식으로_변환()` 결과(정규화된 784 값), 그 입력에 대한 PyTorch 로짓.
  - 원본 픽셀은 크기를 줄이기 위해 0~255 정수를 base64(Uint8)로 저장한다.
- `app.py` 를 import해도 `__main__` 블록만 있으므로 창이 뜨지 않는다.
- 콘솔 한글 출력을 위해 맨 위에서 `sys.stdout.reconfigure(encoding="utf-8")` 호출.
- 경로는 스크립트 파일 위치 기준으로 계산한다.

## 5. 웹 버전 구성

### 5.1 스크립트 로딩
- ES 모듈은 `file://` 에서 브라우저가 차단하므로 **일반 `<script>` 태그**로 순서대로 읽고 전역 함수로 연결한다.
- `index.html` 로딩 순서: `weights.js` → `js/model.js` → `js/preprocess.js` → `js/app.js`.
- `tests/test.html` 로딩 순서: `../weights.js` → `reference.js` → `../js/model.js` → `../js/preprocess.js` → `tests.js`.

### 5.2 `js/model.js` (DOM 없음)
- `가중치_해독(가중치데이터)` → `{ "합성곱1.weight": {형태, 값: Float32Array}, ... }`. base64 → `Uint8Array` → `Float32Array` (리틀엔디언 가정).
- 층 함수 (모두 채널 우선 배열 `[채널][세로][가로]` 를 1차원 배열로 표현, 중간 계산은 오차 누적을 막기 위해 `Float64Array`):
  - `합성곱(입력, 입력채널, 크기, 가중치, 편향)` — 3x3, padding 1, stride 1.
  - `배치정규화(입력, 채널, 감마, 베타, 평균, 분산)` — eps = 1e-5 (PyTorch 기본값).
  - `렐루(입력)`, `최대풀링(입력, 채널, 크기)` — 2x2, stride 2.
  - `완전연결(입력, 가중치, 편향, 출력수)` — 가중치 형태 `[출력][입력]`.
  - `소프트맥스(로짓)` — 최댓값을 빼서 안정적으로 계산.
- `숫자인식CNN_로짓(입력784, 가중치)` 와 `숫자인식CNN_추론(입력784, 가중치)`(확률 반환). 층 순서는 `model.py` 의 `forward` 와 같다. 드롭아웃은 추론 시 아무 일도 하지 않으므로 생략하고 주석으로 표시한다.

### 5.3 `js/preprocess.js` (DOM 없음)
- `평균 = 0.1307`, `표준편차 = 0.3081` (train.py·app.py와 같은 값).
- `파이썬식_반올림(x)` — 은행가 반올림 (`2.5→2`, `3.5→4`, `-0.5→0`).
- `MNIST형식으로_변환(흑백픽셀, 가로, 세로)` → 정규화된 `Float32Array(784)` 또는 빈 그림이면 `null`.
  1. 0이 아닌 픽셀의 경계 상자로 자르기 (PIL `getbbox` 와 같이 오른쪽·아래 끝은 +1).
  2. 긴 변을 20으로 맞추는 배율로 축소. 새 크기 = `max(1, 파이썬식_반올림(길이 * 배율))`. Lanczos3 필터를 가로→세로 순서로 분리 적용하며, 축소 시 필터 폭을 배율만큼 넓힌다 (PIL `ImagingResample` 과 같은 방식). 결과는 0~255로 자르고 반올림.
  3. 28x28 검은 배경에 `((28-가로)//2, (28-세로)//2)` 위치로 붙이기.
  4. 무게중심을 구해 `이동 = 파이썬식_반올림(14 - 중심)` 만큼 정수 평행 이동 (밖으로 나간 부분은 버리고 빈 곳은 0).
  5. `/255` 후 `(값 - 평균) / 표준편차`.
- PIL 내부 정수 연산과 비트 단위로 같지는 않으므로 테스트는 허용 오차로 비교한다.

### 5.4 `js/app.js` 와 화면
- `<canvas>` 280x280, 검은 배경, 흰 선, 붓 두께 18, `lineCap/lineJoin = "round"`. 점만 찍어도 원이 그려지게 한다.
- 인식할 때 캔버스를 `getImageData` 로 읽어 R 채널을 흑백 값으로 쓴다 (데스크톱처럼 이미지를 두 벌 관리하지 않음).
- 포인터 이벤트(`pointerdown/move/up/cancel`, `setPointerCapture`)로 마우스·터치 모두 지원. 캔버스에 `touch-action: none`. CSS 표시 크기가 280보다 작으면 `getBoundingClientRect` 비율로 좌표 환산.
- 손을 떼면 자동 인식. `인식하기` 버튼 / `Enter` = 다시 인식, `지우기` 버튼 / `Esc` / `Delete` = 초기화.
- 결과 영역: 큰 예측 숫자, `확신도: xx.x%`, 0~9 확률 막대 (최댓값 막대는 파란색 `#1a73e8`, 나머지 회색 `#9aa0a6`).
- 레이아웃: 넓은 화면은 그림판 | 결과 가로 배치, 좁은 화면(휴대폰)은 세로 배치. 가로 스크롤 없음.
- 오류 처리:
  - `가중치데이터` 가 없거나 해독에 실패하면 안내 문구("desktop_version 에서 export_web_weights.py 를 실행하세요")를 표시하고 그림판·버튼을 비활성화.
  - 빈 그림에서 인식하면 "먼저 숫자를 그려 주세요".

### 5.5 데이터 흐름
```
포인터 드래그 → 캔버스에 그리기 → 손 뗌 → getImageData → 흑백 배열(280x280)
 → MNIST형식으로_변환 → 숫자인식CNN_추론 → 확률 10개 → 결과 숫자·확신도·막대
```

## 6. 검증

### 6.1 브라우저 테스트 페이지 (`tests/test.html`)
외부 라이브러리 없이 `검사(이름, 함수)` 로 결과를 표로 출력하고, 맨 위에 `통과 N / 전체 M` 을 표시한다. 자동 확인을 위해 `window.테스트결과 = {통과, 전체, 실패목록}` 을 남긴다.

| 검사 | 기준 |
|---|---|
| 가중치 해독 | 모든 층의 형태·개수가 목록과 일치, 총 개수가 base64 길이와 일치 |
| 모델 추론 20장 | 로짓 최대 절대 오차 < 1e-4, 예측 숫자 일치 |
| `파이썬식_반올림` | 0.5→0, 1.5→2, 2.5→2, 3.5→4, -0.5→0, -1.5→-2, 2.4→2, 2.6→3 |
| 전처리 5장 | 픽셀 최대 오차 ≤ 3/255 (정규화 전 기준), 전처리 결과로 추론한 예측 숫자가 파이썬과 일치 |
| 빈 그림 | `null` 반환 |

### 6.2 진행 방식
- TDD: 기준값·테스트를 먼저 만들고 실패를 확인한 뒤 구현한다.
- 내장 브라우저로 `tests/test.html` 과 `index.html` 을 열어 확인한다. 그림판에 드래그로 숫자를 그려 인식되는지, 375px 폭에서도 레이아웃이 깨지지 않는지 본다.
- 데스크톱: 새 `.venv` 로 `app.py` 의 모델 로드·추론을 스크립트로 확인하고, 창을 띄워 확인하고, 바로가기를 다시 만든다.

## 7. CLAUDE.md 3개

- **루트 `CLAUDE.md`**: 프로젝트 개요, 두 폴더 안내, 한글 작성 규칙, 두 버전이 공유하는 계약(모델 구조, 정규화 값 0.1307/0.3081, 전처리 5단계), 연결 관계(모델 재학습 → `export_web_weights.py` 재실행 → `weights.js`·`reference.js` 갱신).
- **`desktop_version/CLAUDE.md`**: 기존 루트 CLAUDE.md 내용(실행 환경·명령어·그림판 두 벌·바로가기·앱ID·`make_shortcut.py` 방식) + `.venv` 위치, `desktop_version/` 을 작업 폴더로 실행해야 하는 점, `export_web_weights.py` 설명.
- **`web_version/CLAUDE.md`**: 순수 JS·외부 라이브러리 금지, ES 모듈을 쓰지 않는 이유, 스크립트 로딩 순서, DOM 없는 파일과 DOM 파일의 분리, 생성 파일(`weights.js`, `tests/reference.js`) 직접 수정 금지, 전처리·정규화 변경 시 `desktop_version/app.py` 와 함께 수정, 테스트 방법, GitHub Pages 게시 방법(이 폴더 내용을 저장소 루트 또는 `/docs` 에 올리기).
