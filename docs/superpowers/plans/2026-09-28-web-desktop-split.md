# 손글씨 인식기 웹/데스크톱 분리 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 PyTorch/tkinter 앱을 `desktop_version/` 으로 옮기고, 같은 모델 가중치로 순수 자바스크립트 추론을 하는 정적 웹 앱 `web_version/` 을 새로 만든다.

**Architecture:** `desktop_version/export_web_weights.py` 가 `mnist_cnn.pt` 를 base64 float32로 담은 `web_version/weights.js` 와 테스트 기준값 `web_version/tests/reference.js` 를 생성한다. 웹은 ES 모듈 없이 일반 `<script>` 로 `weights.js → js/model.js → js/preprocess.js → js/app.js` 를 읽으며, DOM 없는 계산 파일(model/preprocess)은 브라우저 테스트 페이지로 PyTorch 결과와 비교 검증한다.

**Tech Stack:** Python 3.13 (Store판) + PyTorch 2.14 CPU / torchvision 0.29 / Pillow 12.3 / numpy 2.5 (데스크톱·내보내기), HTML + CSS + 순수 JavaScript (웹, 외부 라이브러리 없음).

**Spec:** `docs/superpowers/specs/2026-09-28-web-desktop-split-design.md`

> 이 폴더는 git 저장소가 아니므로 커밋 단계는 없다. 각 작업은 검증 단계로 끝난다.
> 모든 명령은 프로젝트 루트 `C:\Users\user\DSMP\3장 손글씨 앱\study01_minist` 에서 Bash(Git Bash) 기준으로 적었다 (경로에 공백·한글이 있으므로 필요한 곳은 따옴표로 감싼다).

## Global Constraints

- 모든 코드·주석·식별자는 한글로 작성한다 (JS 함수·변수·CSS 클래스·요소 id 포함). 파일 이름만 영어로 둔다.
- 콘솔에 한글을 출력하는 파이썬 스크립트는 맨 위에서 `sys.stdout.reconfigure(encoding="utf-8")` 를 호출한다.
- 웹 버전은 외부 라이브러리·CDN·빌드 도구·ES 모듈(`type="module"`, `import`/`export`)을 쓰지 않는다.
- 웹 스크립트들은 전역 스코프를 공유하므로 최상위 `const`/`let`/`function` 이름이 파일끼리 겹치면 안 된다.
- 정규화 값은 평균 `0.1307`, 표준편차 `0.3081` (train.py·app.py·preprocess.js 세 곳이 같아야 함).
- 배치정규화 eps = `1e-5`.
- 그림판: 280x280, 검은 배경·흰 선, 붓 두께 18, 둥근 끝.
- 막대 색: 최댓값 `#1a73e8`, 나머지 `#9aa0a6`.
- 데스크톱 코드(`app.py`, `model.py`, `train.py`, `make_shortcut.py`)는 수정하지 않고 이동만 한다.
- 앱 ID `DSMP.HandwritingDigitRecognizer` 는 그대로 유지한다.
- 새 가상환경은 `desktop_version/.venv`, 패키지 버전: `torch==2.14.0` `torchvision==0.29.0` (CPU 인덱스), `pillow==12.3.0`, `numpy==2.5.2`.

## Review Focus

1. **한 번 톡 찍은 작은 점** (글씨 영역이 20px보다 작음) → Lanczos가 축소가 아니라 확대 경로(필터배율 1)를 타도 파이썬과 같은 결과가 나와야 한다. → Task 2 합성 사례 `작은점`, Task 4 검사.
2. **그림판 가장자리에 걸친 납작한 가로획** → 잘린 높이가 `max(1, 반올림)` 으로 1px이 되고, 필터가 이미지 경계에서 잘려도 결과가 같아야 한다. → Task 2 합성 사례 `아래 가장자리 가로선`, Task 4 검사.
3. **`index.html` 을 더블클릭(`file://`)으로 열기** → 서버 없이도 가중치를 읽고 인식해야 한다. → Task 5 Step 6.
4. **휴대폰 폭(375px)에서 CSS로 축소된 캔버스, 두 손가락 터치** → 손가락 위치와 그려지는 위치가 어긋나지 않아야 하고, 두 번째 포인터는 무시해야 한다. → Task 5 Step 5 (좌표 환산 확인), app.js 의 `활성포인터` 처리.
5. **`weights.js` 가 없거나 손상됨** → 빈 화면이나 콘솔 오류만 남지 않고, 안내 문구가 보이며 그림판·버튼이 비활성화되어야 한다. → Task 5 Step 7.

---

## 파일 구조

| 경로 | 작업 | 책임 |
|---|---|---|
| `desktop_version/app.py` `model.py` `train.py` `make_shortcut.py` `app.ico` `mnist_cnn.pt` `data/` `README.md` | 이동 (Task 1) | 기존 데스크톱 앱 |
| `desktop_version/.venv/` | 생성 (Task 1) | 데스크톱 전용 가상환경 |
| `desktop_version/CLAUDE.md` | 생성 (Task 1), 수정 (Task 2) | 데스크톱 작업 안내 |
| `desktop_version/README.md` | 수정 (Task 1, 2) | 경로 안내·가중치 내보내기 절 |
| `desktop_version/export_web_weights.py` | 생성 (Task 2) | 가중치·기준값을 웹용 JS로 내보내기 |
| `web_version/weights.js` | 생성됨 (Task 2 실행 결과) | base64 float32 가중치 |
| `web_version/tests/reference.js` | 생성됨 (Task 2 실행 결과) | PyTorch·파이썬 기준값 |
| `web_version/tests/test.html` `tests/tests.js` | 생성 (Task 3), 수정 (Task 4) | 브라우저 테스트 페이지 |
| `web_version/js/model.js` | 생성 (Task 3) | CNN 추론 엔진 (DOM 없음) |
| `web_version/js/preprocess.js` | 생성 (Task 4) | MNIST 형식 전처리 (DOM 없음) |
| `web_version/index.html` `style.css` `js/app.js` | 생성 (Task 5) | 그림판 화면 |
| `.claude/launch.json` | 생성 (Task 3) | 로컬 확인용 정적 서버 설정 |
| `web_version/CLAUDE.md` `web_version/README.md` | 생성 (Task 6) | 웹 작업 안내·사용법 |
| `CLAUDE.md` `README.md` (루트) | 다시 작성 (Task 6) | 전체 개요·공유 계약 |

---

### Task 1: 데스크톱 버전을 `desktop_version/` 으로 이동

**Files:**
- Move: `app.py model.py train.py make_shortcut.py app.ico mnist_cnn.pt README.md data/` → `desktop_version/`
- Create: `desktop_version/.venv/`, `desktop_version/CLAUDE.md`
- Modify: `desktop_version/README.md` (설치·실행 경로 안내)
- Delete: 루트 `.venv/`, 루트 `__pycache__/`

