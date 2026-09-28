# CLAUDE.md — desktop_version

This file provides guidance to Claude Code (claude.ai/code) when working with code in this folder.

## 이 폴더

손글씨 숫자 인식기의 **데스크톱(윈도우 tkinter) 버전**입니다. PyTorch로 MNIST CNN을 학습하고, 학습된 가중치(`mnist_cnn.pt`)로 그림판 앱을 실행합니다. 사용법·모델 구조·학습 설정은 `README.md` 에 있습니다. 웹 버전과 함께 지켜야 할 규칙은 루트의 `../CLAUDE.md` 를 참고하세요.

## 작성 규칙

- **모든 코드와 주석은 한글로 작성합니다.** 변수·함수·클래스 이름도 한글 식별자를 씁니다 (예: `숫자인식CNN`, `MNIST형식으로_변환`, `앱ID`). 새 코드도 이 방식을 따릅니다.
- 콘솔에 한글을 출력하는 스크립트는 윈도우 콘솔에서 깨지지 않도록 맨 위에서 `sys.stdout.reconfigure(encoding="utf-8")` 를 호출합니다.

## 실행 환경과 명령어

- 윈도우 11, Microsoft Store판 Python 3.13 기반의 전용 가상환경 `desktop_version/.venv` 를 사용합니다 (PyTorch 2.14 CPU, torchvision 0.29, Pillow 12.3, numpy 2.5). 시스템 Python에는 PyTorch가 없으므로 항상 `.venv/Scripts/python` 으로 실행합니다.
- **명령은 `desktop_version/` 을 작업 폴더로 해서 실행합니다.** `train.py` 는 `data/` 와 `mnist_cnn.pt` 를 상대 경로로 쓰므로 다른 폴더에서 실행하면 엉뚱한 곳에 파일이 생깁니다. (`app.py`, `make_shortcut.py` 는 파일 위치 기준으로 경로를 계산하므로 어디서 실행해도 됩니다.)
- 빌드·린트·테스트 도구는 없습니다.

```bash
cd desktop_version
.venv/Scripts/python train.py          # 학습 (CPU 약 9분) → mnist_cnn.pt 생성, MNIST는 data/ 에 자동 다운로드
.venv/Scripts/python app.py            # 그림판 앱 실행 (mnist_cnn.pt 필요)
.venv/Scripts/python make_shortcut.py  # app.ico 생성 + 바탕 화면 바로가기 생성
.venv/Scripts/python export_web_weights.py  # ../web_version/weights.js 와 tests/reference.js 생성
```

가상환경을 다시 만들어야 할 때 (`.venv` 는 절대 경로가 들어 있어서 폴더를 옮기면 깨집니다):

```bash
cd desktop_version
python -m venv .venv
.venv/Scripts/python -m pip install torch==2.14.0 torchvision==0.29.0 --index-url https://download.pytorch.org/whl/cpu
.venv/Scripts/python -m pip install pillow==12.3.0 numpy==2.5.2
```

## 구조 (여러 파일에 걸친 연결 관계)

- **`model.py` 는 학습과 추론이 공유합니다.** `train.py` 는 `state_dict` 만 `mnist_cnn.pt` 에 저장하고, `app.py` 는 같은 클래스로 모델을 만든 뒤 가중치를 불러옵니다. 모델 구조를 바꾸면 반드시 다시 학습해야 합니다.
- **전처리는 학습과 똑같이 맞춰야 합니다.** 정규화 값(평균 0.1307, 표준편차 0.3081)은 `train.py` 와 `app.py` 에 각각 따로 정의되어 있으니, 바꿀 때는 두 곳을 함께 수정합니다. `app.py` 의 `MNIST형식으로_변환()` 은 그린 글씨를 MNIST 형식으로 바꿉니다: 글씨 영역 자르기 → 긴 변을 20px로 축소 → 28x28 가운데 배치 → 무게중심 보정. 이 과정을 빼면 직접 그린 글씨의 인식률이 크게 떨어집니다.
- **그림판 이미지는 두 벌로 관리됩니다.** 화면에 보이는 tkinter `Canvas` 와 별도로, 인식에 쓰는 PIL 흑백 이미지(검은 배경 + 흰 글씨)에 선을 동시에 그립니다. 그리기나 지우기 로직을 바꿀 때는 두 곳을 함께 수정해야 합니다.
- **윈도우 바로가기 / 작업 표시줄 연동:**
  - 바로가기는 `.venv\Scripts\pythonw.exe "app.py"` 를 실행하므로 콘솔 창이 없습니다. 그래서 `app.py` 는 시작할 때 생긴 오류를 `messagebox` 로 보여 줍니다.
  - 모든 파일 경로는 현재 작업 폴더가 아니라 `app.py` 가 있는 폴더를 기준으로 계산합니다.
  - 바로가기에는 절대 경로가 들어가므로 폴더를 옮기면 `make_shortcut.py` 를 다시 실행해야 합니다.
  - Store판 Python은 앱 창이 "Python" 으로 묶이므로, `app.py` 가 Tk 창을 만들기 전에 `SetCurrentProcessExplicitAppUserModelID(앱ID)` 를 호출합니다. 바로가기에도 같은 AppUserModelID를 넣어야 작업 표시줄의 고정 아이콘과 실행 중인 창이 하나로 합쳐집니다. `make_shortcut.py` 는 이 값을 `app.py` 에서 import해서 씁니다.
- **`make_shortcut.py` 의 바로가기 생성 방식:**
  - AppUserModelID는 `WScript.Shell` 로는 넣을 수 없어서, PowerShell 안의 C# 코드(`Add-Type`)로 `IShellLinkW` / `IPropertyStore` COM 인터페이스를 직접 호출합니다.
  - 경로에 한글과 공백이 있으므로 스크립트는 `-EncodedCommand`(UTF-16LE base64)로, 경로 값은 `SC_*` 환경 변수로 넘깁니다.
  - PowerShell은 CP949로 출력할 수 있어서, 출력은 `출력_해독()` 으로 읽습니다 (UTF-8 → mbcs 순서로 시도).
  - 바탕 화면이 OneDrive로 옮겨져 있을 수 있으므로 경로는 `[Environment]::GetFolderPath('Desktop')` 으로 구합니다.
- **웹 버전으로 가중치 내보내기 (`export_web_weights.py`):**
  - `mnist_cnn.pt` 의 텐서를 float32 리틀엔디언으로 이어 붙여 base64로 담은 `../web_version/weights.js` 를 만듭니다 (`num_batches_tracked` 제외). 웹 버전은 이 파일의 층 이름(`합성곱1.weight` 등)으로 가중치를 찾으므로 `model.py` 의 속성 이름을 바꾸면 웹 코드도 함께 고쳐야 합니다.
  - 웹 테스트용 기준값 `../web_version/tests/reference.js` 도 함께 만듭니다: MNIST 시험 데이터 20장의 PyTorch 로짓과, 합성 손글씨 5장에 대한 `app.py` 의 `MNIST형식으로_변환()` 결과·로짓.
  - **모델을 다시 학습했거나 `app.py` 의 전처리를 바꿨다면 반드시 다시 실행합니다.** 두 출력 파일은 생성 파일이므로 직접 수정하지 않습니다.
