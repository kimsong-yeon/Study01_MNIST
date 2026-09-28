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
        ("작은점", [(200, 90)], 6),                               # 20px 보다 작아서 확대 경로를 탐
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
