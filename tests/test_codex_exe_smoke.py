"""codex-exe wrapper smoke test (S53).

본 파일은 codex GPT-5.5 가 wrapper 를 통해 실제 파일 생성에 성공했음을
사후 입증하는 single-assertion smoke test.
"""


def test_codex_exe_round_trip_marker() -> None:
    """codex 가 본 파일을 생성했다는 사실 자체가 wrapper round-trip 성공의 증거."""
    marker = "codex_exec_v1_round_trip"
    assert marker == "codex_exec_v1_round_trip"
