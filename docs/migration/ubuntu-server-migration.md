# DnT 미니PC (Ubuntu Server) 마이그레이션 가이드

> 생성: 2026-04-13 S27 | 방식: B+ 하이브리드 (새 환경 + TEMS DB 이식)

## 사전 조건 (Ubuntu 서버)

```bash
# Python 3.10+
python3 --version

# Node.js 18+ (Claude Code CLI 필요)
node --version

# git, gh CLI
sudo apt install git gh

# Claude Code CLI 설치
npm install -g @anthropic-ai/claude-code

# gh 로그인
gh auth login
```

## Phase 1: 기본 인프라 (Ubuntu 서버에서)

```bash
# 1-1. 작업 디렉토리 구조 생성
mkdir -p ~/DnT ~/agents

# 1-2. TEMS 패키지 설치
pip install git+https://github.com/bobpullie/TEMS.git

# 1-3. TEMS 레지스트리 경로 설정 (.bashrc에 추가)
echo 'export TEMS_REGISTRY_PATH="$HOME/agents/tems_registry.json"' >> ~/.bashrc
source ~/.bashrc
```

## Phase 2: Git 레포 클론

```bash
cd ~/DnT

# DnT 메인 (MRV_DnT → 빌드군)
git clone https://github.com/bobpullie/DnT.git MRV_DnT

# KnowledgeHub (기록군)
git clone https://github.com/bobpullie/KnowledgeHub.git

# KJI_Portfolio (포폴군)
git clone https://github.com/blueitems-Mystic/KJI_id.git KJI_Portfolio

# TEMS 패키지 (개발용 — 이미 pip으로 설치했으면 선택사항)
# git clone https://github.com/bobpullie/TEMS.git ~/bobpullie/TEMS
```

## Phase 3: 에이전트 Scaffold

```bash
# 위상군
tems scaffold --agent-id wesanggoon --agent-name "위상군" --project DnT --cwd ~/agents/wesanggoon

# 빌드군
tems scaffold --agent-id buildgoon --agent-name "빌드군" --project DnT --cwd ~/DnT/MRV_DnT

# 기록군
tems scaffold --agent-id girokgoon --agent-name "기록군" --project KnowledgeHub --cwd ~/DnT/KnowledgeHub

# 포폴군
tems scaffold --agent-id pofolgoon --agent-name "포폴군" --project KJI_Portfolio --cwd ~/DnT/KJI_Portfolio

# 디니군
tems scaffold --agent-id dinigoon --agent-name "디니군" --project Houdini --cwd ~/agents/dinigoon

# 코드군
tems scaffold --agent-id codegoon --agent-name "코드군" --project Fermion --cwd ~/agents/codegoon

# 어플군
tems scaffold --agent-id appgoon --agent-name "어플군" --project ChildSchedule --cwd ~/agents/appgoon

# 관리군
tems scaffold --agent-id managegoon --agent-name "관리군" --project TCAS --cwd ~/agents/managegoon
```

## Phase 4: TEMS 메모리 이식 (현재 PC → Ubuntu)

**이식 대상 (규칙 수 > 0인 에이전트만):**

| 에이전트 | 규칙 수 | 원본 경로 (Windows) |
|---------|---------|-------------------|
| wesanggoon | 64 | `E:/DnT/DnT_WesangGoon/memory/error_logs.db` |
| codegoon | 47 | `E:/QuantProject/DnT_Fermion/memory/error_logs.db` |
| girokgoon | 19 | `E:/KnowledgeHub/memory/error_logs.db` |
| pofolgoon | 7 | `E:/KJI_Portfolio/memory/error_logs.db` |
| appgoon | 5 | `E:/ChildSchedule/memory/error_logs.db` |
| dinigoon | 4 | `E:/01_houdiniAgent/memory/error_logs.db` |

### Windows 쪽에서 SCP 전송:

