# -*- coding: utf-8 -*-
"""마우스로 숫자를 그리면 학습된 CNN(mnist_cnn.pt)으로 인식하는 손글씨 앱"""

import ctypes
import os
import sys
import tkinter as tk
from tkinter import messagebox

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw

from model import 숫자인식CNN

# ===== 설정 =====
# 바로가기 등 어디에서 실행하더라도 파일을 찾을 수 있도록 이 파일이 있는 폴더를 기준으로 경로를 잡음
프로젝트폴더 = os.path.dirname(os.path.abspath(__file__))
가중치파일 = os.path.join(프로젝트폴더, "mnist_cnn.pt")
아이콘파일 = os.path.join(프로젝트폴더, "app.ico")
# 작업 표시줄에서 이 앱을 구별하는 고유 ID (make_shortcut.py 의 값과 반드시 같아야 함)
앱ID = "DSMP.HandwritingDigitRecognizer"
캔버스크기 = 280        # 화면에 보이는 그림판 크기(픽셀)
붓두께 = 18             # 선 굵기
평균, 표준편차 = 0.1307, 0.3081  # 학습 때와 같은 정규화 값


def 윈도우_앱ID_설정():
    """
    작업 표시줄이 이 창을 'Python'이 아닌 독립된 앱으로 인식하도록 고유 ID를 지정.
    바로가기에도 같은 ID가 들어 있어서, 고정한 아이콘과 실행 중인 창이 한 버튼으로 합쳐짐.
    """
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(앱ID)
        except (AttributeError, OSError):
            pass  # ID 지정에 실패해도 앱 실행에는 문제가 없음


def 모델_불러오기():
    """저장된 가중치를 읽어 추론용 모델을 준비"""
    if not os.path.exists(가중치파일):
        raise FileNotFoundError(f"'{가중치파일}' 파일이 없습니다. 먼저 train.py 를 실행해 주세요.")
    모델 = 숫자인식CNN()
    모델.load_state_dict(torch.load(가중치파일, map_location="cpu", weights_only=True))
    모델.eval()  # 드롭아웃·배치정규화를 추론 모드로 전환
    return 모델


