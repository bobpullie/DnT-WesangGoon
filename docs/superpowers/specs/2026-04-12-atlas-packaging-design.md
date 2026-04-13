# Atlas 패키지화 — 표준 Python 패키지 + Claude Code 스킬 배포

> 작성: 2026-04-12, 위상군 Session 22
> 상태: 승인 대기

## 1. 목적

atlas를 `pip install git+https://github.com/bobpullie/atlas`로 설치 가능한 표준 Python 패키지로 변환하여, 다른 PC의 Claude Code 에이전트에게 `/atlas` 스킬로 제공한다.

## 2. 현재 문제

- flat layout + `pythonpath = [".."]` 해킹으로 pytest만 동작
- `pip install -e .` 불가 — `import atlas` 실패
- SKILL.md 배포 경로 없음
- CLI가 개별 엔트리포인트 7개로 분산

## 3. 결정 사항

| 항목 | 결정 | 근거 |
|------|------|------|
| 레이아웃 | src layout (`src/atlas/`) | Python 패키징 베스트 프랙티스, pip install 보장 |
| PyPI name | `atlas-docs` | `atlas` 기존 점유, 충돌 방지 |
| CLI | 통합 `atlas <command>` | 에이전트 UX, SKILL.md 1:1 대응 |
| TEMS 의존성 | optional (`atlas-docs[tems]`) | 핵심은 독립 동작, TEMS 있으면 완전 통합 |
| SKILL.md 배포 | package_data + `atlas init-skill` | pip post-install 비표준이므로 명시적 커맨드 |
| import 경로 | `atlas.topology`, `atlas.atlas_setup` 등 | `scripts` 중간 패키지 제거 |

## 4. 디렉토리 레이아웃

```
atlas/                              ← git repo root (bobpullie/atlas)
├── src/
│   └── atlas/
│       ├── __init__.py             ← __version__ = "1.0.0"
│       ├── cli.py                  ← 통합 CLI 진입점
│       ├── topology.py
│       ├── render_template.py
│       ├── anchor_detect.py
│       ├── git_analysis.py
│       ├── atlas_setup.py
│       ├── atlas_backfill.py
│       ├── atlas_check.py
│       ├── atlas_split.py
│       ├── atlas_collapse.py
│       ├── atlas_promote_check.py
│       ├── tems_query.py           ← TEMS_AVAILABLE 분기
│       ├── templates/
│       │   ├── L0.template.md
│       │   ├── Lk.template.md
│       │   ├── Lk.history.template.md
│       │   ├── README.template.md
│       │   └── CHANGELOG.template.md
│       ├── hook_templates/
│       │   ├── post_tool_use_sync.py.tmpl
│       │   └── session_end_check.py.tmpl
│       ├── SKILL.md                ← package_data (init-skill 소스)
│       └── references/
│           ├── topology-invariants.md
│           ├── drill-down-protocol.md
│           ├── backfill-staged.md
│           ├── sync-watch-schema.md
│           ├── promotion-rules.md
│           └── anchor-presets.md
├── tests/
│   ├── conftest.py
│   ├── test_topology_core.py
│   ├── test_topology_invariants_i5_i8.py
│   ├── test_topology_skeleton_and_check_all.py
│   ├── test_topology_sync_index.py
│   ├── test_anchor_detect.py
│   ├── test_atlas_setup.py
│   ├── test_atlas_check.py
│   ├── test_render_template.py
│   ├── test_hook_templates.py
│   ├── test_git_analysis.py
│   ├── test_backfill.py
│   ├── test_tems_query.py
│   ├── test_promote_check.py
│   ├── test_promote_register.py
│   ├── test_atlas_split.py
│   ├── test_atlas_collapse.py
│   └── test_e2e_smoke.py
├── SKILL.md                        ← repo root에도 유지 (GitHub 열람용)
├── references/                     ← repo root에도 유지 (GitHub 열람용)
├── pyproject.toml
└── README.md
```

## 5. pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "atlas-docs"
version = "1.0.0"
description = "Dynamic hierarchical documentation for agent contexts"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0",
    "python-frontmatter>=1.0",
]

[project.optional-dependencies]
tems = ["tems @ git+https://github.com/bobpullie/TEMS"]
dev = ["pytest>=7.0"]