```powershell
# 미니PC IP를 MINI_IP로 대체
$MINI_IP = "192.168.x.x"
$USER = "your_ubuntu_user"

# DB 파일 전송
scp E:\DnT\DnT_WesangGoon\memory\error_logs.db ${USER}@${MINI_IP}:~/agents/wesanggoon/memory/
scp E:\QuantProject\DnT_Fermion\memory\error_logs.db ${USER}@${MINI_IP}:~/agents/codegoon/memory/
scp E:\KnowledgeHub\memory\error_logs.db ${USER}@${MINI_IP}:~/DnT/KnowledgeHub/memory/
scp E:\KJI_Portfolio\memory\error_logs.db ${USER}@${MINI_IP}:~/DnT/KJI_Portfolio/memory/
scp E:\ChildSchedule\memory\error_logs.db ${USER}@${MINI_IP}:~/agents/appgoon/memory/
scp E:\01_houdiniAgent\memory\error_logs.db ${USER}@${MINI_IP}:~/agents/dinigoon/memory/
```

## Phase 5: 위상군 docs 이식 (git 아님!)

위상군(DnT_WesangGoon)은 git repo가 아니므로 핵심 문서를 직접 복사:

```powershell
# 핸드오버 문서 + docs + CLAUDE.md
scp -r E:\DnT\DnT_WesangGoon\handover_doc ${USER}@${MINI_IP}:~/agents/wesanggoon/
scp -r E:\DnT\DnT_WesangGoon\docs ${USER}@${MINI_IP}:~/agents/wesanggoon/
scp E:\DnT\DnT_WesangGoon\CLAUDE.md ${USER}@${MINI_IP}:~/agents/wesanggoon/
scp -r E:\DnT\DnT_WesangGoon\.claude ${USER}@${MINI_IP}:~/agents/wesanggoon/

# qmd_rules (있으면)
scp -r E:\DnT\DnT_WesangGoon\memory\qmd_rules ${USER}@${MINI_IP}:~/agents/wesanggoon/memory/
```

## Phase 6: 검증 (Ubuntu 서버에서)

```bash
# TEMS 패키지 확인
python3 -c "import tems; print(tems.__version__)"

# 각 에이전트 DB 확인
for dir in ~/agents/wesanggoon ~/DnT/MRV_DnT ~/DnT/KnowledgeHub ~/DnT/KJI_Portfolio; do
  db="$dir/memory/error_logs.db"
  if [ -f "$db" ]; then
    count=$(python3 -c "import sqlite3; c=sqlite3.connect('$db'); print(c.execute('SELECT COUNT(*) FROM memory_logs').fetchone()[0])")
    agent=$(cat "$dir/.claude/tems_agent_id" 2>/dev/null)
    echo "$agent: $count rules"
  fi
done

# Claude Code 세션 시작 테스트
cd ~/agents/wesanggoon
claude
```

## Phase 7: SSH 원격 작업

```bash
# Windows에서 미니PC 접속
ssh user@mini-pc-ip

# tmux로 세션 유지 (SSH 끊어져도 계속 실행)
tmux new -s wesanggoon
cd ~/agents/wesanggoon
claude

# 다른 에이전트는 다른 tmux 창에서
# Ctrl+B, C → 새 창
# Ctrl+B, 0~9 → 창 전환
```

## 디렉토리 구조 (Ubuntu)

```
~/
├── DnT/
│   ├── MRV_DnT/          # 빌드군 (git clone)
│   ├── KnowledgeHub/      # 기록군 (git clone)
│   └── KJI_Portfolio/     # 포폴군 (git clone)
├── agents/
│   ├── tems_registry.json # TEMS 중앙 레지스트리
│   ├── wesanggoon/        # 위상군 (scaffold + docs 복사)
│   ├── dinigoon/          # 디니군 (scaffold)
│   ├── codegoon/          # 코드군 (scaffold)
│   ├── appgoon/           # 어플군 (scaffold)
│   └── managegoon/        # 관리군 (scaffold)
└── bobpullie/
    └── TEMS/              # (선택) 개발용 clone
```

## 주의사항

1. **CLAUDE.md 경로 수정 필요** — 이식 후 `E:\` 경로를 `~/` 로 바꿔야 함
2. **settings.local.json** — scaffold가 Linux 경로로 자동 생성하므로 OK
3. **Anthropic API 키** — 미니PC에서 `claude` 첫 실행 시 설정
4. **WAL 파일** — `error_logs.db-wal`, `-shm`, `-journal` 파일은 복사하지 않아도 됨
