# 손글씨 숫자 인식기 (PyTorch + MNIST)

마우스나 손가락으로 숫자(0~9)를 그리면 합성곱 신경망(CNN)이 어떤 숫자인지 인식합니다. 같은 모델을 두 가지 형태로 제공합니다.

| 버전 | 설명 | 안내 |
|---|---|---|
| 데스크톱 | PyTorch로 MNIST를 학습하고 윈도우 tkinter 그림판 앱으로 실행 | [desktop_version/README.md](desktop_version/README.md) |
| 웹 | 학습된 가중치를 순수 자바스크립트로 실행하는 정적 웹 앱 — **[바로 실행](https://kimsong-yeon.github.io/Study01_MNIST/)** | [web_version/README.md](web_version/README.md) |

웹 버전은 `main` 브랜치에 올리면 GitHub Actions(`.github/workflows/pages.yml`)가 GitHub Pages 에 자동으로 배포합니다. 모든 프로젝트에 공통으로 쓰는 규칙은 [CLAUDE_전역.md](CLAUDE_전역.md) 에 있습니다.

## 흐름

```
desktop_version/train.py  →  mnist_cnn.pt  →  desktop_version/app.py (데스크톱 앱)
                                  │
                                  └→ export_web_weights.py → web_version/weights.js → web_version/index.html (웹 앱)
```