**Interfaces:**
- Consumes: 없음
- Produces: `desktop_version/.venv/Scripts/python` (이후 모든 파이썬 실행에 사용), `desktop_version/app.py` 의 `모델_불러오기()`, `MNIST형식으로_변환(그림: PIL.Image) -> torch.Tensor | None`, 상수 `평균`, `표준편차`, `붓두께`, `캔버스크기` (Task 2가 import)

- [ ] **Step 1: 실행 중인 손글씨 앱 창이 있으면 닫는다** (파일이 잠겨 이동이 실패하지 않도록).

- [ ] **Step 2: 새 가상환경 만들기**

```bash
mkdir -p desktop_version
python -m venv desktop_version/.venv
desktop_version/.venv/Scripts/python --version
```
Expected: `Python 3.13.14`

- [ ] **Step 3: 패키지 설치** (다운로드 때문에 몇 분 걸림, timeout 넉넉히)

```bash
desktop_version/.venv/Scripts/python -m pip install torch==2.14.0 torchvision==0.29.0 --index-url https://download.pytorch.org/whl/cpu
desktop_version/.venv/Scripts/python -m pip install pillow==12.3.0 numpy==2.5.2
desktop_version/.venv/Scripts/python -m pip list | grep -iE "torch|pillow|numpy"
```
Expected: `numpy 2.5.2`, `pillow 12.3.0`, `torch 2.14.0+cpu`, `torchvision 0.29.0+cpu`

- [ ] **Step 4: 실패하는 동작 확인 스크립트 실행** (아직 파일을 옮기지 않았으므로 실패해야 함)

```bash
desktop_version/.venv/Scripts/python - <<'EOF'
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "desktop_version")
import torch
from PIL import Image, ImageDraw
import app
모델 = app.모델_불러오기()
그림 = Image.new("L", (280, 280), 0)
ImageDraw.Draw(그림).line([140, 50, 140, 230], fill=255, width=18)
with torch.no_grad():
    예측 = 모델(app.MNIST형식으로_변환(그림)).argmax(1).item()
print("세로선 예측:", 예측)
assert 예측 == 1, "세로선을 1로 인식하지 못함"
print("데스크톱 동작 확인 통과")
EOF
```
Expected: `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 5: 파일 이동**

```bash
mv app.py model.py train.py make_shortcut.py app.ico mnist_cnn.pt README.md data desktop_version/
ls desktop_version
```
Expected: `README.md app.ico app.py data make_shortcut.py mnist_cnn.pt model.py train.py` (+ `.venv`)

- [ ] **Step 6: Step 4 스크립트를 다시 실행** → Expected: `세로선 예측: 1` 과 `데스크톱 동작 확인 통과`

- [ ] **Step 7: 창이 실제로 만들어지는지 확인** (1.5초 뒤 자동으로 닫힘)

```bash
desktop_version/.venv/Scripts/python - <<'EOF'
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "desktop_version")
import tkinter as tk
import app
app.윈도우_앱ID_설정()
루트 = tk.Tk()
app.손글씨앱(루트)
루트.after(1500, 루트.destroy)
루트.mainloop()
print("창 생성 확인 통과")
EOF
```
Expected: `창 생성 확인 통과`, 오류 없음

- [ ] **Step 8: 예전 가상환경과 캐시 삭제**

```bash
rm -rf .venv __pycache__ desktop_version/__pycache__
ls -a
```
Expected: 루트에 `.venv`, `__pycache__`, `*.py` 가 없고 `CLAUDE.md docs desktop_version` 만 남음 (`.claude` 는 아직 없음)

- [ ] **Step 9: 바탕 화면 바로가기 다시 만들기 및 대상 확인**

```bash
desktop_version/.venv/Scripts/python desktop_version/make_shortcut.py
```
Expected: `아이콘 생성: ...\desktop_version\app.ico`, `바로가기 생성: ...\손글씨 숫자 인식기.lnk`, `완료!`

PowerShell 도구로 확인:
```powershell
$lnk = Join-Path ([Environment]::GetFolderPath('Desktop')) '손글씨 숫자 인식기.lnk'; $s = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk); $s.TargetPath; $s.Arguments; $s.WorkingDirectory
```
Expected: `...\desktop_version\.venv\Scripts\pythonw.exe`, `"...\desktop_version\app.py"`, `...\desktop_version`

- [ ] **Step 10: `desktop_version/CLAUDE.md` 작성**

````markdown
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
````

- [ ] **Step 11: `desktop_version/README.md` 수정** — 설치 절 맨 앞과 사용 방법 절 맨 앞에 작업 폴더 안내 추가.

`## 설치` 바로 아래(첫 문단 "Python 3.10 이상이 필요합니다..." 앞)에 추가:
```markdown
> 아래 명령은 모두 `desktop_version/` 폴더에서 실행합니다 (`cd desktop_version`).
```
`## 사용 방법` 바로 아래에 같은 문장 추가.

- [ ] **Step 12: 검증 요약** — Step 6, 7, 9의 기대 출력이 모두 나왔는지 확인한다.

---

### Task 2: 가중치·기준값 내보내기 스크립트

**Files:**
- Create: `desktop_version/export_web_weights.py`
- Generated: `web_version/weights.js`, `web_version/tests/reference.js`
- Modify: `desktop_version/CLAUDE.md`, `desktop_version/README.md`

**Interfaces:**
- Consumes: `app.모델_불러오기()`, `app.MNIST형식으로_변환()`, `app.평균`, `app.표준편차`, `app.붓두께`, `app.캔버스크기`
- Produces (JS 전역 상수, Task 3·4·5가 사용):
  - `가중치데이터 = { 목록: [{이름: string, 형태: number[], 시작: number, 개수: number}], base64: string }` — `시작`·`개수` 는 float 단위, 16개 층 (`num_batches_tracked` 제외). 층 이름: `합성곱1.weight`, `합성곱1.bias`, `정규화1.weight`, `정규화1.bias`, `정규화1.running_mean`, `정규화1.running_var`, 같은 식으로 `합성곱2.*`, `정규화2.*`, `완전연결1.weight`, `완전연결1.bias`, `완전연결2.weight`, `완전연결2.bias`.
  - `기준데이터 = { 모델사례: [{이름, 정답, 입력: base64<f32 784>, 로짓: number[10]}] (20개), 전처리사례: [{이름, 가로, 세로, 원본: base64<u8 가로*세로>, 결과: base64<f32 784>, 로짓: number[10]}] (5개) }`

- [ ] **Step 1: 실패 확인용 검증 스크립트 실행** (아직 출력 파일이 없으므로 실패해야 함)

