# CLAUDE.md — web_version

This file provides guidance to Claude Code (claude.ai/code) when working with code in this folder.

## 이 폴더

손글씨 숫자 인식기의 **웹 버전**입니다. `desktop_version` 에서 PyTorch로 학습한 CNN 가중치를 그대로 가져와, **외부 라이브러리 없이 순수 자바스크립트로** 브라우저 안에서 추론합니다. 이 폴더의 내용이 곧 정적 웹사이트이며 GitHub Pages에 그대로 올릴 수 있습니다. 두 버전이 함께 지켜야 할 규칙은 루트의 `../CLAUDE.md` 를 참고하세요.

## 작성 규칙

- **모든 코드와 주석은 한글로 작성합니다.** 자바스크립트 함수·변수, CSS 클래스, HTML 요소 id 도 한글을 씁니다 (예: `숫자인식CNN_추론`, `MNIST형식으로_변환`, `#그림판`, `.막대줄`). 파일 이름만 영어로 둡니다 (한글 파일명은 GitHub Pages URL에서 퍼센트 인코딩되기 때문).
- **외부 라이브러리·CDN·빌드 도구·npm 을 쓰지 않습니다.** 텐서 연산도 직접 구현합니다.
- **ES 모듈(`type="module"`, `import`/`export`)을 쓰지 않습니다.** 브라우저는 `file://` 로 연 페이지의 모듈 로딩을 막기 때문에, `index.html` 을 더블클릭해도 동작하도록 일반 `<script>` 로 순서대로 읽고 전역 함수로 연결합니다.
- 스크립트들이 전역 스코프를 공유하므로 **최상위 `const`/`let`/`function` 이름이 파일끼리 겹치면 안 됩니다** (겹치면 뒤 파일이 `SyntaxError` 로 통째로 실행되지 않음).

## 파일 구성과 로딩 순서

- `index.html`: `weights.js` → `js/model.js` → `js/preprocess.js` → `js/app.js`
- `tests/test.html`: `../weights.js` → `reference.js` → `../js/model.js` → `../js/preprocess.js` → `tests.js`

| 파일 | 역할 | DOM |
|---|---|---|
| `weights.js` | **생성 파일.** `const 가중치데이터 = { 목록: [{이름, 형태, 시작, 개수}], base64 }` — 모든 가중치를 float32 리틀엔디언으로 이어 붙인 base64 | ✗ |
| `js/model.js` | `가중치_해독()`, 층 함수(`합성곱`·`배치정규화`·`렐루`·`최대풀링`·`완전연결`·`소프트맥스`), `숫자인식CNN_로짓()`/`숫자인식CNN_추론()`, `가장_큰_위치()` | ✗ |
| `js/preprocess.js` | `MNIST형식으로_변환(흑백픽셀, 가로, 세로)` → 정규화된 `Float32Array(784)` 또는 `null`, `파이썬식_반올림()`, Lanczos3 `크기_바꾸기()` | ✗ |
| `js/app.js` | 그림판(포인터 이벤트), 버튼·단축키, 결과·확률 막대 표시, 가중치 불러오기 실패 안내 | ✓ |
| `tests/test.html`, `tests/tests.js` | 브라우저 테스트 페이지 (외부 라이브러리 없는 `검사(이름, 함수)`) | ✓ |
| `tests/reference.js` | **생성 파일.** `const 기준데이터` — PyTorch 로짓 20건, 파이썬 전처리 결과 5건 | ✗ |

계산 파일(`model.js`, `preprocess.js`)은 DOM을 쓰지 않아야 테스트 페이지에서 그대로 검증할 수 있습니다. 화면 관련 코드는 `app.js` 에만 둡니다.

## 여러 파일에 걸친 연결 관계

- **생성 파일은 직접 수정하지 않습니다.** `weights.js` 와 `tests/reference.js` 는 `desktop_version/export_web_weights.py` 가 만듭니다. 모델을 다시 학습했거나 데스크톱 전처리를 바꿨다면 다시 생성합니다:
  ```bash
  cd ../desktop_version
  .venv/Scripts/python export_web_weights.py
  ```
- **`js/model.js` 는 `desktop_version/model.py` 의 `forward` 를 그대로 따라갑니다** (합성곱 → 배치정규화 → ReLU → 최대풀링 두 번 → 완전연결 → ReLU → 완전연결, 드롭아웃은 추론에서 생략). 가중치는 `model.py` 의 속성 이름(`합성곱1.weight` 등)으로 찾으므로 모델 구조나 속성 이름이 바뀌면 이 파일도 함께 고칩니다. 배치정규화 eps 는 PyTorch 기본값 `1e-5` 입니다. 중간 계산은 `Float64Array` 로 해서 PyTorch 로짓과 약 1e-6 이내로 일치합니다.
- **`js/preprocess.js` 는 `desktop_version/app.py` 의 `MNIST형식으로_변환()` 과 같아야 합니다:** 글씨 영역 자르기 → 긴 변을 20px로 Lanczos 축소 → 28x28 가운데 배치 → 무게중심 보정 → 정규화(평균 0.1307, 표준편차 0.3081). 한쪽을 바꾸면 다른 쪽도 바꾸고 기준값을 다시 생성합니다.
  - 축소는 Pillow의 `LANCZOS` 와 같은 방식(가로 → 세로 분리 적용, 축소 시 필터 폭 확대, 매 단계 0~255 반올림)으로 직접 구현했습니다. 테스트 허용 오차는 픽셀 3이지만 현재는 Pillow와 완전히 같은 값(오차 0)이 나옵니다.
  - 파이썬 `round()` 는 은행가 반올림(2.5 → 2)이므로 `Math.round` 대신 `파이썬식_반올림()` 을 씁니다.
