# GCE: Gaussian Context Encoding
## Compressing LLM Context via 3D Gaussian Splatting Principles

**Authors:** Triad Chord Studio (종일군, 위상군)
**Date:** 2026-03-23
**Status:** Research Proposal — Pre-PoC

---

## 1. Abstract

대형 언어 모델(LLM)의 컨텍스트 윈도우는 유한하며, 긴 프롬프트는 O(n²) 어텐션 연산과 선형적 KV 캐시 증가를 유발한다. 기존 프롬프트 압축 연구(LLMLingua, Gist Tokens, DAST)는 토큰 제거 또는 학습된 이산 벡터 방식에 의존하지만, 정보의 **연속적 분포 구조**를 활용하지 못한다.

본 연구는 3D Gaussian Splatting(3DGS)의 핵심 원리 — **가우시안 피팅, 불투명도 기반 가지치기, LoD(Level of Detail), HAC++ 압축** — 을 LLM 컨텍스트 압축에 적용하는 **GCE(Gaussian Context Encoding)** 프레임워크를 제안한다.

핵심 아이디어: 토큰은 임베딩 공간의 **점(point)**이지만, 가우시안은 **확률 분포(distribution)**이다. 하나의 가우시안이 의미적으로 유사한 토큰 클러스터 전체를 덮을 수 있으므로, N개 토큰을 M개 가우시안(M << N)으로 표현하여 극단적 압축을 달성한다.

**기대 효과:** 텍스트 대비 100~1000x 컨텍스트 압축, O(n²) → O(m²) 어텐션 연산 감소, 사용자 맞춤형 컨텍스트 개인화.

---

## 2. Motivation & Problem Statement

### 2.1 문제: LLM 컨텍스트의 근본적 병목

```
사용자 → 텍스트 프롬프트 → 토크나이저 → 정수 시퀀스 → 임베딩 벡터열 → 트랜스포머

                                    ↑ 여기서 정보 밀도가 매우 낮다

"세션 종료 시 핸드오버 문서를 작성하세요" = 12토큰
  → 12개 벡터가 컨텍스트를 점유
  → 핵심 의미는 {세션종료, 핸드오버, 작성} 3개 개념
  → 9/12 = 75%가 구문적 접착제(조사, 어미, 구두점)
```

| 병목 | 원인 | 영향 |
|------|------|------|
| 컨텍스트 윈도우 포화 | 자연어의 낮은 정보 밀도 | 규칙 100건만으로도 8K 윈도우 소진 |
| 어텐션 O(n²) | 모든 토큰이 서로 어텐션 | 프롬프트 길이 2배 → 연산 4배 |
| KV 캐시 O(n) | 토큰당 캐시 엔트리 | VRAM 선형 증가 → 배치 크기 제한 |

### 2.2 기존 접근의 한계

| 방법 | 압축률 | 한계 |
|------|--------|------|
| **LLMLingua** (Microsoft, 2024) | ~20x | 토큰 제거 방식 — 정보 손실 불가피 |
| **Gist Tokens** (Mu et al., 2023) | ~26x | 이산 벡터 — 의미 범위(Σ) 표현 불가 |
| **DAST** (ACL 2025) | ~15x | 동적 토큰 할당 — 여전히 이산적 |
| **KV-Distill** (2025) | ~4x | 캐시만 압축, 입력은 그대로 |

**공통 한계:** 모두 토큰을 "점(point)"으로 취급. 의미의 **범위, 방향, 중요도**를 하나의 표현에 통합하지 못함.

### 2.3 영감: 3DGS는 어떻게 장면을 압축하는가?

3D Gaussian Splatting은 수백만 개의 3D 점(point cloud)을 수만 개의 가우시안으로 대체하여:

```
NeRF:    수백만 레이 샘플 → 느린 볼륨 렌더링
3DGS:    수만 가우시안 → 실시간 스플랫 렌더링 (100x 빠름)
```

**동일 원리를 텍스트에 적용하면:**

```
기존 LLM:   수만 토큰 → 느린 어텐션 연산
GCE:        수백 가우시안 → 빠른 어텐션 연산 (100x 압축)
```

---

## 3. Core Idea: Gaussian Context Encoding

### 3.1 토큰 → 가우시안 변환

