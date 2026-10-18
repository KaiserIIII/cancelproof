"""Private subprocess entry point. Imports execute trusted local code."""
import asyncio
import hashlib
import importlib
import inspect
import json
import pathlib
import sys

from .config import validate
from .engine import execute, skeleton, exception_info


def main():
    folder = pathlib.Path(sys.argv[1])
    request = json.loads((folder / "request.json").read_text(encoding="utf-8"))
    scenario = request["scenario"]
    plan, limits = validate(scenario, request.get("plan"), request.get("limits"))
    report = skeleton(scenario, plan, limits)
    try:
        module_name, func_name = scenario.split(":")
        module = importlib.import_module(module_name)
        path = getattr(module, "__file__", None)
        digest = hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest() if path else None
        report["source_sha256"] = digest
        expected = request.get("expected_source_sha256")
        if expected is not None and digest != expected:
            report.update(verdict="INCONCLUSIVE", diagnostics=[{"code": "SOURCE_MISMATCH"}])
        else:
            target = getattr(module, func_name)
            if not inspect.iscoroutinefunction(target):
                raise TypeError("target must be async callable")
            with (folder / "events.jsonl").open("w", encoding="utf-8") as trace:
                def emit(row):
                    trace.write(json.dumps(row, ensure_ascii=True, allow_nan=False) + "\n")
                    trace.flush()

                async def work():
                    result = await execute(target, scenario, plan, limits, digest, emit)
                    # Parent still requires normal child exit; shutdown can itself hang.
                    (folder / "report.json").write_text(json.dumps(result, ensure_ascii=True), encoding="utf-8")
                    return result
                report = asyncio.run(work())
    except BaseException as exc:
        report.update(verdict="NOT_RUN", outcome="not_run", input_error=True,
                      diagnostics=[{"code": "TARGET_IMPORT_OR_WORKER_ERROR", "exception": exception_info(exc)}])
    (folder / "report.json").write_text(json.dumps(report, ensure_ascii=True), encoding="utf-8")


if __name__ == "__main__":
    main()
