---
description: TEMS Rule Viewer 를 별도 네이티브 윈도우로 실행 (컨텍스트 격리)
argument-hint: ""
---

# /tems-view — TEMS 규칙 뷰어 실행

규칙들을 별도 윈도우(NiceGUI + pywebview 네이티브)에서 모니터링/편집하기 위한 명령. **viewer 는 별도 OS 프로세스로 detached 되어 실행되므로, 내(에이전트) 컨텍스트엔 "launched (PID xxx)" 한 줄만 들어간다.** 실제 규칙 내용은 viewer 윈도우에만 표시되어 컨텍스트 오염 0.

## 실행

다음 한 줄을 Bash 로 실행하고 즉시 종료할 것. PID 만 보고하고 추가 액션 금지.

```bash
python -c "
import subprocess, sys, os
from pathlib import Path
viewer = Path('viewer/rule_viewer.py')
if not viewer.exists():
    print('[ERR] viewer not installed at viewer/rule_viewer.py'); sys.exit(1)
# pythonw.exe (windows subsystem, 콘솔 없음) + CREATE_NO_WINDOW 조합으로 conhost.exe 깜빡임 차단.
# pythonw 부재 환경(비-Windows / 임베디드)은 sys.executable 로 fallback.
exe = sys.executable
if os.name == 'nt':
    pw = Path(sys.executable).with_name('pythonw.exe')
    if pw.exists(): exe = str(pw)
    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
else:
    flags = 0
p = subprocess.Popen([exe, str(viewer)], creationflags=flags, close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f'TEMS Rule Viewer launched — PID {p.pid} (detached, separate window)')
"
```

## 의존성 미설치 시

위 실행이 PID 만 출력했지만 윈도우가 안 뜨면, 의존성 설치 안 된 것:
```bash
pip install -r viewer/requirements.txt
```

## 격리 보장 (왜 컨텍스트에 안 들어오나)

- `subprocess.Popen` + `DETACHED_PROCESS` 플래그 → viewer 가 부모 프로세스(claude-code)와 분리
- `stdout=DEVNULL` → viewer 의 모든 출력이 컨텍스트로 들어오지 않음
- viewer 는 자체 NiceGUI 서버를 localhost 임의 포트로 띄우고 pywebview 네이티브 윈도우로 표시
- 종일군이 viewer 를 닫아도 claude-code 세션은 영향 없음

## 보고 형식

PID 만 사용자에게 보고할 것. 예: "TEMS Rule Viewer 가 별도 윈도우로 실행됐어 (PID 12345)."