표준 LLM 입력:
```
x = [e₁, e₂, ..., eₙ]   where eᵢ ∈ ℝᵈ (토큰 임베딩, d=4096)
```

GCE 인코딩:
```
G = {G₁, G₂, ..., Gₘ}   where m << n

각 가우시안 Gⱼ = (μⱼ, Σⱼ, αⱼ, fⱼ):
  μⱼ ∈ ℝᵈ         — 의미 중심 (position in embedding space)
  Σⱼ ∈ ℝᵈˣᵏ       — 의미 범위/방향 (low-rank covariance, k << d)
  αⱼ ∈ [0, 1]     — 중요도/확신도 (opacity)
  fⱼ ∈ ℝˢ          — 부가 특징 (SH-like feature coefficients)
```

### 3.2 3DGS → GCE 대응 관계

| 3DGS (3D 장면) | GCE (LLM 컨텍스트) |
|----------------|-------------------|
| 3D 공간 좌표 | d차원 임베딩 공간 |
| 가우시안 위치 (μ) | 개념의 의미적 중심 |
| 공분산 (Σ) | 의미의 범위와 방향 (넓으면 일반적, 좁으면 구체적) |
| 불투명도 (α) | 개념의 중요도 / 현재 관련성 |
| SH 계수 | 다각도 의미 표현 (문맥에 따라 다른 뉘앙스) |
| 카메라 시점 | 현재 사용자 쿼리/프롬프트 |
| 렌더링 | 가우시안 → LLM 입력 벡터 생성 |
| LoD | 쿼리 관련도에 따른 동적 해상도 조절 |
| 가지치기 (pruning) | α < 임계값인 가우시안 제거 |
| 고밀도화 (densification) | 커버리지 부족 영역에 가우시안 추가 |
| HAC++ 압축 | 앵커-해시그리드로 가우시안 파라미터 극한 압축 |

### 3.3 스플랫팅: 가우시안 → LLM 입력 변환

3DGS에서 카메라 방향으로 가우시안을 "스플랫"하여 2D 이미지를 만들듯이, GCE에서는 **현재 쿼리 방향**으로 가우시안을 "스플랫"하여 LLM 입력 벡터열을 생성한다.

```
입력: 쿼리 q, 가우시안 집합 G = {G₁, ..., Gₘ}

1. 관련도 계산:
   rⱼ = αⱼ · exp(-½ (q - μⱼ)ᵀ Σⱼ⁻¹ (q - μⱼ))
   → 쿼리에 가까운 가우시안은 높은 관련도

2. 정렬 & 선택 (LoD):
   상위 K개 가우시안만 선택 (K = 컨텍스트 버짓)

3. 스플래팅 (벡터 생성):
   각 선택된 가우시안에서 LLM 입력 벡터를 생성:
   vⱼ = μⱼ + Σⱼ · fⱼ   (중심 + 방향성 특징)

4. LLM 입력:
   inputs_embeds = [v₁, v₂, ..., vₖ, q_embed₁, q_embed₂, ...]
                   ↑ 압축된 컨텍스트    ↑ 원본 쿼리
```

### 3.4 학습: 가우시안 최적화

3DGS가 이미지 재구성 손실로 가우시안을 최적화하듯, GCE는 **LLM 응답 품질 손실**로 가우시안을 최적화한다.

```
L_total = L_response + λ₁·L_reconstruct + λ₂·L_sparsity

L_response:     압축된 입력으로 생성한 응답 vs 원본 입력 응답의 KL divergence
L_reconstruct:  가우시안에서 원본 토큰 임베딩을 복원할 수 있는가 (정보 보존)
L_sparsity:     가우시안 수를 최소화하는 정규화 (|{j : αⱼ > ε}|)
```

**적응적 가우시안 제어 (3DGS의 Adaptive Density Control 차용):**
- **분할 (Split):** 그래디언트가 큰 가우시안 → 의미가 너무 넓음 → 2개로 분할
- **복제 (Clone):** 재구성 에러가 큰 영역 → 커버리지 부족 → 가우시안 추가
- **제거 (Prune):** α < ε인 가우시안 → 불필요 → 제거

---

## 4. Hypotheses

### H1: 정보 밀도 가설
> 가우시안 1개는 파라미터 수 기준으로 토큰 ~5개에 해당하지만, 의미적으로 토큰 ~20개의 정보를 인코딩할 수 있다. 따라서 **순 정보 효율은 ~4x**이다.

