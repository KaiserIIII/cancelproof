"""Fresh process execution with a parent deadline and bounded campaign selection."""
import asyncio
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import time
import warnings

from .config import validate, integer, VERSION
from .engine import skeleton

MAX_FILE = 2 * 1024 * 1024


class _Workspace:
    """Windows can briefly retain a dead process's file handles. Never mask cancellation."""
    def __enter__(self):
        self.name = tempfile.mkdtemp(prefix="cancelproof-")
        self.cleaned = False
        return self.name

    def __exit__(self, exc_type, exc, tb):
        for attempt in range(20):
            try:
                shutil.rmtree(self.name)
                self.cleaned = True
                break
            except FileNotFoundError:
                self.cleaned = True
                break
            except OSError:
                time.sleep(.05)
        if not self.cleaned:
            warnings.warn("CancelProof private temporary directory cleanup incomplete", ResourceWarning)
        return False


def _stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=.5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1)


async def arun_scenario(scenario, plan=None, limits=None, *, expected_source_sha256=None):
    plan, limits = validate(scenario, plan, limits)
    if expected_source_sha256 is not None and (not isinstance(expected_source_sha256, str)
            or len(expected_source_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_source_sha256)):
        raise ValueError("expected digest must be lowercase SHA256")
    request = dict(scenario=scenario, plan=plan, limits=limits, expected_source_sha256=expected_source_sha256)
    result = skeleton(scenario, plan, limits)
    workspace = _Workspace()
    with workspace as name:
        folder = Path(name)
        (folder / "request.json").write_text(json.dumps(request), encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(str(Path(p).absolute()) for p in sys.path if p)
        env["PYTHONIOENCODING"] = "utf-8"
        with (folder / "stdout.log").open("wb") as out, (folder / "stderr.log").open("wb") as err:
            process = subprocess.Popen([sys.executable, "-m", "cancelproof._worker", name],
                                       stdin=subprocess.DEVNULL, stdout=out, stderr=err, env=env)
            started = time.monotonic()
            reason = None
            try:
                while process.poll() is None:
                    if time.monotonic() - started > limits["wall_timeout"]:
                        reason = "HARD_DEADLINE"
                        break
                    if any(p.stat().st_size > MAX_FILE for p in folder.iterdir() if p.is_file()):
                        reason = "OUTPUT_LIMIT"
                        break
                    await asyncio.sleep(.01)
            finally:
                _stop(process)
        if reason is None and process.returncode == 0 and (folder / "report.json").is_file():
            if (folder / "report.json").stat().st_size <= MAX_FILE:
                result = json.loads((folder / "report.json").read_text(encoding="utf-8"))
            else:
                reason = "OUTPUT_LIMIT"
        elif reason is None:
            reason = "WORKER_EXIT"
        if reason:
            result.update(verdict="INCONCLUSIVE", outcome="hard_timeout" if reason == "HARD_DEADLINE" else "not_run",
                          diagnostics=[dict(code=reason, returncode=process.returncode)])
            trace = folder / "events.jsonl"
            if trace.is_file():
                for line in trace.read_bytes()[:MAX_FILE].splitlines()[:limits["max_events"]]:
                    try:
                        result["events"].append(json.loads(line))
                    except (ValueError, UnicodeError):
                        break
        result["process"] = dict(returncode=process.returncode, reaped=process.poll() is not None,
                                 elapsed_seconds=round(time.monotonic() - started, 4),
                                 stdout_bytes=(folder / "stdout.log").stat().st_size,
                                 stderr_bytes=(folder / "stderr.log").stat().st_size)
    result["process"]["workspace_removed"] = workspace.cleaned
    if not workspace.cleaned:
        result["diagnostics"].append({"code": "WORKSPACE_CLEANUP_INCOMPLETE"})
        if result["verdict"] == "PASS":
            result["verdict"] = "INCONCLUSIVE"
    return result


def run_scenario(scenario, plan=None, limits=None, *, expected_source_sha256=None):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(arun_scenario(scenario, plan, limits, expected_source_sha256=expected_source_sha256))
    raise ValueError("use await arun_scenario inside a running event loop")


def aggregate(scenario, runs, selection=None):
    verdicts = [r["verdict"] for r in runs]
    verdict = "FAIL" if "FAIL" in verdicts else "INCONCLUSIVE" if any(v != "PASS" for v in verdicts) else "PASS"
    return dict(schema_version=1, version=VERSION, scenario=scenario, verdict=verdict if runs else "NOT_RUN", runs=runs,
                selection=selection or {}, summary={v: verdicts.count(v) for v in ("PASS", "FAIL", "INCONCLUSIVE", "NOT_RUN")},
                limitations=["Checkpoint selection is bounded coverage, not exhaustive scheduling."])


def campaign(scenario, max_runs=12, seed=0, repeats=1, limits=None):
    integer(max_runs, 1, 64)
    integer(repeats, 1, 8)
    if type(seed) is not int:
        raise ValueError("seed must be integer")
    started = time.monotonic()
    baseline = run_scenario(scenario, limits=limits)
    runs = [baseline]
    points = baseline["checkpoints"].copy()
    rng = random.Random(seed)
    rng.shuffle(points)
    plans = []
    for point in points:
        for _ in range(repeats):
            plans.append({"actions": [{k: point[k] for k in ("checkpoint", "task", "occurrence")}]})
    for plan in plans[:max_runs - 1]:
        if time.monotonic() - started + (limits or {}).get("wall_timeout", 5) + 2.6 > 120:
            break
        runs.append(run_scenario(scenario, plan, limits))
    return aggregate(scenario, runs, dict(mode="baseline_then_checkpoint_cancellation", seed=seed, repeats=repeats,
                                         max_runs=max_runs, total_seconds_limit=120, selected=len(runs) - 1,
                                         unselected=max(0, len(plans) - len(runs) + 1)))