```bash
desktop_version/.venv/Scripts/python - <<'EOF'
import sys, os, re, json, base64
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "desktop_version")
import numpy as np
import app
내용 = open("web_version/weights.js", encoding="utf-8").read()
목록 = json.loads(re.search(r"목록: (\[.*?\]),\n", 내용).group(1))
전체 = np.frombuffer(base64.b64decode(re.search(r'base64: "([^"]+)"', 내용).group(1)), dtype="<f4")
상태 = app.모델_불러오기().state_dict()
assert len(목록) == 16, len(목록)
for 항목 in 목록:
    기대 = 상태[항목["이름"]].numpy().ravel()
    실제 = 전체[항목["시작"]:항목["시작"] + 항목["개수"]]
    assert list(상태[항목["이름"]].shape) == 항목["형태"], 항목["이름"]
    assert np.array_equal(기대, 실제), 항목["이름"]
assert 항목["시작"] + 항목["개수"] == 전체.size
기준 = open("web_version/tests/reference.js", encoding="utf-8").read()
기준 = json.loads(기준[기준.index("{"):기준.rindex("}") + 1])
assert len(기준["모델사례"]) == 20 and len(기준["전처리사례"]) == 5
for 사례 in 기준["전처리사례"]:
    assert len(base64.b64decode(사례["원본"])) == 사례["가로"] * 사례["세로"]
    assert len(base64.b64decode(사례["결과"])) == 784 * 4
    print(사례["이름"], "→ 파이썬 예측", int(np.argmax(사례["로짓"])))
print("내보내기 검증 통과")
EOF
```
Expected: `FileNotFoundError: ... 'web_version/weights.js'`

- [ ] **Step 2: `desktop_version/export_web_weights.py` 작성**

```python
# -*- coding: utf-8 -*-
"""
학습된 가중치(mnist_cnn.pt)를 웹 버전에서 쓸 수 있도록 자바스크립트 파일로 내보내는 코드.

- ../web_version/weights.js         : 모든 가중치를 float32 로 이어 붙여 base64 로 담은 파일
- ../web_version/tests/reference.js : 웹 버전 테스트가 비교할 PyTorch·파이썬 계산 결과
모델을 다시 학습했거나 전처리를 바꿨다면 이 파일을 다시 실행해야 웹 버전에도 반영됨.
"""

import base64
import json
import math
import os
import sys

import numpy as np
import torch
from PIL import Image, ImageDraw
from torchvision import datasets, transforms

from app import MNIST형식으로_변환, 모델_불러오기, 붓두께, 캔버스크기, 평균, 표준편차

# 윈도우 콘솔에서도 한글이 깨지지 않도록 출력 인코딩을 UTF-8로 설정
sys.stdout.reconfigure(encoding="utf-8")

# ===== 경로 설정 (이 파일이 있는 폴더 기준) =====
프로젝트폴더 = os.path.dirname(os.path.abspath(__file__))
데이터폴더 = os.path.join(프로젝트폴더, "data")
웹폴더 = os.path.normpath(os.path.join(프로젝트폴더, "..", "web_version"))
가중치JS = os.path.join(웹폴더, "weights.js")
기준JS = os.path.join(웹폴더, "tests", "reference.js")
모델사례수 = 20  # 기준값으로 쓸 MNIST 시험 데이터 개수
생성안내 = "// 자동 생성 파일 — 직접 수정하지 마세요 (desktop_version/export_web_weights.py 로 다시 만듦)\n"


def base64로(배열, 자료형: str) -> str:
    """배열을 리틀엔디언 바이트로 바꾼 뒤 base64 문자열로 변환"""
    return base64.b64encode(np.ascontiguousarray(배열, dtype=자료형).tobytes()).decode("ascii")


def 파일_쓰기(경로: str, 내용: str):
    """UTF-8, 줄바꿈 LF 로 파일을 저장하고 크기를 출력"""
    os.makedirs(os.path.dirname(경로), exist_ok=True)
    with open(경로, "w", encoding="utf-8", newline="\n") as 파일:
        파일.write(내용)
    print(f"생성: {경로} ({os.path.getsize(경로) / 1024:,.0f}KB)")


def 가중치_내보내기(상태: dict):
    """state_dict 의 모든 텐서를 하나의 float32 배열로 이어 붙여 weights.js 로 저장"""
    목록, 조각들, 시작 = [], [], 0
    for 이름, 텐서 in 상태.items():
        if 이름.endswith("num_batches_tracked"):
            continue  # 학습 때만 쓰는 카운터라 추론에는 필요 없음
        값 = 텐서.detach().cpu().numpy().astype("<f4").ravel()
        목록.append({"이름": 이름, "형태": list(텐서.shape), "시작": 시작, "개수": int(값.size)})
        조각들.append(값)
        시작 += 값.size
    내용 = (
        생성안내
        + "const 가중치데이터 = {\n"
        + f"  목록: {json.dumps(목록, ensure_ascii=False)},\n"
        + f'  base64: "{base64로(np.concatenate(조각들), "<f4")}",\n'
        + "};\n"
    )
    파일_쓰기(가중치JS, 내용)
    print(f"  가중치 {시작:,}개, 층 {len(목록)}개")


def 선_그리기(붓: ImageDraw.ImageDraw, 점들, 두께: int = 붓두께):
    """app.py 의 그리기() 와 같은 방식(선 + 점마다 원)으로 흰 선을 그림"""
    r = 두께 // 2
    for i, (x, y) in enumerate(점들):
        if i > 0:
            붓.line([*점들[i - 1], x, y], fill=255, width=두께)
        붓.ellipse([x - r, y - r, x + r, y + r], fill=255)


def 합성_이미지들():
    """전처리 비교용으로 그림판에 그린 것 같은 손글씨 이미지 (이름, PIL 이미지) 목록"""
    영점들 = [(round(140 + 55 * math.sin(2 * math.pi * i / 36)),
              round(140 - 85 * math.cos(2 * math.pi * i / 36))) for i in range(37)]
    사례 = [
        ("세로선(1)", [(140, 50), (140, 230)], 붓두께),
        ("칠(7)", [(70, 60), (210, 60), (120, 230)], 붓두께),
        ("영(0)", 영점들, 붓두께),
        ("작은점", [(200, 90)], 6),                      # 20px 보다 작아서 확대 경로를 탐
        ("아래 가장자리 가로선", [(20, 275), (260, 275)], 붓두께),  # 경계에 걸리고 높이가 1px 로 줄어듦
    ]
    결과 = []
    for 이름, 점들, 두께 in 사례:
        그림 = Image.new("L", (캔버스크기, 캔버스크기), 0)
        선_그리기(ImageDraw.Draw(그림), 점들, 두께)
        결과.append((이름, 그림))
    return 결과


@torch.no_grad()
def 기준값_내보내기(모델):
    """웹 테스트가 비교할 PyTorch 로짓과 파이썬 전처리 결과를 reference.js 로 저장"""
    시험데이터 = datasets.MNIST(데이터폴더, train=False, download=True, transform=transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((평균,), (표준편차,)),
    ]))
    모델사례 = []
    for i in range(모델사례수):
        입력, 정답 = 시험데이터[i]
        로짓 = 모델(입력.unsqueeze(0))[0]
        모델사례.append({"이름": f"시험데이터 {i}번", "정답": int(정답),
                     "입력": base64로(입력.numpy(), "<f4"), "로짓": [float(v) for v in 로짓]})

    전처리사례 = []
    for 이름, 그림 in 합성_이미지들():
        결과 = MNIST형식으로_변환(그림)  # 모양: (1, 1, 28, 28)
        로짓 = 모델(결과)[0]
        전처리사례.append({"이름": 이름, "가로": 그림.width, "세로": 그림.height,
                      "원본": base64로(np.asarray(그림), "u1"),
                      "결과": base64로(결과.numpy(), "<f4"),
                      "로짓": [float(v) for v in 로짓]})
        print(f"  전처리 사례 '{이름}' → 파이썬 예측 {int(로짓.argmax())}")

    데이터 = {"모델사례": 모델사례, "전처리사례": 전처리사례}
    파일_쓰기(기준JS, 생성안내 + "const 기준데이터 = " + json.dumps(데이터, ensure_ascii=False) + ";\n")


if __name__ == "__main__":
    모델 = 모델_불러오기()
    가중치_내보내기(모델.state_dict())
    기준값_내보내기(모델)
    print("완료! web_version 의 weights.js 와 tests/reference.js 를 새로 만들었습니다.")
```

