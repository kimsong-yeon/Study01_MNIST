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
- `.claude/launch.json` 의 `web` 설정은 `web_version` 을 `http://localhost:8765` 로 띄우는 로컬 확인용 정적 서버입니다.