**검증:** 고정된 파라미터 버짓에서 가우시안 vs 동일 수의 soft prompt 토큰의 응답 품질 비교.

### H2: LoD 효율 가설
> 3DGS의 LoD와 동일하게, 쿼리와 먼 가우시안은 스킵함으로써 **필요한 컨텍스트만 동적으로 로드**할 수 있다. 이는 전체 컨텍스트를 항상 입력하는 기존 방식 대비 불필요한 연산을 제거한다.

**검증:** 다양한 쿼리에 대해 활성화되는 가우시안 비율 측정. 전체의 20-30%만 활성화되면서도 90%+ 정확도를 유지하는가?

### H3: HAC++ 극한 압축 가설
> 3DGS에서 HAC++가 100x 압축을 달성한 것처럼, 임베딩 공간에서도 앵커-해시 그리드 구조로 가우시안 파라미터를 **추가 10x 압축**할 수 있다. 기본 가우시안 압축(~100x) × HAC++(~10x) = 이론적 **~1000x 총 압축**.

**검증:** HAC++ 적용 전후의 응답 품질(BLEU, ROUGE, 정확도) 비교.

### H4: 개인화 가설
> 특정 사용자의 과거 프롬프트로 가우시안을 학습하면, 해당 사용자의 관심사/어휘/패턴에 최적화된 **개인화된 컨텍스트 압축**이 가능하다. 범용 압축 대비 동일 압축률에서 더 높은 정확도를 달성한다.

**검증:** 사용자 A의 데이터로 학습 → 사용자 A 쿼리 정확도 vs 범용 모델 정확도 비교.

---

## 5. Experimental Methodology

### 5.1 실험 환경

| 항목 | 사양 |
|------|------|
| GPU | NVIDIA RTX 4090 (24GB VRAM) |
| 기반 LLM | Qwen2.5-7B-Instruct (FP16, ~14GB) |
| 여유 VRAM | ~10GB (학습/추론용) |
| 프레임워크 | PyTorch 2.x + HuggingFace Transformers |
| 3DGS 참조 | gsplat / nerfstudio (최적화 루프 차용) |
| 비교 베이스라인 | Gist Tokens, LLMLingua-2, DAST, Soft Prompt |

### 5.2 실험 단계

#### Phase 0: 베이스라인 구축 (1주)

원본 텍스트 프롬프트 대비 기존 압축 방법들의 성능 기준선 설정.

```
태스크:
  T1: 규칙 준수 (TEMS 규칙 N건 → 주어진 상황에서 올바른 행동 선택)
  T2: QA (압축된 문서 기반 질문 응답)
  T3: 요약 (압축된 컨텍스트 기반 요약 생성)

메트릭:
  M1: 정확도 (rule compliance accuracy, QA exact match)
  M2: ROUGE-L (요약 품질)
  M3: 컨텍스트 토큰 수 (압축률)
  M4: TTFT (Time to First Token, 응답 속도)
  M5: VRAM 사용량 (KV 캐시 포함)
```

#### Phase 1: 단순 가우시안 피팅 (2주)

토큰 임베딩을 K-means → 가우시안 피팅하는 가장 단순한 접근.

```python
# 의사 코드
token_embeddings = embed(tokenizer(rules_text))     # (N, d)
clusters = kmeans(token_embeddings, n_clusters=M)    # M개 클러스터
gaussians = fit_gaussians(token_embeddings, clusters) # M개 가우시안(μ, Σ, α)
compressed = splat(gaussians, query_embedding)        # LLM 입력 생성
output = model(inputs_embeds=compressed)              # 추론
```

**변수:** M = {N/2, N/5, N/10, N/20, N/50}으로 압축률 변화에 따른 정확도 곡선 측정.

#### Phase 2: 미분 가능 가우시안 최적화 (3주)

3DGS와 동일한 미분 가능 파이프라인으로 가우시안을 end-to-end 학습.