- [ ] **Step 3: 스크립트 실행**

```bash
desktop_version/.venv/Scripts/python desktop_version/export_web_weights.py
```
Expected: `weights.js` 약 2,200KB, 층 16개, 가중치 422,026개, 전처리 사례 5개의 파이썬 예측 출력 (세로선은 1, 칠은 7, 영은 0으로 예측되는 것이 자연스러움 — 다르면 기록만 하고 진행, 테스트는 파이썬과 JS의 일치를 본다), `reference.js` 생성, `완료!`

- [ ] **Step 4: Step 1 검증 스크립트 다시 실행** → Expected: 사례별 예측 5줄과 `내보내기 검증 통과`

- [ ] **Step 5: `desktop_version/CLAUDE.md` 수정**

명령어 코드 블록의 `make_shortcut.py` 줄 아래에 추가:
```
.venv/Scripts/python export_web_weights.py  # ../web_version/weights.js 와 tests/reference.js 생성
```
`## 구조` 절 맨 끝에 추가:
```markdown
- **웹 버전으로 가중치 내보내기 (`export_web_weights.py`):**
  - `mnist_cnn.pt` 의 텐서를 float32 리틀엔디언으로 이어 붙여 base64로 담은 `../web_version/weights.js` 를 만듭니다 (`num_batches_tracked` 제외). 웹 버전은 이 파일의 층 이름(`합성곱1.weight` 등)으로 가중치를 찾으므로 `model.py` 의 속성 이름을 바꾸면 웹 코드도 함께 고쳐야 합니다.
  - 웹 테스트용 기준값 `../web_version/tests/reference.js` 도 함께 만듭니다: MNIST 시험 데이터 20장의 PyTorch 로짓과, 합성 손글씨 5장에 대한 `app.py` 의 `MNIST형식으로_변환()` 결과·로짓.
  - **모델을 다시 학습했거나 `app.py` 의 전처리를 바꿨다면 반드시 다시 실행합니다.** 두 출력 파일은 생성 파일이므로 직접 수정하지 않습니다.
```

- [ ] **Step 6: `desktop_version/README.md` 수정**

파일 구성 표의 `make_shortcut.py` 행 아래에 추가:
```markdown
| `export_web_weights.py` | 가중치를 웹 버전용 `../web_version/weights.js` 로 내보내는 코드 |
```
`### 3. 바탕 화면 바로가기 만들기 (윈도우)` 절 끝(다음 `## 모델 구조` 앞)에 추가:
````markdown
### 4. 웹 버전으로 가중치 내보내기

```bash
.venv/Scripts/python export_web_weights.py
```

- 학습된 가중치를 `../web_version/weights.js` 로, 웹 버전 테스트용 기준값을 `../web_version/tests/reference.js` 로 저장합니다.
- 모델을 다시 학습했다면 이 명령도 다시 실행해야 웹 버전에 반영됩니다.
````

---

### Task 3: 테스트 페이지 + JS 추론 엔진 (`js/model.js`)

**Files:**
- Create: `web_version/tests/test.html`, `web_version/tests/tests.js`, `web_version/js/model.js`, `.claude/launch.json`

**Interfaces:**
- Consumes: `가중치데이터`, `기준데이터` (Task 2)
- Produces (전역 함수, Task 4·5가 사용):
  - `base64를_바이트로(문자열: string) -> Uint8Array`
  - `base64를_실수배열로(문자열: string) -> Float32Array`
  - `가중치_해독(데이터) -> { [층이름]: { 형태: number[], 값: Float32Array } }` — 길이가 모자라면 `Error` 를 던짐
  - `숫자인식CNN_로짓(입력: ArrayLike<number> 길이 784, 가중치) -> Float64Array(10)`
  - `숫자인식CNN_추론(입력, 가중치) -> number[10]` (확률, 합 1)
  - `가장_큰_위치(배열) -> number`
  - 테스트 도구 (tests.js 전역): `검사(이름, 함수)`, `확인(조건, 메시지)`, `최대오차(가, 나)`, `테스트용_가중치()`

- [ ] **Step 1: 로컬 정적 서버 설정 `.claude/launch.json` 작성**

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "web",
      "runtimeExecutable": "python",
      "runtimeArgs": ["-m", "http.server", "8765", "--directory", "web_version"],
      "port": 8765
    }
  ]
}
```

- [ ] **Step 2: `web_version/tests/test.html` 작성**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>웹 버전 테스트</title>
<style>
  body { font-family: "맑은 고딕", "Malgun Gothic", system-ui, sans-serif; margin: 16px; color: #202124; }
  #요약 { font-size: 1.2rem; font-weight: bold; margin-bottom: 12px; }
  table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
  td, th { border: 1px solid #dadce0; padding: 4px 8px; text-align: left; vertical-align: top; }
  .통과 { color: #188038; }
  .실패 { color: #d93025; }
</style>
</head>
<body>
<h1>손글씨 인식 웹 버전 테스트</h1>
<div id="요약">실행 중...</div>
<table>
  <thead><tr><th>결과</th><th>검사</th><th>내용</th></tr></thead>
  <tbody id="결과표"></tbody>
</table>
<!-- 순서 중요: 데이터 → 계산 코드 → 검사 코드 -->
<script src="../weights.js"></script>
<script src="reference.js"></script>
<script src="../js/model.js"></script>
<script src="../js/preprocess.js"></script>
<script src="tests.js"></script>
</body>
</html>
```

- [ ] **Step 3: `web_version/tests/tests.js` 작성 (모델 검사까지)**

