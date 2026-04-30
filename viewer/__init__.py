"""TEMS Rule Viewer — 위상군 TEMS 규칙 모니터링 + 코멘트/제거 뷰어.

옵션 패키지. TEMS core 와 의존성 분리됨 — 이 디렉터리를 통째로 삭제해도
TEMS 작동에 영향 없음. 데이터 흐름: viewer → rule_user_annotations 테이블
+ user_annotations.jsonl 백업 → preflight_hook 가 LEFT JOIN 으로 읽음.
"""

__version__ = "0.1.0"