```python
# 학습 루프 (3DGS 최적화와 동일 구조)
gaussians = init_gaussians(token_embeddings, M)

for step in range(num_steps):
    # Forward: 가우시안 → LLM 입력
    compressed = differentiable_splat(gaussians, query)
    output = model(inputs_embeds=compressed)

    # Loss
    loss = kl_div(output, reference_output) + λ * sparsity(gaussians)

    # Backward: 가우시안 파라미터 업데이트
    loss.backward()
    optimizer.step()

    # Adaptive Density Control (매 100 step)
    if step % 100 == 0:
        split_large_gaussians(gaussians)
        clone_underrepresented(gaussians)
        prune_low_opacity(gaussians, threshold=0.01)
```

#### Phase 3: LoD 동적 선택 (2주)

쿼리에 따라 관련 가우시안만 선택하는 LoD 메커니즘 구현.

```
쿼리 "세션을 종료합니다" → 관련도 계산:
  G₁(세션관리):  r=0.92  → 선택 ✓
  G₂(에러처리):  r=0.15  → 스킵 ✗
  G₃(문서작성):  r=0.78  → 선택 ✓
  G₄(3DGS):     r=0.03  → 스킵 ✗

→ 4개 중 2개만 입력 → 50% 추가 절감
```

#### Phase 4: HAC++ 파라미터 압축 (2주)

가우시안 자체의 파라미터를 HAC++ 방식으로 압축.

```
가우시안 50개 × (μ: 4096 + Σ: 4096×4 + α: 1 + f: 256)
= 50 × 20,737 ≈ 1M 파라미터

HAC++ 적용:
  앵커 5개 + 해시 그리드 참조
  = 5 × 20,737 + 해시 테이블 ~50K
  ≈ 150K 파라미터 (6.7x 추가 압축)
```

#### Phase 5: 개인화 실험 (2주)

특정 사용자의 과거 프롬프트로 가우시안을 사전 학습.

```
학습 데이터: 사용자의 과거 대화 1000건
  → 빈출 개념 추출
  → 개인화된 가우시안 분포 학습
  → 해당 사용자의 새 쿼리에 대해 정확도/압축률 측정
```

### 5.3 비교 실험 설계

| 방법 | 입력 형태 | 압축 메커니즘 |
|------|-----------|-------------|
| **Original** (상한) | 원본 텍스트 토큰 | 없음 |
| **LLMLingua-2** | 토큰 부분집합 | 토큰 제거 |
| **Gist Tokens** | 학습된 이산 벡터 | 벡터 학습 |
| **Soft Prompt** | 학습된 연속 벡터 | 프롬프트 튜닝 |
| **GCE-basic** (Phase 1) | K-means 가우시안 | 클러스터링 |
| **GCE-opt** (Phase 2) | 최적화된 가우시안 | 미분 가능 스플랫팅 |
| **GCE-LoD** (Phase 3) | 동적 선택 가우시안 | LoD |
| **GCE-HAC** (Phase 4) | 압축된 가우시안 | HAC++ |
| **GCE-personal** (Phase 5) | 개인화 가우시안 | 사용자 사전 학습 |

### 5.4 예상 결과

| 방법 | 압축률 | 정확도 (상대) | TTFT 개선 |
|------|--------|-------------|-----------|
| Original | 1x | 100% | 기준 |
| LLMLingua-2 | 20x | ~85% | ~4x |
| Gist Tokens | 26x | ~80% | ~5x |
| **GCE-basic** | 10-20x | ~75% | ~3x |
| **GCE-opt** | 50-100x | ~85% | ~8x |
| **GCE-LoD** | 100-200x | ~83% | ~10x |
| **GCE-HAC** | 500-1000x | ~78% | ~15x |
| **GCE-personal** | 100x | ~90% | ~10x |

---

## 6. Key Contributions (예상)

1. **개념적 기여:** 3DGS의 렌더링 원리를 LLM 컨텍스트 관리에 역방향 적용하는 최초의 프레임워크 — 3D 비전과 NLP의 새로운 교차점.

2. **기술적 기여:** 토큰을 가우시안(μ, Σ, α, f)으로 파라미터화하고 미분 가능 스플랫팅으로 end-to-end 학습하는 파이프라인.

3. **실용적 기여:** 극단적 컨텍스트 압축(100-1000x)으로 LLM 추론 비용을 근본적으로 절감하고, LoD 기반 동적 선택으로 컨텍스트를 쿼리에 맞게 자동 조절.

