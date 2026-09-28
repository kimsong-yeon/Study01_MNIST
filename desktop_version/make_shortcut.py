# -*- coding: utf-8 -*-
"""
손글씨 숫자 인식 앱의 아이콘(app.ico)과 바탕 화면 바로가기를 만드는 코드.

- 바로가기는 pythonw.exe 로 app.py 를 실행하므로 검은 콘솔 창이 뜨지 않음
- 바로가기에 앱 고유 ID(AppUserModelID)를 넣어서 작업 표시줄에 고정했을 때
  고정 아이콘과 실행 중인 창이 하나의 버튼으로 합쳐지도록 함
"""

import base64
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

from app import 앱ID  # 앱과 바로가기가 같은 ID를 쓰도록 app.py 의 값을 그대로 가져옴

# 윈도우 콘솔에서도 한글이 깨지지 않도록 출력 인코딩을 UTF-8로 설정
sys.stdout.reconfigure(encoding="utf-8")

# ===== 경로 설정 =====
프로젝트폴더 = os.path.dirname(os.path.abspath(__file__))
아이콘파일 = os.path.join(프로젝트폴더, "app.ico")
앱파일 = os.path.join(프로젝트폴더, "app.py")
# 콘솔 창 없이 실행하는 파이썬 (가상환경 안의 pythonw.exe)
콘솔없는파이썬 = os.path.join(프로젝트폴더, ".venv", "Scripts", "pythonw.exe")
바로가기이름 = "손글씨 숫자 인식기.lnk"