[project.scripts]
atlas = "atlas.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
atlas = [
    "templates/*.md",
    "hook_templates/*.tmpl",
    "SKILL.md",
    "references/*.md",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## 6. CLI 설계 (`cli.py`)

통합 `atlas` 커맨드. argparse 서브파서 기반.

```
atlas setup <root> --name <N> --modules <m1,m2,...> [--no-confirm]
atlas backfill <root> --stage <2|3> [--k N] [--use-haiku]
atlas check <root>
atlas split <target> [--mode vertical|horizontal] [--project-root <root>]
atlas collapse <target> [--project-root <root>]
atlas promote-check <root> [--threshold F]
atlas init-skill [--target <path>]
```

모든 서브커맨드의 `project_root`는 기본값 `.` (현재 디렉토리).

## 7. TEMS optional 분기

### 7.1 분기 지점

| 모듈 | TEMS 사용 | TEMS 미설치 시 |
|------|-----------|---------------|
| `tems_query.py` | `from tems import ...` | `TEMS_AVAILABLE = False`, 순수함수만 유지 |
| `atlas_setup.py` | TCL 등록 | 스킵 + 경고 출력 |
| `atlas_backfill.py` | Stage 3 tgl_xref | xref=0으로 진행 |
| `atlas_promote_check.py` | 기존 TGL 필터 + 등록 | 후보 표시만, 등록 스킵 |
| `topology.py` | 없음 | 영향 없음 |
| `atlas_check.py` | 없음 | 영향 없음 |
| `atlas_split.py` / `atlas_collapse.py` | 없음 | 영향 없음 |

### 7.2 순수 함수 (atlas 자체 유지)

`jaccard_similarity` — 집합 유사도 계산. TEMS 불필요.

### 7.3 전제 조건

TEMS (`bobpullie/TEMS`)도 `pip install` 가능한 표준 패키지로 리팩터링 필요. 이 스펙 범위 밖이지만 `atlas-docs[tems]` 동작을 위한 전제.

## 8. init-skill 메커니즘

```python
def init_skill(target="~/.claude/skills/atlas"):
    target = Path(target).expanduser()
    target.mkdir(parents=True, exist_ok=True)

    skill_src = importlib.resources.files("atlas") / "SKILL.md"
    shutil.copy2(skill_src, target / "SKILL.md")

    ref_src = importlib.resources.files("atlas") / "references"
    if ref_src.is_dir():
        shutil.copytree(ref_src, target / "references", dirs_exist_ok=True)

    print(f"atlas skill installed at {target}")
```

## 9. 에이전트 온보딩 E2E 시나리오

```bash
# 1. 설치 (1회)
pip install git+https://github.com/bobpullie/atlas
atlas init-skill
# → ~/.claude/skills/atlas/SKILL.md + references/ 배포

# 2. Claude Code 에이전트 세션에서
# 에이전트가 /atlas 스킬을 인식 → SKILL.md 로드
atlas setup . --name MyProject --modules core,api,db --no-confirm
atlas backfill . --stage 2
atlas backfill . --stage 3
atlas check .

# 3. 일상 사용 (자동)
# - PostToolUse hook → <doc-sync-reminder> 주입
# - 에이전트가 drift clear (3-Option Rule)
# - 세션 종료 시 session_end_check
```

## 10. 마이그레이션 체크리스트

1. `scripts/*.py` → `src/atlas/*.py` 이동
2. `templates/`, `hook_templates/` → `src/atlas/` 안으로 이동
3. `SKILL.md`, `references/` → `src/atlas/` 안으로 복사 (repo root에도 유지)
4. `src/atlas/__init__.py` 생성 (`__version__`)
5. `src/atlas/cli.py` 신규 작성
6. `scripts/__init__.py` 제거
7. 모든 테스트 import: `atlas.scripts.X` → `atlas.X`
8. `conftest.py` 수정: fixture import 경로 변경
9. `pyproject.toml` 전면 교체
10. `pip install -e .` → 52 tests green 확인
11. `atlas --help` CLI 동작 확인
12. `atlas init-skill` → SKILL.md 복사 확인

## 11. 범위 밖 (별도 태스크)

- TEMS 표준 패키지화 (`bobpullie/TEMS`)
- GitHub Actions CI/CD
- PyPI 퍼블리시 (현재 git+https 설치로 충분)
- `atlas rebuild-cache` 구현 (Phase 10 deferred)
