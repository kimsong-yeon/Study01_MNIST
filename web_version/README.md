# 손글씨 숫자 인식기 — 웹 버전

마우스나 손가락으로 숫자(0~9)를 그리면 합성곱 신경망(CNN)이 어떤 숫자인지 인식합니다.
PyTorch로 학습한 MNIST 모델의 가중치를 그대로 가져와 **외부 라이브러리 없이 순수 자바스크립트로** 브라우저 안에서 계산합니다. 서버가 필요 없는 정적 사이트라 GitHub Pages에 그대로 올릴 수 있습니다.

## 실행

- `index.html` 을 더블클릭해 브라우저로 열거나,
- 정적 서버로 엽니다: `python -m http.server 8765 --directory web_version` → `http://localhost:8765/`

| 조작 | 동작 |
|---|---|
| 마우스 드래그 / 손가락으로 그리기 | 숫자 그리기 (손을 떼면 자동 인식) |
| `인식하기` 버튼 / `Enter` | 다시 인식 |
| `지우기` 버튼 / `Esc` / `Delete` | 그림판 지우기 |

## 파일 구성

| 파일 | 설명 |
|---|---|
| `index.html`, `style.css` | 화면 |
| `js/app.js` | 그림판과 결과 표시 |
| `js/model.js` | CNN 추론 엔진 (합성곱·배치정규화·풀링·완전연결을 직접 구현) |
| `js/preprocess.js` | 그린 글씨를 MNIST 형식(28x28, 가운데 정렬)으로 바꾸는 전처리 |
| `weights.js` | 학습된 가중치 (`desktop_version/export_web_weights.py` 로 생성) |
| `tests/` | 자바스크립트 계산이 PyTorch와 같은지 확인하는 테스트 페이지 |

## 가중치 다시 만들기

데스크톱 버전에서 모델을 다시 학습했다면 가중치 파일도 다시 만들어야 합니다.

```bash
cd desktop_version
.venv/Scripts/python export_web_weights.py
```

## 테스트

`tests/test.html` 을 브라우저로 열면 가중치 해독, 모델 추론(PyTorch 로짓과 비교), 전처리(파이썬 결과와 비교) 검사 결과가 표로 나옵니다. 맨 위가 `통과 30 / 전체 30` 이면 정상입니다.

## GitHub Pages에 올리기

1. GitHub 저장소를 만들고 이 폴더 안의 파일들을 저장소 루트(또는 `docs/` 폴더)에 올립니다.
2. 저장소 **Settings → Pages** 에서 브랜치와 폴더(`/ (root)` 또는 `/docs`)를 선택합니다.
3. 잠시 후 `https://<사용자이름>.github.io/<저장소이름>/` 에서 앱이 열립니다.