```js
// 웹 버전 테스트: PyTorch·파이썬이 계산한 기준값(reference.js)과 자바스크립트 계산 결과를 비교함.
// 외부 라이브러리 없이 검사(이름, 함수) 로 등록하고, 함수가 예외를 던지면 실패로 표시함.

const 테스트목록 = [];

/** 검사 하나를 등록 */
function 검사(이름, 함수) {
  테스트목록.push({ 이름, 함수 });
}

/** 조건이 거짓이면 메시지와 함께 실패시킴 */
function 확인(조건, 메시지) {
  if (!조건) throw new Error(메시지);
}

/** 두 배열의 원소별 절대 오차 중 가장 큰 값 */
function 최대오차(가, 나) {
  확인(가.length === 나.length, `길이가 다름: ${가.length} / ${나.length}`);
  let 최대 = 0;
  for (let i = 0; i < 가.length; i++) 최대 = Math.max(최대, Math.abs(가[i] - 나[i]));
  return 최대;
}

let 테스트가중치 = null;
/** 가중치는 한 번만 해독해서 여러 검사가 같이 씀 */
function 테스트용_가중치() {
  if (테스트가중치 === null) 테스트가중치 = 가중치_해독(가중치데이터);
  return 테스트가중치;
}

function 모델_검사_등록() {
  검사("가중치 해독: 층 16개, 층별 형태·개수, 전체 길이", () => {
    const 가중치 = 테스트용_가중치();
    확인(가중치데이터.목록.length === 16, `층 개수 ${가중치데이터.목록.length}`);
    let 합계 = 0;
    for (const 항목 of 가중치데이터.목록) {
      const 층 = 가중치[항목.이름];
      확인(층 !== undefined, `${항목.이름} 없음`);
      const 형태곱 = 항목.형태.reduce((곱, 값) => 곱 * 값, 1);
      확인(층.값.length === 항목.개수 && 형태곱 === 항목.개수, `${항목.이름} 개수 불일치`);
      합계 += 항목.개수;
    }
    확인(합계 * 4 === base64를_바이트로(가중치데이터.base64).length, "전체 바이트 길이 불일치");
  });

  검사("가중치 해독: 손상된 데이터는 오류", () => {
    const 손상 = { 목록: 가중치데이터.목록, base64: "AAAAAA==" };
    let 오류 = null;
    try { 가중치_해독(손상); } catch (e) { 오류 = e; }
    확인(오류 !== null, "오류가 나지 않음");
  });

  검사("소프트맥스: 합이 1, 가장 큰 로짓이 가장 큰 확률", () => {
    const 확률 = 숫자인식CNN_추론(base64를_실수배열로(기준데이터.모델사례[0].입력), 테스트용_가중치());
    const 합 = 확률.reduce((a, b) => a + b, 0);
    확인(확률.length === 10 && Math.abs(합 - 1) < 1e-9, `합 ${합}`);
    확인(가장_큰_위치(확률) === 가장_큰_위치(기준데이터.모델사례[0].로짓), "최댓값 위치 불일치");
  });

  for (const 사례 of 기준데이터.모델사례) {
    검사(`모델 추론: ${사례.이름} (정답 ${사례.정답})`, () => {
      const 로짓 = 숫자인식CNN_로짓(base64를_실수배열로(사례.입력), 테스트용_가중치());
      const 오차 = 최대오차(로짓, 사례.로짓);
      확인(오차 < 1e-4, `로짓 최대 오차 ${오차.toExponential(2)}`);
      확인(가장_큰_위치(로짓) === 가장_큰_위치(사례.로짓), "예측 숫자 불일치");
      return `최대 오차 ${오차.toExponential(2)}`;
    });
  }
}

/** 등록된 검사를 모두 실행하고 표로 출력. 자동 확인용으로 window.테스트결과 에 요약을 남김 */
function 테스트_실행() {
  const 결과 = { 통과: 0, 전체: 테스트목록.length, 실패목록: [] };
  const 표 = document.getElementById("결과표");
  for (const { 이름, 함수 } of 테스트목록) {
    let 내용 = "";
    let 성공 = true;
    try {
      내용 = 함수() || "";
    } catch (오류) {
      성공 = false;
      내용 = 오류.message;
      결과.실패목록.push(`${이름}: ${오류.message}`);
    }
    if (성공) 결과.통과++;
    const 줄 = 표.insertRow();
    줄.insertCell().textContent = 성공 ? "통과" : "실패";
    줄.cells[0].className = 성공 ? "통과" : "실패";
    줄.insertCell().textContent = 이름;
    줄.insertCell().textContent = 내용;
  }
  const 요약 = document.getElementById("요약");
  요약.textContent = `통과 ${결과.통과} / 전체 ${결과.전체}`;
  요약.className = 결과.통과 === 결과.전체 ? "통과" : "실패";
  window.테스트결과 = 결과;
}

// ===== 검사 등록 =====
if (typeof 가중치데이터 === "undefined" || typeof 기준데이터 === "undefined") {
  검사("기준 데이터 불러오기", () => {
    throw new Error("weights.js 또는 tests/reference.js 가 없습니다. desktop_version 에서 export_web_weights.py 를 실행하세요.");
  });
} else {
  모델_검사_등록();
}

window.addEventListener("load", 테스트_실행);
```

- [ ] **Step 4: 테스트가 실패하는지 확인**

`preview_start` 로 `web` 서버를 시작하고 `http://localhost:8765/tests/test.html` 로 이동한 뒤, `javascript_tool` 로 확인:
```js
window.테스트결과
```
Expected: `{통과: 0, 전체: 23, 실패목록: [... "가장_큰_위치 is not defined" / "가중치_해독 is not defined" ...]}` (model.js 가 없으므로 전부 실패)

- [ ] **Step 5: `web_version/js/model.js` 작성**

```js
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
```

- [ ] **Step 6: 테스트 페이지 새로고침 후 확인**

`javascript_tool`: `location.reload()` 후 `window.테스트결과`
Expected: `{통과: 23, 전체: 23, 실패목록: []}`. 실패하면 superpowers:systematic-debugging 으로 원인을 찾는다 (가장 흔한 원인: 층 이름 오타, 합성곱 인덱스, 배치정규화 순서).

---

### Task 4: 전처리 (`js/preprocess.js`)

**Files:**
- Create: `web_version/js/preprocess.js`
- Modify: `web_version/tests/tests.js` (전처리 검사 함수 추가 및 등록)

**Interfaces:**
- Consumes: `base64를_바이트로`, `base64를_실수배열로`, `숫자인식CNN_로짓`, `가장_큰_위치` (Task 3), `기준데이터.전처리사례` (Task 2)
- Produces (전역, Task 5가 사용):
  - `MNIST평균 = 0.1307`, `MNIST표준편차 = 0.3081`
  - `파이썬식_반올림(x: number) -> number`
  - `MNIST형식으로_변환(흑백픽셀: Uint8Array | Uint8ClampedArray (길이 가로*세로, 0~255), 가로: number, 세로: number) -> Float32Array(784) | null`

- [ ] **Step 1: `tests.js` 에 전처리 검사 추가**

`function 모델_검사_등록() { ... }` 정의 바로 아래에 추가:

```js
function 전처리_검사_등록() {
  검사("파이썬식 반올림 (은행가 반올림)", () => {
    const 사례 = [[0.5, 0], [1.5, 2], [2.5, 2], [3.5, 4], [-0.5, 0], [-1.5, -2],
      [2.4, 2], [2.6, 3], [-2.6, -3], [7, 7]];
    for (const [입력, 기대] of 사례) {
      const 실제 = 파이썬식_반올림(입력);
      확인(실제 === 기대, `round(${입력}) = ${실제}, 기대 ${기대}`);
    }
  });

  검사("빈 그림은 null", () => {
    확인(MNIST형식으로_변환(new Uint8Array(280 * 280), 280, 280) === null, "null 이 아님");
  });

  for (const 사례 of 기준데이터.전처리사례) {
    검사(`전처리: ${사례.이름}`, () => {
      const 결과 = MNIST형식으로_변환(base64를_바이트로(사례.원본), 사례.가로, 사례.세로);
      확인(결과 !== null && 결과.length === 784, "결과가 784 길이 배열이 아님");
      // 정규화된 값의 차이를 0~255 픽셀 단위로 되돌려 비교
      const 픽셀오차 = 최대오차(결과, base64를_실수배열로(사례.결과)) * MNIST표준편차 * 255;
      확인(픽셀오차 <= 3, `픽셀 최대 오차 ${픽셀오차.toFixed(2)} (허용 3)`);
      const 파이썬예측 = 가장_큰_위치(사례.로짓);
      const 예측 = 가장_큰_위치(숫자인식CNN_로짓(결과, 테스트용_가중치()));
      확인(예측 === 파이썬예측, `예측 ${예측}, 파이썬 ${파이썬예측}`);
      return `픽셀 최대 오차 ${픽셀오차.toFixed(2)}, 예측 ${예측}`;
    });
  }
}
```

`// ===== 검사 등록 =====` 의 `else` 블록을 다음으로 바꾼다:
```js
} else {
  모델_검사_등록();
  전처리_검사_등록();
}
```

- [ ] **Step 2: 테스트가 실패하는지 확인** — `location.reload()` 후 `window.테스트결과`
Expected: `전체: 30`, `통과: 23`, 실패 7개 (`파이썬식_반올림 is not defined`, `MNIST형식으로_변환 is not defined`)

- [ ] **Step 3: `web_version/js/preprocess.js` 작성**

```js
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
```

- [ ] **Step 4: 테스트 통과 확인** — `location.reload()` 후 `window.테스트결과`
Expected: `{통과: 30, 전체: 30, 실패목록: []}`. 결과표에서 전처리 사례별 `픽셀 최대 오차` 가 보통 0~1 이어야 한다. 오차가 크면(특히 전체가 한 칸 밀린 모양) superpowers:systematic-debugging 으로 단계별(자르기 크기 → 축소 크기 → 여백 → 이동량) 파이썬 중간값과 비교한다.

---

### Task 5: 그림판 화면 (`index.html`, `style.css`, `js/app.js`)

**Files:**
- Create: `web_version/index.html`, `web_version/style.css`, `web_version/js/app.js`

**Interfaces:**
- Consumes: `가중치데이터`, `가중치_해독`, `숫자인식CNN_추론`, `가장_큰_위치` (Task 2·3), `MNIST형식으로_변환` (Task 4)
- Produces: 완성된 웹 앱 (다른 작업이 소비하지 않음)

- [ ] **Step 1: `web_version/index.html` 작성**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>손글씨 숫자 인식기</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<main class="앱">
  <h1>손글씨 숫자 인식기</h1>
  <p class="설명">PyTorch로 학습한 CNN을 순수 자바스크립트로 실행합니다. 모든 계산은 이 브라우저 안에서 이루어집니다.</p>
  <div id="오류안내" class="오류" hidden></div>
  <div class="본문">
    <section class="그림판영역">
      <p class="제목">여기에 숫자(0~9)를 그려 주세요</p>
      <canvas id="그림판" width="280" height="280"></canvas>
      <div class="버튼줄">
        <button id="인식버튼" type="button" class="주버튼">인식하기</button>
        <button id="지우기버튼" type="button">지우기</button>
      </div>
    </section>
    <section class="결과영역">
      <p class="제목">인식 결과</p>
      <div id="결과숫자" class="결과숫자">?</div>
      <div id="확신도" class="확신도"></div>
      <ol id="막대목록" class="막대목록"></ol>
    </section>
  </div>
  <p class="도움말">손을 떼면 자동으로 인식합니다 · Enter: 다시 인식 · Esc / Delete: 지우기</p>
