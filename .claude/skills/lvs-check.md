---
name: lvs-check
description: "빌드 완료 후 Layout Visual Spec 기반 시각적 검증을 수행합니다. (TCL #42)"
user_invocable: true
---

# /lvs-check — Layout Visual Spec 검증

## Usage
```
/lvs-check [project_path]
```

**Examples:**
- `/lvs-check`
- `/lvs-check E:\MRV`

## Purpose
빌드 완료 후 화면에 보이는 UI 요소들이 설계 스펙과 일치하는지 검증합니다 (TCL #42).
data-layout 속성, LAYOUT 상수, 상태별 제약 조건을 자동으로 체크합니다.

## Execution Steps

### Step 1. LAYOUT 상수 로드
프로젝트의 레이아웃 상수를 읽습니다:
- `src/packages/shared/constants/game.ts` 의 LAYOUT 객체
- `docs/decisions/ADR-012*.md` 등 관련 ADR

### Step 2. data-layout 태그 스캔
```bash
grep -r "data-layout" src/client/src/ --include="*.tsx"
```
모든 `data-layout` 속성이 태깅된 요소를 수집합니다.

### Step 3. UX Layer 문서 대조
`docs/planning/*_ux_layers.md` 에 정의된 LVS 항목과 실제 코드를 대조합니다:

| 검증 항목 | 방법 |
|-----------|------|
| 크기/위치 | LAYOUT 상수와 CSS 값 일치 여부 |
| 상태별 표시 | roundState에 따른 조건부 렌더링 확인 |
| 반응형 | viewport 범위 내 동작 확인 |
| 겹침/오버플로 | z-index, overflow 설정 확인 |

### Step 4. 불일치 리포트 생성
```markdown
## LVS Check Report

### ✅ PASS
| 요소 | 스펙 | 실제 | 결과 |
|------|------|------|------|
| NavRail | width: 40px | width: 40px | ✅ |

### ❌ FAIL
| 요소 | 스펙 | 실제 | 결과 |
|------|------|------|------|
| SidePanel | width: 160px | width: 210px | ❌ 불일치 |

### ⚠️ 미태깅 (data-layout 없음)
- {태깅되지 않은 주요 요소 목록}
```

### Step 5. 사용자에게 보고
PASS/FAIL 개수와 주요 불일치 항목을 요약 보고합니다.

## Hard Rules
- 이 스킬은 빌드 후, 종일군 테스트 전에 실행
- FAIL 항목이 있으면 빌드군에게 수정 요청
- 코드를 수정하지 않음 (검증만 수행)
