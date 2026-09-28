# -*- coding: utf-8 -*-
"""손글씨 숫자 인식용 CNN 모델 정의 (학습 코드와 앱 코드가 함께 사용)"""

import torch.nn as nn
import torch.nn.functional as F


class 숫자인식CNN(nn.Module):
    """28x28 흑백 이미지를 입력받아 0~9 숫자를 분류하는 합성곱 신경망"""

    def __init__(self):
        super().__init__()
        # 합성곱 층: 1채널(흑백) → 32채널 → 64채널
        self.합성곱1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.정규화1 = nn.BatchNorm2d(32)
        self.합성곱2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.정규화2 = nn.BatchNorm2d(64)
        # 과적합 방지를 위한 드롭아웃
        self.드롭아웃1 = nn.Dropout(0.25)
        self.드롭아웃2 = nn.Dropout(0.5)
        # 완전 연결 층: 풀링 두 번 후 64채널 x 7 x 7 → 128 → 10(숫자 개수)
        self.완전연결1 = nn.Linear(64 * 7 * 7, 128)
        self.완전연결2 = nn.Linear(128, 10)

    def forward(self, x):
        # 첫 번째 합성곱 블록: 28x28 → 14x14
        x = F.max_pool2d(F.relu(self.정규화1(self.합성곱1(x))), 2)
        # 두 번째 합성곱 블록: 14x14 → 7x7
        x = F.max_pool2d(F.relu(self.정규화2(self.합성곱2(x))), 2)
        x = self.드롭아웃1(x)
        # 1차원으로 펼친 뒤 분류
        x = x.flatten(1)
        x = self.드롭아웃2(F.relu(self.완전연결1(x)))
        return self.완전연결2(x)  # 각 숫자에 대한 점수(로짓) 반환
