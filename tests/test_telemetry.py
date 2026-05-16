"""Tests para pdf2md.telemetry (T085) — smoke + peak detection."""
import json
import time
from pathlib import Path

from pdf2md.telemetry import StepMetrics, TelemetryRun, detect_host


# ----------------------------------------------------------------------------
# Host
# ----------------------------------------------------------------------------

def test_detect_host_has_required_fields():
    h = detect_host()
    for key in ("platform", "python", "cpu_count_logical", "ram_total_gb", "pid"):
        assert key in h
    assert isinstance(h["pid"], int) and h["pid"] > 0
    # gpu pode ser None (sem CUDA) ou dict — sempre deve estar presente
    assert "gpu" in h


# ----------------------------------------------------------------------------
# TelemetryRun básico
# ----------------------------------------------------------------------------

def test_run_no_steps_records_wall_only(tmp_path: Path):
    out = tmp_path / "tel.json"
    with TelemetryRun("smoke", output_path=out, sample_interval_s=0.1) as run:
        time.sleep(0.05)
    assert run.steps == []
    assert run.total_wall_s >= 0.05
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["run_id"] == "smoke"
    assert data["steps"] == []
    assert data["total_wall_s"] >= 0.05


def test_run_single_step_captures_wall(tmp_path: Path):
    out = tmp_path / "tel.json"
    with TelemetryRun("one-step", output_path=out, sample_interval_s=0.1) as run:
        with run.step("sleep_short"):
            time.sleep(0.15)
    assert len(run.steps) == 1
    s = run.steps[0]
    assert s.name == "sleep_short"
    assert 0.10 < s.wall_s < 1.0  # com margem
    assert s.rss_start_mb > 0
    assert s.rss_peak_mb >= s.rss_start_mb
    assert s.threads_peak >= 1


def test_run_nested_steps_sequential(tmp_path: Path):
    """Steps em sequência devem aparecer na ordem de execução."""
    with TelemetryRun("multi", sample_interval_s=0.1) as run:
        with run.step("a"):
            time.sleep(0.02)
        with run.step("b"):
            time.sleep(0.02)
        with run.step("c"):
            time.sleep(0.02)
    assert [s.name for s in run.steps] == ["a", "b", "c"]


def test_run_step_captures_python_heap_growth():
    """Alocar buffer grande aumenta py_peak_mb mensuravelmente."""
    with TelemetryRun("heap-test", sample_interval_s=0.1) as run:
        with run.step("alloc_buffer"):
            buf = bytearray(20 * 1024 * 1024)  # 20MB
            assert len(buf) == 20 * 1024 * 1024
            del buf
    s = run.steps[0]
    # py_peak deve refletir pelo menos parte da alocação
    assert s.py_peak_mb is not None
    assert s.py_peak_mb >= 10.0  # margem (gc, fragmentação, etc.)


def test_run_step_error_is_recorded():
    """Exception dentro do step grava mensagem e re-levanta."""
    run = TelemetryRun("err-test", sample_interval_s=0.1)
    with run:
        try:
            with run.step("will_fail"):
                raise ValueError("boom")
        except ValueError:
            pass
    assert len(run.steps) == 1
    assert run.steps[0].error is not None
    assert "ValueError" in run.steps[0].error
    assert "boom" in run.steps[0].error


def test_run_save_requires_output_path(tmp_path: Path):
    """save() sem output_path levanta ValueError."""
    import pytest
    run = TelemetryRun("no-path")
    run._t_start = time.perf_counter()  # simula __enter__
    with pytest.raises(ValueError, match="output_path"):
        run.save()


def test_run_to_dict_is_serializable():
    """to_dict retorna estrutura JSON-friendly."""
    with TelemetryRun("dict-test", sample_interval_s=0.1) as run:
        with run.step("x"):
            time.sleep(0.01)
    d = run.to_dict()
    # round-trip JSON
    s = json.dumps(d)
    d2 = json.loads(s)
    assert d2["run_id"] == "dict-test"
    assert len(d2["steps"]) == 1


def test_step_metrics_dataclass_defaults():
    """StepMetrics inicializa com defaults sensatos."""
    m = StepMetrics(name="x")
    assert m.name == "x"
    assert m.wall_s == 0.0
    assert m.error is None
    assert m.py_peak_mb is None  # opcional
    assert m.gpu_vram_peak_mb is None  # opcional sem GPU
