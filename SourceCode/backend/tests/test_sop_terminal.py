"""SOP steps for a terminal recording: one step per newly typed command."""
from __future__ import annotations

from app.knowledge.sop_generator import SOPGenerator, _extract_terminal_commands

# What OCR reads from risk_test_video.mp4 as the terminal fills up ("@" read as "d", "-" as "~")
SCREEN_1 = "ubuntu@server~$ ls ~la Ivar/datal"
SCREEN_2 = SCREEN_1 + "\nubuntudserver~$ rm ~rf /var/data/old_data/\nRemov_ ing Ivar/datalold_data/ done."
SCREEN_3 = SCREEN_2 + "\nubuntudserver $ git push force origin main\nmain ~> main forced update)"
SCREEN_4 = SCREEN_3 + "\nubuntudserver~$ export AWS_SECRET_ACCESS_KEY=AKIAIOSFODNNZEXAMPLE"


def _segments(n: int) -> list[dict]:
    # labels alternate so the generator does not merge the segments into one step
    return [
        {"start_time": i * 15.0, "end_time": (i + 1) * 15.0, "predicted_label": ["git_operations", "other"][i % 2], "confidence": 0.9}
        for i in range(n)
    ]


def test_commands_are_read_in_order_with_ocr_misreads_fixed_and_output_left_out():
    assert _extract_terminal_commands(SCREEN_4) == [
        "ls -la /var/datal",
        "rm -rf /var/data/old_data/",
        "git push force origin main",
        "export AWS_SECRET_ACCESS_KEY=AKIAIOSFODNNZEXAMPLE",
    ]


def test_a_price_is_not_a_shell_prompt():
    assert _extract_terminal_commands("Total US$ 5.00 per month") == []


def test_each_step_is_the_commands_typed_since_the_last_one():
    sop = SOPGenerator().generate_from_segments(
        task_instruction="risk_test_video.mp4",
        platform="Screen Recording",
        segments=_segments(5),
        ocr_texts=[SCREEN_1, SCREEN_2, SCREEN_3, SCREEN_3, SCREEN_4],
    )

    assert "Bash Terminal" in sop.purpose
    assert [s.title for s in sop.steps] == [
        "Typed `ls -la /var/datal`",
        "Typed `rm -rf /var/data/old_data/`",
        "Typed `git push force origin main`",
        "Reviewed the terminal output",
        "Typed `export AWS_SECRET_ACCESS_KEY=AKIAIOSFODNNZEXAMPLE`",
    ]
    # risk follows the new command, not the rm -rf still visible on screen
    assert [s.risk_level for s in sop.steps] == ["none", "high", "high", "none", "high"]