</main>
<!-- 순서 중요: 가중치 → 추론 엔진 → 전처리 → 화면 (ES 모듈은 file:// 에서 막히므로 일반 스크립트 사용) -->
<script src="weights.js"></script>
<script src="js/model.js"></script>
<script src="js/preprocess.js"></script>
<script src="js/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: `web_version/style.css` 작성**

```css
* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: "맑은 고딕", "Malgun Gothic", system-ui, sans-serif;
  background: #f5f6f8;
  color: #202124;
}

.앱 { max-width: 640px; margin: 0 auto; padding: 16px; }
h1 { font-size: 1.4rem; margin: 8px 0 4px; }
.설명, .도움말 { color: #5f6368; font-size: 0.9rem; margin: 0 0 12px; }
.도움말 { margin-top: 12px; }
.제목 { margin: 0 0 8px; }

.본문 { display: flex; gap: 16px; align-items: flex-start; }
.그림판영역, .결과영역 {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}
.그림판영역 { flex: 0 0 auto; }
.결과영역 { flex: 1 1 auto; min-width: 0; text-align: center; }

#그림판 {
  display: block;
  width: 280px;
  max-width: 100%;
  height: auto;
  aspect-ratio: 1;
  background: #000;
  border-radius: 4px;
  cursor: crosshair;
  touch-action: none;  /* 휴대폰에서 그릴 때 화면이 스크롤되지 않도록 */
}
#그림판.비활성 { opacity: 0.4; cursor: not-allowed; }

.버튼줄 { display: flex; gap: 8px; margin-top: 10px; }
.버튼줄 button {
  flex: 1;
  padding: 10px;
  font: inherit;
  border: 1px solid #dadce0;
  border-radius: 8px;
  background: #fff;
  color: #202124;
  cursor: pointer;
}
.버튼줄 .주버튼 { background: #1a73e8; border-color: #1a73e8; color: #fff; font-weight: bold; }
.버튼줄 button:disabled { opacity: 0.5; cursor: not-allowed; }

.결과숫자 { font-size: 72px; font-weight: bold; color: #1a73e8; line-height: 1.1; }
.확신도 { min-height: 1.4em; font-size: 0.95rem; }

.막대목록 { list-style: none; padding: 0; margin: 12px 0 0; }
.막대줄 {
  display: grid;
  grid-template-columns: 1.5em 1fr 4.5em;
  align-items: center;
  gap: 6px;
  margin: 3px 0;
  font-size: 0.85rem;
}
.막대배경 { height: 14px; background: #eee; border-radius: 3px; overflow: hidden; }
.막대 { height: 100%; width: 0; background: #9aa0a6; }
.막대.최대 { background: #1a73e8; }
.막대값 { text-align: right; font-variant-numeric: tabular-nums; }

.오류 { background: #fce8e6; color: #a50e0e; padding: 12px; border-radius: 8px; margin-bottom: 12px; }

/* 좁은 화면(휴대폰): 그림판 위, 결과 아래로 세로 배치 */
@media (max-width: 600px) {
  .본문 { flex-direction: column; align-items: stretch; }
  .그림판영역 { align-self: center; width: 100%; max-width: 312px; }
  #그림판 { width: 100%; }
}
```

- [ ] **Step 3: `web_version/js/app.js` 작성**

```js
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

/** 캔버스 픽셀을 읽어 흑백 배열(0~255)로 만듦 — 흰 글씨이므로 빨강 채널 값만 쓰면 됨 */
function 흑백_픽셀_읽기() {
  const 데이터 = 붓.getImageData(0, 0, 캔버스크기, 캔버스크기).data;
  const 흑백 = new Uint8Array(캔버스크기 * 캔버스크기);
  for (let i = 0; i < 흑백.length; i++) 흑백[i] = 데이터[i * 4];
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
  if (앱가중치 === null || 활성포인터 !== null) return;
  이벤트.preventDefault();
  활성포인터 = 이벤트.pointerId;
  그림판.setPointerCapture(이벤트.pointerId);  // 그림판 밖으로 나가도 계속 이벤트를 받음
  이전좌표 = 그림판_좌표(이벤트);
  점_찍기(이전좌표);
}

function 붓_움직임(이벤트) {
  if (이벤트.pointerId !== 활성포인터) return;
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
  그림판.addEventListener("pointerup", 붓_떼기);
  그림판.addEventListener("pointercancel", 붓_떼기);
  인식버튼.addEventListener("click", 인식하기);
  지우기버튼.addEventListener("click", 지우기);
  // 키보드 단축키: Enter = 다시 인식, Esc / Delete = 지우기 (버튼에 초점이 있을 때 Enter 가 두 번 처리되지 않도록 버튼은 제외)
  document.addEventListener("keydown", (이벤트) => {
    if (이벤트.target instanceof HTMLButtonElement) return;
    if (이벤트.key === "Enter") 인식하기();
    else if (이벤트.key === "Escape" || 이벤트.key === "Delete") 지우기();
  });
}

시작하기();
```

- [ ] **Step 4: 넓은 화면에서 동작 확인** — `http://localhost:8765/index.html` 로 이동, `read_console_messages` (onlyErrors) 로 오류 없음 확인, `computer` 의 `left_click_drag` 로 그림판 안에 세로선(위→아래)을 그린 뒤 스크린샷.
Expected: 콘솔 오류 없음, 결과 숫자 `1` (또는 세로선에 가까운 숫자), 확신도·막대 표시. `javascript_tool` 로 한 번 더 확인:
```js
[document.getElementById("결과숫자").textContent, document.getElementById("확신도").textContent]
```
이어서 `Escape` 키 → 결과가 `?` 로 돌아오는지, 빈 상태에서 `인식하기` 클릭 → `먼저 숫자를 그려 주세요` 가 나오는지 확인.

- [ ] **Step 5: 휴대폰 폭(375px)에서 좌표 환산 확인** — `resize_window` preset `mobile`, 새로고침, 스크린샷으로 가로 스크롤 없이 그림판 위·결과 아래 배치 확인. 그림판 화면 영역의 정중앙을 짧게 드래그한 뒤:
```js
(() => { const 붓 = document.getElementById("그림판").getContext("2d");
  const 영역 = document.getElementById("그림판").getBoundingClientRect();
  return { 표시폭: 영역.width, 중앙픽셀: 붓.getImageData(140, 140, 1, 1).data[0],
           가로스크롤: document.documentElement.scrollWidth > innerWidth }; })()
```
Expected: `표시폭` 280 이하, `중앙픽셀` 255 (화면 중앙에 그은 선이 내부 좌표 중앙에 그려짐), `가로스크롤: false`. 끝나면 `resize_window` preset `desktop` 으로 되돌린다.

- [ ] **Step 6: `file://` 로 열기 확인** — `navigate` 로 `file:///C:/Users/user/DSMP/3장 손글씨 앱/study01_minist/web_version/index.html` 을 열어 Step 4와 같이 그려 인식되는지 확인 (내장 브라우저가 `file://` 을 막으면 그 사실을 기록하고, 사용자에게 탐색기에서 `index.html` 을 더블클릭해 확인해 달라고 요청). 같은 방식으로 `file:///.../web_version/tests/test.html` 의 `window.테스트결과` 도 `통과 30 / 전체 30` 인지 확인.

- [ ] **Step 7: 가중치 파일이 없을 때 확인**

```bash
mv web_version/weights.js web_version/weights.js.bak
```
`http://localhost:8765/index.html` 새로고침 → 빨간 안내 문구(`export_web_weights.py 를 실행해`)가 보이고 버튼이 비활성인지 확인:
```js
[document.getElementById("오류안내").hidden, document.getElementById("인식버튼").disabled]
```
Expected: `[false, true]`. 그다음 반드시 되돌린다:
```bash
mv web_version/weights.js.bak web_version/weights.js
```
새로고침 후 오류 안내가 사라지고 그리기가 되는지 확인.

---

### Task 6: 문서 (웹 CLAUDE.md·README, 루트 CLAUDE.md·README)

**Files:**
- Create: `web_version/CLAUDE.md`, `web_version/README.md`
- Rewrite: `CLAUDE.md`, `README.md` (루트)

**Interfaces:**
- Consumes: 앞 작업들의 파일 이름·함수 이름·명령어 (아래 문서에 그대로 사용)
- Produces: 없음

- [ ] **Step 1: `web_version/CLAUDE.md` 작성**

````markdown
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

`index.html`: `weights.js` → `js/model.js` → `js/preprocess.js` → `js/app.js`
`tests/test.html`: `../weights.js` → `reference.js` → `../js/model.js` → `../js/preprocess.js` → `tests.js`

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
- **`js/model.js` 는 `desktop_version/model.py` 의 `forward` 를 그대로 따라갑니다** (합성곱 → 배치정규화 → ReLU → 최대풀링 두 번 → 완전연결 → ReLU → 완전연결, 드롭아웃은 추론에서 생략). 가중치는 `model.py` 의 속성 이름(`합성곱1.weight` 등)으로 찾으므로 모델 구조나 속성 이름이 바뀌면 이 파일도 함께 고칩니다. 배치정규화 eps 는 PyTorch 기본값 `1e-5` 입니다.
- **`js/preprocess.js` 는 `desktop_version/app.py` 의 `MNIST형식으로_변환()` 과 같아야 합니다:** 글씨 영역 자르기 → 긴 변을 20px로 Lanczos 축소 → 28x28 가운데 배치 → 무게중심 보정 → 정규화(평균 0.1307, 표준편차 0.3081). 한쪽을 바꾸면 다른 쪽도 바꾸고 기준값을 다시 생성합니다.
  - 축소는 Pillow의 `LANCZOS` 와 같은 방식(가로 → 세로 분리 적용, 축소 시 필터 폭 확대, 매 단계 0~255 반올림)으로 직접 구현했습니다. Pillow 내부 정수 연산과 비트 단위로 같지는 않아서 테스트는 픽셀 오차 3 이하로 비교합니다.
  - 파이썬 `round()` 는 은행가 반올림(2.5 → 2)이므로 `Math.round` 대신 `파이썬식_반올림()` 을 씁니다.
- **그림판은 이미지를 한 벌만 씁니다.** 데스크톱과 달리 화면의 `<canvas>`(내부 280x280, 검은 배경·흰 선·붓 두께 18)를 `getImageData` 로 읽어 빨강 채널을 흑백 값으로 씁니다. CSS 로 표시 크기가 줄어드는 휴대폰에서는 `그림판_좌표()` 가 `getBoundingClientRect` 비율로 좌표를 환산합니다.

## 테스트와 확인

빌드·린트 도구는 없습니다. 브라우저 테스트 페이지로 JS 계산이 PyTorch·파이썬과 일치하는지 확인합니다.

```bash
python -m http.server 8765 --directory web_version   # 저장소 루트에서 실행 (.claude/launch.json 의 "web" 설정과 같음)
```

- `http://localhost:8765/tests/test.html` — 맨 위가 `통과 N / 전체 N` 이어야 합니다. 자동 확인은 페이지의 `window.테스트결과` (`{통과, 전체, 실패목록}`) 를 읽습니다.
- `http://localhost:8765/index.html` — 실제 앱. `index.html`·`tests/test.html` 은 `file://` 로 더블클릭해 열어도 동작해야 합니다.

## GitHub Pages 게시

이 폴더의 **내용**(폴더 자체가 아니라 안의 파일들)을 저장소 루트 또는 `/docs` 폴더에 올리고, 저장소 설정 → Pages 에서 해당 브랜치·폴더를 선택합니다. 빌드 과정이 없으므로 올린 파일이 그대로 서비스됩니다. `tests/` 폴더는 함께 올려도 되고 빼도 됩니다.
````

- [ ] **Step 2: `web_version/README.md` 작성**

````markdown
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
````

- [ ] **Step 3: 루트 `CLAUDE.md` 다시 작성**

````markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

MNIST 손글씨 숫자(0~9)를 CNN으로 인식하는 프로그램입니다. 두 버전으로 나뉘며, 각 폴더에 자세한 안내(`CLAUDE.md`)가 있습니다.

| 폴더 | 내용 |
|---|---|
| `desktop_version/` | PyTorch 학습(`train.py`) + 윈도우용 tkinter 그림판 앱(`app.py`) + 웹용 가중치 내보내기(`export_web_weights.py`). 전용 가상환경 `desktop_version/.venv` 사용 |
| `web_version/` | 외부 라이브러리 없이 순수 자바스크립트로 추론하는 정적 웹 앱. 폴더 내용을 그대로 GitHub Pages에 올림 |
| `docs/superpowers/` | 설계(specs)·구현 계획(plans) 문서 |

## 작성 규칙

- **모든 코드와 주석은 한글로 작성합니다.** 변수·함수·클래스 이름도 한글 식별자를 씁니다 (파이썬·자바스크립트·CSS 모두). 파일 이름은 영어로 둡니다.
- 콘솔에 한글을 출력하는 파이썬 스크립트는 맨 위에서 `sys.stdout.reconfigure(encoding="utf-8")` 를 호출합니다.

## 두 버전이 공유하는 계약

웹 버전은 데스크톱에서 학습한 가중치를 그대로 쓰므로, 아래 항목은 두 버전이 반드시 같아야 합니다.

- **모델 구조:** `desktop_version/model.py` 의 `숫자인식CNN` = `web_version/js/model.js` 의 `숫자인식CNN_로짓()`. 가중치는 `model.py` 의 속성 이름(`합성곱1.weight` 등)으로 연결됩니다.
- **정규화 값:** 평균 0.1307, 표준편차 0.3081 — `desktop_version/train.py`, `desktop_version/app.py`, `web_version/js/preprocess.js` 세 곳.
- **전처리 5단계:** 글씨 영역 자르기 → 긴 변 20px Lanczos 축소 → 28x28 가운데 배치 → 무게중심 보정(파이썬식 반올림) → 정규화 — `desktop_version/app.py` 의 `MNIST형식으로_변환()` 과 `web_version/js/preprocess.js` 의 같은 이름 함수.

## 변경 시 연결 관계

- 모델을 다시 학습하거나 `model.py`·데스크톱 전처리를 바꿨다면 → `desktop_version/` 에서 `.venv/Scripts/python export_web_weights.py` 를 실행해 `web_version/weights.js` 와 `web_version/tests/reference.js` 를 다시 만들고 → `web_version/tests/test.html` 이 모두 통과하는지 확인합니다.
- 두 생성 파일은 직접 수정하지 않습니다.
````

- [ ] **Step 4: 루트 `README.md` 작성**

````markdown
# 손글씨 숫자 인식기 (PyTorch + MNIST)

마우스나 손가락으로 숫자(0~9)를 그리면 합성곱 신경망(CNN)이 어떤 숫자인지 인식합니다. 같은 모델을 두 가지 형태로 제공합니다.

| 버전 | 설명 | 안내 |
|---|---|---|
| 데스크톱 | PyTorch로 MNIST를 학습하고 윈도우 tkinter 그림판 앱으로 실행 | [desktop_version/README.md](desktop_version/README.md) |
| 웹 | 학습된 가중치를 순수 자바스크립트로 실행하는 정적 웹 앱 (GitHub Pages 가능) | [web_version/README.md](web_version/README.md) |

## 흐름

```
desktop_version/train.py  →  mnist_cnn.pt  →  desktop_version/app.py (데스크톱 앱)
                                  │
                                  └→ export_web_weights.py → web_version/weights.js → web_version/index.html (웹 앱)
```
````

- [ ] **Step 5: 문서 검증** — 문서에 적은 경로·명령·함수 이름이 실제와 맞는지 확인:

```bash
ls web_version web_version/js web_version/tests desktop_version
grep -c "function 숫자인식CNN_로짓\|function 가중치_해독\|function 가장_큰_위치" web_version/js/model.js
grep -c "function MNIST형식으로_변환\|function 파이썬식_반올림\|function 크기_바꾸기" web_version/js/preprocess.js
grep -c "function 그림판_좌표" web_version/js/app.js
```
Expected: 파일 목록이 문서 표와 일치, grep 결과 `3`, `3`, `1`.

- [ ] **Step 6: 최종 확인** — superpowers:verification-before-completion 에 따라 다음을 다시 실행해 증거를 남긴다: Task 1 Step 4 스크립트(데스크톱 동작), Task 2 Step 1 스크립트(내보내기 검증), `tests/test.html` 의 `window.테스트결과` (`통과 30 / 전체 30`), `index.html` 에서 숫자 하나 그려 인식.
