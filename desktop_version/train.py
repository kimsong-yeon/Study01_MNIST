# -*- coding: utf-8 -*-
"""MNIST 데이터셋으로 CNN을 학습하고 가중치를 mnist_cnn.pt 로 저장하는 코드"""

import sys
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model import 숫자인식CNN

# 윈도우 콘솔에서도 한글이 깨지지 않도록 출력 인코딩을 UTF-8로 설정
sys.stdout.reconfigure(encoding="utf-8")

# ===== 학습 설정 =====
에폭수 = 5
배치크기 = 128
학습률 = 1e-3
가중치파일 = "mnist_cnn.pt"
장치 = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# MNIST 전체 데이터의 평균과 표준편차 (정규화에 사용)
평균, 표준편차 = 0.1307, 0.3081


def 데이터로더_만들기():
    """학습용/시험용 데이터로더를 만들어 반환"""
    # 학습 데이터에는 약간의 회전·이동·확대를 적용해
    # 사람이 직접 그린 삐뚤어진 글씨에도 잘 동작하도록 함
    학습변환 = transforms.Compose([
        transforms.RandomAffine(degrees=10, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize((평균,), (표준편차,)),
    ])
    시험변환 = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((평균,), (표준편차,)),
    ])

    # 데이터가 없으면 ./data 폴더에 자동으로 내려받음
    학습데이터 = datasets.MNIST("data", train=True, download=True, transform=학습변환)
    시험데이터 = datasets.MNIST("data", train=False, download=True, transform=시험변환)

    학습로더 = DataLoader(학습데이터, batch_size=배치크기, shuffle=True)
    시험로더 = DataLoader(시험데이터, batch_size=1000, shuffle=False)
    return 학습로더, 시험로더


def 한_에폭_학습(모델, 로더, 최적화기, 손실함수):
    """학습 데이터 전체를 한 번 돌며 가중치를 갱신하고 평균 손실을 반환"""
    모델.train()
    누적손실 = 0.0
    for 이미지, 정답 in 로더:
        이미지, 정답 = 이미지.to(장치), 정답.to(장치)
        최적화기.zero_grad()           # 이전 기울기 초기화
        출력 = 모델(이미지)             # 순전파
        손실 = 손실함수(출력, 정답)     # 손실 계산
        손실.backward()                # 역전파
        최적화기.step()                # 가중치 갱신
        누적손실 += 손실.item() * 이미지.size(0)
    return 누적손실 / len(로더.dataset)


@torch.no_grad()
def 평가(모델, 로더):
    """시험 데이터에 대한 정확도(%)를 계산해 반환"""
    모델.eval()
    맞은개수 = 0
    for 이미지, 정답 in 로더:
        이미지, 정답 = 이미지.to(장치), 정답.to(장치)
        예측 = 모델(이미지).argmax(dim=1)
        맞은개수 += (예측 == 정답).sum().item()
    return 100.0 * 맞은개수 / len(로더.dataset)


def main():
    torch.manual_seed(0)  # 재현 가능하도록 난수 고정
    print(f"사용 장치: {장치}")

    학습로더, 시험로더 = 데이터로더_만들기()
    모델 = 숫자인식CNN().to(장치)
    최적화기 = torch.optim.Adam(모델.parameters(), lr=학습률)
    # 에폭마다 학습률을 조금씩 줄여 후반부 학습을 안정화
    스케줄러 = torch.optim.lr_scheduler.StepLR(최적화기, step_size=1, gamma=0.7)
    손실함수 = nn.CrossEntropyLoss()

    for 에폭 in range(1, 에폭수 + 1):
        시작 = time.time()
        평균손실 = 한_에폭_학습(모델, 학습로더, 최적화기, 손실함수)
        정확도 = 평가(모델, 시험로더)
        스케줄러.step()
        print(f"[{에폭}/{에폭수}] 손실: {평균손실:.4f} | 시험 정확도: {정확도:.2f}% | "
              f"소요 시간: {time.time() - 시작:.1f}초")

    # 학습된 가중치 저장
    torch.save(모델.state_dict(), 가중치파일)
    print(f"학습 완료! 가중치를 '{가중치파일}' 파일로 저장했습니다.")


if __name__ == "__main__":
    main()