4. **개인화 기여:** 사용자별 가우시안 분포 학습을 통한 맞춤형 컨텍스트 압축 — 같은 압축률에서 범용 방법 대비 높은 정확도.

---

## 7. Risks & Mitigations

| 리스크 | 영향 | 대응 |
|--------|------|------|
| LLM 어텐션이 가우시안 입력을 잘 처리 못함 | 정확도 하락 | 가우시안 → 토큰 변환 어댑터 레이어 추가 |
| 가우시안 최적화가 수렴하지 않음 | 학습 실패 | Phase 1의 K-means 초기화로 안정화 |
| 한국어 특화 문제 (형태소 복잡성) | 압축률 저하 | 형태소 단위 대신 의미 단위 클러스터링 |
| VRAM 부족 (4090 24GB) | 실험 제약 | 그래디언트 체크포인팅 + 양자화(QLoRA) |
| 기존 방법 대비 이점 미미 | 논문 가치 하락 | Phase별 점진적 개선으로 최소 기여 보장 |

---

## 8. Timeline

| 주차 | 작업 | 마일스톤 |
|------|------|----------|
| W1-2 | Phase 0: 베이스라인 + 인프라 | 비교 실험 프레임워크 구축 |
| W3-4 | Phase 1: 단순 가우시안 피팅 | 최초 GCE 동작 확인 |
| W5-7 | Phase 2: 미분 가능 최적화 | 핵심 결과 — 압축률 vs 정확도 곡선 |
| W8-9 | Phase 3: LoD 동적 선택 | 연산 효율 개선 검증 |
| W10-11 | Phase 4: HAC++ 극한 압축 | 최대 압축률 달성 |
| W12-13 | Phase 5: 개인화 | 사용자 맞춤 압축 검증 |
| W14-16 | 논문 작성 + 추가 실험 | 논문 초안 완성 |

**타깃 학회:** NeurIPS 2026 (제출 마감: ~2026년 5월) 또는 ICLR 2027

---

## 9. Related Work

### 9.1 Prompt/Context Compression
- LLMLingua / LLMLingua-2 (Microsoft, 2024) — 토큰 분류 기반 하드 압축
- Gist Tokens (Mu et al., 2023) — 학습된 gist 토큰
- DAST (ACL 2025) — 동적 소프트 토큰 할당
- CompactPrompt (2025) — 자기 정보 기반 구절 그룹화

### 9.2 Gaussian Representations in NLP
- Word2Gauss (Vilnis & McCallum, ICLR 2015) — 단어를 가우시안 분포로 표현
- Gaussian Transformer (AAAI) — 어텐션에 가우시안 거리 바이어스

### 9.3 3DGS Compression
- HAC / HAC++ — 앵커-해시 그리드 기반 100x 압축
- EGGS — 2D/3D 가우시안 하이브리드
- Voyager — 시간 인지 LoD

### 9.4 Cross-Domain GS Applications
- GaussianVision (2025) — 2DGS로 비전-언어 입력 23.5x 압축
- GSVC (2025) — GS 기반 비디오 압축

---

## 10. Repository Structure (예정)

```
GCE/
├── README.md
├── docs/
│   └── research_proposal.md      ← 본 문서
├── src/
│   ├── gaussian.py               # 가우시안 파라미터화 (μ, Σ, α, f)
│   ├── splat.py                  # 미분 가능 스플랫팅
│   ├── encoder.py                # 토큰 → 가우시안 인코더
│   ├── decoder.py                # 가우시안 → LLM 입력 디코더
│   ├── lod.py                    # LoD 동적 선택
│   ├── hac_compress.py           # HAC++ 스타일 가우시안 압축
│   └── trainer.py                # end-to-end 학습 루프
├── baselines/
│   ├── gist_tokens.py
│   ├── llmlingua.py
│   └── soft_prompt.py
├── experiments/
│   ├── phase0_baseline.py
│   ├── phase1_kmeans.py
│   ├── phase2_diffable.py
│   ├── phase3_lod.py
│   ├── phase4_hac.py
│   └── phase5_personal.py
├── data/
│   └── tems_rules.json           # TEMS 규칙 데이터 (실험용)
└── results/
    └── ...
```

---

*"토큰은 점이고, 가우시안은 구름이다. 같은 하늘을 더 적은 구름으로 덮을 수 있다."*

— Triad Chord Studio, 2026
