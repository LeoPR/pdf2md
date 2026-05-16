"""Telemetria por step do pipeline — instrumento (T085).

Captura wall-time, CPU time + %, memória RSS, Python heap, GPU VRAM +
util%, I/O e threads em context managers aninhados. Sampling em thread
separada (overhead < 1% validado em e10).

Uso típico:

    from pdf2md.telemetry import TelemetryRun

    with TelemetryRun("run-name", output_path=Path("out/telemetry.json")) as run:
        with run.step("extract"):
            ...
        with run.step("optimize"):
            ...

Output JSON em `output_path` no exit. Sem dependência de torch — degrada
graceful em máquinas sem GPU (`gpu = None`).

Promovido de `lab/e10_pixel_roundtrip_fingerprint/telemetry.py` (validado
overhead < 1% wall-time, captura cleanly 6 steps com perfis distintos).
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import threading
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import psutil


DEFAULT_SAMPLE_INTERVAL_S = 0.5


# ----------------------------------------------------------------------------
# Host info — capturado uma vez por run
# ----------------------------------------------------------------------------

def detect_host() -> dict:
    """Detecta CPU/RAM/GPU/Python/OS. Sem deps obrigatórias."""
    out: dict[str, Any] = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 1),
        "pid": os.getpid(),
    }
    try:
        out["cpu_model"] = platform.processor()
    except Exception:
        out["cpu_model"] = "unknown"
    out["gpu"] = _detect_gpu()
    return out


def _detect_gpu() -> dict | None:
    """Retorna info da GPU via nvidia-smi, ou None se ausente."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return None
        line = r.stdout.strip().splitlines()[0]
        parts = [p.strip() for p in line.split(",")]
        return {
            "name": parts[0],
            "vram_total_mb": int(parts[1]),
            "driver": parts[2] if len(parts) > 2 else "?",
        }
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        return None


# ----------------------------------------------------------------------------
# Step metrics
# ----------------------------------------------------------------------------

@dataclass
class StepMetrics:
    """Métricas capturadas para um step do pipeline."""
    name: str
    wall_s: float = 0.0
    cpu_s: float = 0.0
    cpu_pct_mean: float = 0.0
    cpu_pct_peak: float = 0.0
    rss_start_mb: float = 0.0
    rss_peak_mb: float = 0.0
    rss_delta_mb: float = 0.0
    py_peak_mb: float | None = None
    gpu_vram_start_mb: float | None = None
    gpu_vram_peak_mb: float | None = None
    gpu_vram_delta_mb: float | None = None
    gpu_util_pct_mean: float | None = None
    io_read_mb: float = 0.0
    io_write_mb: float = 0.0
    threads_peak: int = 0
    error: str | None = None


class _Sampler(threading.Thread):
    """Thread daemon que amostra recursos do processo periodicamente."""

    def __init__(self, proc: psutil.Process, has_gpu: bool, interval_s: float):
        super().__init__(daemon=True)
        self.proc = proc
        self.has_gpu = has_gpu
        self.interval_s = interval_s
        self.stop_evt = threading.Event()
        self.samples_cpu: list[float] = []
        self.samples_rss: list[float] = []
        self.samples_threads: list[int] = []
        self.samples_gpu_util: list[float] = []
        self.samples_gpu_vram: list[float] = []

    def run(self) -> None:
        while not self.stop_evt.is_set():
            try:
                self.samples_cpu.append(self.proc.cpu_percent(interval=None))
                self.samples_rss.append(self.proc.memory_info().rss / (1024 ** 2))
                self.samples_threads.append(self.proc.num_threads())
                if self.has_gpu:
                    g = self._poll_gpu()
                    if g is not None:
                        self.samples_gpu_util.append(g[0])
                        self.samples_gpu_vram.append(g[1])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            self.stop_evt.wait(self.interval_s)

    @staticmethod
    def _poll_gpu() -> tuple[float, float] | None:
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2,
            )
            if r.returncode != 0:
                return None
            line = r.stdout.strip().splitlines()[0]
            util, mem = [float(x.strip()) for x in line.split(",")]
            return util, mem
        except Exception:
            return None


# ----------------------------------------------------------------------------
# TelemetryRun
# ----------------------------------------------------------------------------