def MNIST형식으로_변환(그림: Image.Image) -> torch.Tensor:
    """
    그림판 이미지를 MNIST 데이터와 같은 형식(28x28, 가운데 정렬)으로 변환.
    MNIST 숫자는 20x20 상자 안에 들어가고, 무게중심이 28x28 가운데에 오도록 만들어져 있음.
    """
    # 1) 글씨가 있는 영역만 잘라내기
    영역 = 그림.getbbox()
    if 영역 is None:
        return None  # 아무것도 그리지 않은 경우
    숫자 = 그림.crop(영역)

    # 2) 가로세로 비율을 유지하며 긴 쪽을 20픽셀로 축소
    가로, 세로 = 숫자.size
    배율 = 20.0 / max(가로, 세로)
    새크기 = (max(1, round(가로 * 배율)), max(1, round(세로 * 배율)))
    숫자 = 숫자.resize(새크기, Image.LANCZOS)

    # 3) 28x28 검은 배경의 가운데에 붙이기
    배경 = Image.new("L", (28, 28), 0)
    배경.paste(숫자, ((28 - 새크기[0]) // 2, (28 - 새크기[1]) // 2))

    # 4) 무게중심이 정중앙(14, 14)에 오도록 위치 보정
    배열 = np.asarray(배경, dtype=np.float32)
    전체 = 배열.sum()
    세로좌표, 가로좌표 = np.indices(배열.shape)
    중심y = (세로좌표 * 배열).sum() / 전체
    중심x = (가로좌표 * 배열).sum() / 전체
    이동x, 이동y = round(14 - 중심x), round(14 - 중심y)
    배경 = 배경.transform((28, 28), Image.AFFINE, (1, 0, -이동x, 0, 1, -이동y), fill=0)

    # 5) 텐서로 바꾸고 학습 때와 같은 방식으로 정규화 → 모양: (1, 1, 28, 28)
    텐서 = torch.from_numpy(np.asarray(배경, dtype=np.float32) / 255.0)
    텐서 = (텐서 - 평균) / 표준편차
    return 텐서.unsqueeze(0).unsqueeze(0)


class 손글씨앱:
    """tkinter 로 만든 그림판 + 인식 결과 화면"""

    def __init__(self, 창: tk.Tk):
        self.창 = 창
        self.모델 = 모델_불러오기()
        창.title("손글씨 숫자 인식기 (PyTorch CNN)")
        창.resizable(False, False)
        # 창 제목 표시줄과 작업 표시줄에 보일 아이콘 지정
        if os.path.exists(아이콘파일):
            창.iconbitmap(default=아이콘파일)

        # 화면용 캔버스와 별개로, 실제 인식에 쓸 흑백 이미지를 메모리에 함께 그림
        # (검은 배경에 흰 글씨 = MNIST 와 같은 색 구성)
        self.그림 = Image.new("L", (캔버스크기, 캔버스크기), 0)
        self.붓 = ImageDraw.Draw(self.그림)
        self.이전좌표 = None

        # ----- 왼쪽: 그림판 -----
        왼쪽 = tk.Frame(창, padx=10, pady=10)
        왼쪽.grid(row=0, column=0)
        tk.Label(왼쪽, text="여기에 숫자(0~9)를 그려 주세요", font=("맑은 고딕", 11)).pack()
        self.캔버스 = tk.Canvas(왼쪽, width=캔버스크기, height=캔버스크기,
                              bg="black", cursor="pencil", highlightthickness=1)
        self.캔버스.pack(pady=5)
        self.캔버스.bind("<B1-Motion>", self.그리기)
        self.캔버스.bind("<ButtonRelease-1>", self.붓_떼기)

        버튼줄 = tk.Frame(왼쪽)
        버튼줄.pack(fill="x")
        tk.Button(버튼줄, text="인식하기", width=12, command=self.인식하기,
                  font=("맑은 고딕", 10, "bold")).pack(side="left", expand=True)
        tk.Button(버튼줄, text="지우기", width=12, command=self.지우기,
                  font=("맑은 고딕", 10)).pack(side="left", expand=True)

        # ----- 오른쪽: 결과 표시 -----
        오른쪽 = tk.Frame(창, padx=10, pady=10)
        오른쪽.grid(row=0, column=1, sticky="n")
        tk.Label(오른쪽, text="인식 결과", font=("맑은 고딕", 11)).pack()
        self.결과글자 = tk.Label(오른쪽, text="?", font=("맑은 고딕", 64, "bold"), fg="#1a73e8")
        self.결과글자.pack()
        self.신뢰도글자 = tk.Label(오른쪽, text="", font=("맑은 고딕", 10))
        self.신뢰도글자.pack()

        # 숫자별 확률 막대 그래프
        self.막대들 = []
        막대틀 = tk.Frame(오른쪽, pady=8)
        막대틀.pack()
        for 숫자 in range(10):
            tk.Label(막대틀, text=str(숫자), width=2, font=("맑은 고딕", 9)).grid(row=숫자, column=0)
            막대 = tk.Canvas(막대틀, width=150, height=14, bg="#eeeeee", highlightthickness=0)
            막대.grid(row=숫자, column=1, pady=1)
            값 = tk.Label(막대틀, text="0.0%", width=6, anchor="e", font=("맑은 고딕", 9))
            값.grid(row=숫자, column=2)
            self.막대들.append((막대, 값))

        # 키보드 단축키: Enter = 인식, Esc / Delete = 지우기
        창.bind("<Return>", lambda e: self.인식하기())
        창.bind("<Escape>", lambda e: self.지우기())
        창.bind("<Delete>", lambda e: self.지우기())

    def 그리기(self, 이벤트):
        """마우스를 끌 때마다 화면과 메모리 이미지에 동시에 선을 그림"""
        x, y = 이벤트.x, 이벤트.y
        if self.이전좌표 is not None:
            px, py = self.이전좌표
            self.캔버스.create_line(px, py, x, y, fill="white", width=붓두께,
                                  capstyle=tk.ROUND, smooth=True)
            self.붓.line([px, py, x, y], fill=255, width=붓두께)
        # 선 끝을 둥글게 만들기 위해 원도 함께 그림
        r = 붓두께 // 2
        self.캔버스.create_oval(x - r, y - r, x + r, y + r, fill="white", outline="white")
        self.붓.ellipse([x - r, y - r, x + r, y + r], fill=255)
        self.이전좌표 = (x, y)

    def 붓_떼기(self, _이벤트):
        """마우스 버튼을 떼면 선을 끊고 바로 인식"""
        self.이전좌표 = None
        self.인식하기()

    def 지우기(self):
        """그림판과 결과를 모두 초기화"""
        self.캔버스.delete("all")
        self.붓.rectangle([0, 0, 캔버스크기, 캔버스크기], fill=0)
        self.결과글자.config(text="?")
        self.신뢰도글자.config(text="")
        self.막대_갱신([0.0] * 10)

    @torch.no_grad()
    def 인식하기(self):
        """현재 그림을 모델에 넣어 숫자를 예측하고 화면에 표시"""
        입력 = MNIST형식으로_변환(self.그림)
        if 입력 is None:
            self.신뢰도글자.config(text="먼저 숫자를 그려 주세요")
            return
        확률 = F.softmax(self.모델(입력), dim=1)[0].tolist()
        예측 = int(np.argmax(확률))
        self.결과글자.config(text=str(예측))
        self.신뢰도글자.config(text=f"확신도: {확률[예측] * 100:.1f}%")
        self.막대_갱신(확률)

    def 막대_갱신(self, 확률):
        """숫자별 확률 막대 그래프를 다시 그림"""
        최대 = max(확률)
        for (막대, 값), p in zip(self.막대들, 확률):
            막대.delete("all")
            색 = "#1a73e8" if p == 최대 and p > 0 else "#9aa0a6"
            막대.create_rectangle(0, 0, int(150 * p), 14, fill=색, width=0)
            값.config(text=f"{p * 100:.1f}%")


if __name__ == "__main__":
    윈도우_앱ID_설정()  # 창을 만들기 전에 호출해야 적용됨
    루트 = tk.Tk()
    try:
        손글씨앱(루트)
    except Exception as 오류:
        # 바로가기(pythonw)로 실행하면 콘솔 창이 없으므로 오류를 메시지 창으로 보여 줌
        루트.withdraw()
        messagebox.showerror("손글씨 숫자 인식기 - 오류", str(오류))
        루트.destroy()
        sys.exit(1)
    루트.mainloop()
