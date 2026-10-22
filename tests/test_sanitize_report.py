"""tools/sanitize_report.py places a nightly crash and leads with the sanitizer's report.

On 2026-10-22 an x86 shard aborted (rc=134) with no report and no test named: ASan wrote
to fd 2, which pytest had captured into a temporary file, and the -q log named no test, so
the gdb re-run had nothing to run. The tool is run as a program, as the workflow runs it.
"""
import subprocess
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[1] / "tools" / "sanitize_report.py"
if not TOOL.exists():
    pytest.skip("tools/ is not shipped here", allow_module_level=True)

VERBOSE_LOG = """\
tests/test_a.py::test_one PASSED                                         [ 10%]
tests/test_a.py::test_two[256-cpu] SKIPPED (no GPU)                      [ 11%]
tests/test_b.py::test_three[512] FAILED                                  [ 12%]
tests/test_b.py::test_four[1024-x] tools/sanitize.sh: line 121:  2503 Aborted (core dumped)
=== sanitizer report asan.2503 ===
==2503==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x6020 at pc 0x7f
    #0 0x7f in ap_example src/kernel.cc:10
sanitize: pytest rc=134 (FAILED)
"""


def run(*args, log):
    return subprocess.run([sys.executable, str(TOOL), *args, str(log)], capture_output=True,
                          text=True)


def test_crashing_test_is_the_last_started_test_without_an_outcome(tmp_path):
    log = tmp_path / "san.log"
    log.write_text(VERBOSE_LOG)
    out = run("--crashing-test", log=log)
    assert out.returncode == 0
    assert out.stdout.strip() == "tests/test_b.py::test_four[1024-x]"


def test_a_completed_run_names_no_crashing_test(tmp_path):
    log = tmp_path / "san.log"
    log.write_text(VERBOSE_LOG.split("tests/test_b.py::test_four")[0])
    out = run("--crashing-test", log=log)
    assert out.returncode == 1 and out.stdout.strip() == ""


def test_faulthandler_frame_wins_over_the_verbose_line(tmp_path):
    log = tmp_path / "san.log"
    log.write_text(VERBOSE_LOG + 'Fatal Python error: Aborted\n'
                   '  File "/w/tests/test_c.py", line 5 in test_five\n')
    out = run("--crashing-test", log=log)
    assert out.stdout.strip() == "tests/test_c.py::test_five"


def test_annotation_leads_with_the_asan_report(tmp_path):
    log = tmp_path / "san.log"
    log.write_text(VERBOSE_LOG)
    out = subprocess.run([sys.executable, str(TOOL), str(log), "134"], capture_output=True,
                         text=True)
    body = out.stdout.replace("%0A", "\n")
    assert body.startswith("::error::rc=134")
    head = body.split("-- end of log --")[0]
    assert "heap-buffer-overflow" in head and "ap_example src/kernel.cc:10" in head


def test_annotation_names_the_test_drops_interpreter_frames_and_keeps_gdb(tmp_path):
    frames = "".join("    #%d 0x7f in _PyEval_EvalFrameDefault Python/bytecodes.c:2715\n" % i
                     for i in range(2, 60))
    log = tmp_path / "san.log"
    log.write_text(VERBOSE_LOG.replace("    #0 0x7f in ap_example src/kernel.cc:10\n",
                                       "    #0 0x7f in ap_example src/kernel.cc:10\n"
                                       "    #1 0x7f in MF_run python/matchedfilter/_core.c:5\n"
                                       + frames)
                   + "=== gdb: tests/test_b.py::test_four[1024-x] ===\n"
                   "Thread 1 received signal SIGSEGV\n#0  0x7f in ap::N_AVX3::fft ()\n"
                   "r15            0x7ffd6b464e90\n")
    out = subprocess.run([sys.executable, str(TOOL), str(log), "134"], capture_output=True,
                         text=True)
    head = out.stdout.replace("%0A", "\n").split("-- end of log --")[0]
    assert "crashing test: tests/test_b.py::test_four[1024-x]" in head
    assert "MF_run python/matchedfilter/_core.c:5" in head
    assert "bytecodes.c" not in head
    assert "r15            0x7ffd6b464e90" in head


def test_annotation_carries_the_rerun_without_the_fake_stack(tmp_path):
    log = tmp_path / "san.log"
    log.write_text(VERBOSE_LOG + "=== without use-after-return detection: rc=0 ===\n")
    out = subprocess.run([sys.executable, str(TOOL), str(log), "134"], capture_output=True,
                         text=True)
    head = out.stdout.replace("%0A", "\n").split("-- end of log --")[0]
    assert "=== without use-after-return detection: rc=0 ===" in head