def 아이콘_만들기():
    """파란 둥근 사각형 위에 손글씨 느낌의 흰색 숫자를 그린 아이콘(.ico)을 생성"""
    크기 = 256
    그림 = Image.new("RGBA", (크기, 크기), (0, 0, 0, 0))

    # 위에서 아래로 밝은 파랑 → 진한 파랑으로 변하는 그라데이션 배경
    그라데이션 = Image.new("RGBA", (크기, 크기))
    붓 = ImageDraw.Draw(그라데이션)
    for y in range(크기):
        t = y / (크기 - 1)
        색 = (int(66 + (21 - 66) * t), int(133 + (87 - 133) * t), int(244 + (176 - 244) * t), 255)
        붓.line([(0, y), (크기, y)], fill=색)

    # 둥근 사각형 모양으로 잘라내기
    가림막 = Image.new("L", (크기, 크기), 0)
    ImageDraw.Draw(가림막).rounded_rectangle([8, 8, 크기 - 8, 크기 - 8], radius=52, fill=255)
    그림.paste(그라데이션, (0, 0), 가림막)

    # 손글씨 느낌의 글꼴(Segoe Print)로 숫자를 그림. 글꼴이 없으면 일반 글꼴 사용
    글꼴 = None
    for 글꼴파일 in ("segoeprb.ttf", "segoepr.ttf", "arialbd.ttf"):
        try:
            글꼴 = ImageFont.truetype(글꼴파일, 190)
            break
        except OSError:
            continue
    if 글꼴 is None:
        글꼴 = ImageFont.load_default()

    붓 = ImageDraw.Draw(그림)
    # 글자를 정중앙에 배치 (anchor="mm": 가로·세로 가운데 기준)
    붓.text((크기 // 2 + 6, 크기 // 2 + 10), "7", font=글꼴, fill=(0, 0, 0, 70), anchor="mm")  # 그림자
    붓.text((크기 // 2, 크기 // 2), "7", font=글꼴, fill="white", anchor="mm")

    # 윈도우가 상황에 맞게 골라 쓰도록 여러 크기를 한 파일에 담아 저장
    그림.save(아이콘파일, format="ICO",
              sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"아이콘 생성: {아이콘파일}")


# 바로가기를 만드는 PowerShell 코드.
# 앱 고유 ID는 일반 바로가기 도구(WScript.Shell)로는 넣을 수 없어서,
# 윈도우 셸 COM 인터페이스(IShellLink, IPropertyStore)를 C#으로 직접 호출함.
# 경로에 한글·공백이 있어도 안전하도록 값은 환경 변수로 전달함.
바로가기_파워셸코드 = r'''
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Text;

[ComImport, Guid("000214F9-0000-0000-C000-000000000046"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IShellLinkW {
    void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder f, int n, IntPtr fd, uint fl);
    void GetIDList(out IntPtr p);
    void SetIDList(IntPtr p);
    void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int n);
    void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string s);
    void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int n);
    void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string s);
    void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int n);
    void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string s);
    void GetHotkey(out short h);
    void SetHotkey(short h);
    void GetShowCmd(out int c);
    void SetShowCmd(int c);
    void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int n, out int i);
    void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string s, int i);
    void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string s, uint r);
    void Resolve(IntPtr hwnd, uint fl);
    void SetPath([MarshalAs(UnmanagedType.LPWStr)] string s);
}

[StructLayout(LayoutKind.Sequential, Pack = 4)]
public struct PropertyKey { public Guid fmtid; public uint pid; }

[StructLayout(LayoutKind.Explicit, Size = 24)]
public struct PropVariant { [FieldOffset(0)] public ushort vt; [FieldOffset(8)] public IntPtr p; }

[ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPropertyStore {
    void GetCount(out uint c);
    void GetAt(uint i, out PropertyKey k);
    void GetValue(ref PropertyKey k, out PropVariant v);
    void SetValue(ref PropertyKey k, ref PropVariant v);
    void Commit();
}

public static class ShortcutMaker {
    public static void Create(string lnk, string target, string args, string workDir,
                              string icon, string desc, string appId) {
        var link = (IShellLinkW)Activator.CreateInstance(
            Type.GetTypeFromCLSID(new Guid("00021401-0000-0000-C000-000000000046")));
        link.SetPath(target);
        link.SetArguments(args);
        link.SetWorkingDirectory(workDir);
        link.SetIconLocation(icon, 0);
        link.SetDescription(desc);

        // PKEY_AppUserModel_ID
        var key = new PropertyKey { fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"), pid = 5 };
        var value = new PropVariant { vt = 31 /* VT_LPWSTR */, p = Marshal.StringToCoTaskMemUni(appId) };
        try {
            var store = (IPropertyStore)link;
            store.SetValue(ref key, ref value);
            store.Commit();
        } finally {
            Marshal.FreeCoTaskMem(value.p);
        }
        ((IPersistFile)link).Save(lnk, true);
    }
}
"@

$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = Join-Path $desktop $env:SC_NAME
[ShortcutMaker]::Create($lnk, $env:SC_TARGET, ('"' + $env:SC_APP + '"'), $env:SC_WORKDIR,
                        $env:SC_ICON, $env:SC_DESC, $env:SC_APPID)
Write-Output $lnk
'''


def 출력_해독(바이트: bytes) -> str:
    """PowerShell 출력을 문자열로 변환 (UTF-8 우선, 실패하면 윈도우 기본 인코딩 사용)"""
    try:
        return 바이트.decode("utf-8")
    except UnicodeDecodeError:
        return 바이트.decode("mbcs", errors="replace")


def 바로가기_만들기():
    """바탕 화면에 콘솔 없이 앱을 실행하는 바로가기를 생성"""
    if not os.path.exists(콘솔없는파이썬):
        raise FileNotFoundError(f"'{콘솔없는파이썬}' 이 없습니다. 먼저 가상환경(.venv)을 만들어 주세요.")

    환경변수 = dict(os.environ,
                SC_NAME=바로가기이름,
                SC_TARGET=콘솔없는파이썬,
                SC_APP=앱파일,
                SC_WORKDIR=프로젝트폴더,
                SC_ICON=아이콘파일,
                SC_DESC="마우스로 그린 손글씨 숫자를 인식합니다",
                SC_APPID=앱ID)
    # 한글이 섞인 코드를 안전하게 넘기기 위해 UTF-16 인코딩 후 base64로 전달
    인코딩된코드 = base64.b64encode(바로가기_파워셸코드.encode("utf-16-le")).decode("ascii")
    결과 = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", 인코딩된코드],
        env=환경변수, capture_output=True,
    )
    if 결과.returncode != 0:
        raise RuntimeError(f"바로가기 생성 실패:\n{출력_해독(결과.stderr)}")
    print(f"바로가기 생성: {출력_해독(결과.stdout).strip()}")


if __name__ == "__main__":
    아이콘_만들기()
    바로가기_만들기()
    print("완료! 바탕 화면의 '손글씨 숫자 인식기' 아이콘을 더블 클릭해 보세요.")