- **그림판은 이미지를 한 벌만 씁니다.** 데스크톱과 달리 화면의 `<canvas>`(내부 280x280, 검은 배경·흰 선·붓 두께 18)를 `getImageData` 로 읽어 빨강 채널을 흑백 값으로 씁니다. CSS 로 표시 크기가 줄어드는 휴대폰에서는 `그림판_좌표()` 가 `getBoundingClientRect` 비율로 좌표를 환산합니다.
- **캔버스 읽기 잡음 기준:** `흑백_픽셀_읽기()` 는 16 미만의 흐린 픽셀을 0으로 버립니다. 일부 브라우저(개인정보 보호 기능)가 캔버스 읽기에 잡음을 섞으면 구석의 점 하나 때문에 글씨 영역 자르기가 망가지기 때문입니다. 이 처리는 `app.js` 에만 두고, 파이썬과 비교 검증하는 `preprocess.js` 는 `app.py` 와 똑같이 유지합니다.
- **포인터 처리:**
  - 한 번에 한 포인터(`활성포인터`)만 그리고, 그리는 중에 들어온 주 포인터가 아닌 손가락(`isPrimary === false`)은 무시합니다. 주 포인터가 새로 눌리면 이전 획의 떼기 이벤트를 놓친 것으로 보고 새 획을 시작하며, `buttons === 0` 인 이동이 오면 획을 끝냅니다 (그림판이 멈추지 않도록).
  - `setPointerCapture` 는 실패해도 그리기가 계속되도록 `try` 로 감쌌고, 그래서 손을 떼는 이벤트(`pointerup`/`pointercancel`)는 그림판이 아니라 `window` 에서 받습니다.
  - `pointerdown` 에서 `preventDefault()` 를 하면 초점이 옮겨지지 않으므로 직접 `blur()` 합니다. 그렇지 않으면 버튼을 한 번 누른 뒤 Enter 가 그 버튼(지우기)을 눌러 버립니다. Esc/Delete 는 초점 위치와 관계없이 항상 지우기입니다.
- **로컬 서버 캐시 주의:** `python -m http.server` 는 캐시 헤더를 주지 않아 브라우저가 옛 JS 를 계속 쓸 수 있습니다. 코드를 고친 뒤 결과가 이상하면 강력 새로고침(Ctrl+F5)하거나 `fetch(파일, { cache: "reload" })` 로 갱신합니다.

## 테스트와 확인

빌드·린트 도구는 없습니다. 브라우저 테스트 페이지로 JS 계산이 PyTorch·파이썬과 일치하는지 확인합니다.

```bash
python -m http.server 8765 --directory web_version   # 저장소 루트에서 실행 (.claude/launch.json 의 "web" 설정과 같음)
```

- `http://localhost:8765/tests/test.html` — 맨 위가 `통과 30 / 전체 30` 이어야 합니다. 자동 확인은 페이지의 `window.테스트결과` (`{통과, 전체, 실패목록}`) 를 읽습니다.
- `http://localhost:8765/index.html` — 실제 앱. 넓은 화면(가로 배치)과 600px 이하(세로 배치, 캔버스 축소) 둘 다 확인합니다.
- `index.html`·`tests/test.html` 은 `file://` 로 더블클릭해 열어도 동작해야 합니다. Claude Code 내장 브라우저는 `file://` 을 정적 스냅샷으로 보여 주므로, 자동 확인은 헤드리스 Edge로 합니다:
  ```powershell
  & "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe" --headless=new --disable-gpu --user-data-dir="$env:TEMP\edge-test" --virtual-time-budget=10000 --dump-dom "file:///<web_version 절대 경로>/tests/test.html"
  ```
  출력(Start-Process 의 `-RedirectStandardOutput` 으로 받기)에서 `<div id="요약" ...>통과 30 / 전체 30</div>` 을 확인합니다.

## GitHub Pages 게시

저장소 `kimsong-yeon/Study01_MNIST` 의 `main` 브랜치에서 `web_version/` 이 바뀌면 `.github/workflows/pages.yml` (GitHub Actions)이 이 폴더 내용을 그대로 GitHub Pages 에 배포합니다 (저장소 설정 → Pages 의 Source 는 "GitHub Actions"). 빌드 과정이 없으므로 올린 파일이 그대로 서비스되며 `tests/` 도 함께 올라갑니다.

- 앱: https://kimsong-yeon.github.io/Study01_MNIST/
- 테스트: https://kimsong-yeon.github.io/Study01_MNIST/tests/test.html
- 화면 맨 위 `<header class="학생정보">` 에 학번·이름을 표시합니다.