@dataclass
class TelemetryRun:
    """Container de um run inteiro com múltiplos steps.

    Args:
        run_id: identificador legível do run.
        output_path: onde gravar telemetria final (default: None → não grava).
        sample_interval_s: período de sampling em segundos (default 0.5).
        capture_host: se True (default), detecta info da máquina no init.
    """
    run_id: str
    output_path: Path | None = None
    sample_interval_s: float = DEFAULT_SAMPLE_INTERVAL_S
    capture_host: bool = True
    host: dict = field(default_factory=dict)
    steps: list[StepMetrics] = field(default_factory=list)
    total_wall_s: float = 0.0
    _t_start: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        if self.capture_host and not self.host:
            self.host = detect_host()

    def __enter__(self):
        self._t_start = time.perf_counter()
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.total_wall_s = time.perf_counter() - self._t_start
        if self.output_path:
            self.save()
        return False

    @contextmanager
    def step(self, name: str):
        """Context manager para instrumentar um step específico.

        Yields o `StepMetrics` em construção — pode anotar campos custom
        antes do exit se quiser.
        """
        proc = psutil.Process(os.getpid())
        has_gpu = self.host.get("gpu") is not None

        m = StepMetrics(name=name)
        m.rss_start_mb = proc.memory_info().rss / (1024 ** 2)
        m.rss_peak_mb = m.rss_start_mb
        io_start = _safe_io(proc)
        cpu_start = proc.cpu_times()
        proc.cpu_percent(interval=None)  # warm up

        if has_gpu:
            g0 = _Sampler._poll_gpu()
            if g0 is not None:
                m.gpu_vram_start_mb = g0[1]
            _reset_torch_peak()

        tracemalloc.clear_traces()

        sampler = _Sampler(proc, has_gpu=has_gpu, interval_s=self.sample_interval_s)
        sampler.start()

        t0 = time.perf_counter()
        try:
            yield m
        except Exception as e:
            m.error = f"{type(e).__name__}: {e}"
            raise
        finally:
            m.wall_s = time.perf_counter() - t0
            sampler.stop_evt.set()
            sampler.join(timeout=2.0)

            cpu_end = proc.cpu_times()
            m.cpu_s = (cpu_end.user + cpu_end.system) - (cpu_start.user + cpu_start.system)

            if sampler.samples_cpu:
                m.cpu_pct_mean = sum(sampler.samples_cpu) / len(sampler.samples_cpu)
                m.cpu_pct_peak = max(sampler.samples_cpu)
            if sampler.samples_rss:
                m.rss_peak_mb = max(sampler.samples_rss + [m.rss_peak_mb])
            m.rss_delta_mb = m.rss_peak_mb - m.rss_start_mb
            if sampler.samples_threads:
                m.threads_peak = max(sampler.samples_threads)
            if sampler.samples_gpu_util:
                m.gpu_util_pct_mean = sum(sampler.samples_gpu_util) / len(sampler.samples_gpu_util)
            if sampler.samples_gpu_vram:
                m.gpu_vram_peak_mb = max(sampler.samples_gpu_vram)
                if m.gpu_vram_start_mb is not None:
                    m.gpu_vram_delta_mb = m.gpu_vram_peak_mb - m.gpu_vram_start_mb

            py_now, py_peak = tracemalloc.get_traced_memory()
            m.py_peak_mb = py_peak / (1024 ** 2)

            io_end = _safe_io(proc)
            if io_start and io_end:
                m.io_read_mb = max(0, (io_end.read_bytes - io_start.read_bytes) / (1024 ** 2))
                m.io_write_mb = max(0, (io_end.write_bytes - io_start.write_bytes) / (1024 ** 2))

            self.steps.append(m)

    def save(self) -> Path:
        """Grava JSON serializável em self.output_path. Raise se output_path None."""
        if self.output_path is None:
            raise ValueError("output_path não definido — passe no construtor ou atribua antes de save()")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "run_id": self.run_id,
            "host": self.host,
            "total_wall_s": round(self.total_wall_s, 3),
            "steps": [_round_floats(asdict(s)) for s in self.steps],
        }
        self.output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return self.output_path

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "host": self.host,
            "total_wall_s": round(self.total_wall_s, 3),
            "steps": [_round_floats(asdict(s)) for s in self.steps],
        }


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _safe_io(proc: psutil.Process):
    """psutil.io_counters falha em alguns processos no Windows; trata gracefully."""
    try:
        return proc.io_counters()
    except (psutil.AccessDenied, AttributeError):
        return None


def _reset_torch_peak() -> None:
    """Reseta peak VRAM no torch se disponível (não força import)."""
    try:
        import torch  # noqa
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
    except Exception:
        pass


def _round_floats(d: dict, places: int = 3) -> dict:
    """Arredonda valores float dentro de um dict shallow."""
    return {k: (round(v, places) if isinstance(v, float) else v) for k, v in d.items()}
