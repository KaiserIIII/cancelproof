"""One stock asyncio loop; observation precedes harness cleanup."""
import asyncio
import inspect
import os
import platform
import traceback

from .config import LIMITATIONS, VERSION, json_value
from .probe import Probe, INTERNAL_CREATION


def exception_info(exc):
    frames = traceback.extract_tb(exc.__traceback__)[-8:]
    result = {"type": type(exc).__name__, "frames": [
        {"file": os.path.basename(f.filename), "line": f.lineno, "function": f.name} for f in frames]}
    if isinstance(exc, BaseExceptionGroup):
        result["children"] = [exception_info(child) for child in exc.exceptions[:8]]
    return result


def skeleton(scenario, plan, limits, digest=None):
    return dict(schema_version=1, version=VERSION, scenario=scenario, verdict="PASS", outcome="not_run",
                plan=plan, limits=limits, source_sha256=digest,
                environment={"python": platform.python_version(), "implementation": platform.python_implementation(),
                             "system": platform.system(), "release": platform.release()},
                actions=[], checkpoints=[], events=[], tasks=[], invariants=[], diagnostics=[], cleanup={},
                limitations=list(LIMITATIONS))


async def execute(target, scenario, plan, limits, digest=None, emit=None):
    loop = asyncio.get_running_loop()
    previous = loop.get_task_factory()
    previous_handler = loop.get_exception_handler()
    unhandled = []
    created = 0
    created_tasks = set()

    def handler(loop, context):
        exc = context.get("exception")
        if len(unhandled) < 32:
            unhandled.append(dict(code="UNHANDLED_LOOP_EXCEPTION",
                                  exception=exception_info(exc) if exc else {"type": "LoopCallbackError"}))

    def factory(loop, coro, **kwargs):
        nonlocal created
        if not INTERNAL_CREATION.get():
            if created >= limits["max_tasks"]:
                if inspect.iscoroutine(coro):
                    coro.close()
                raise ValueError("max_tasks cumulative creation budget exceeded")
            created += 1
        task = previous(loop, coro, **kwargs) if previous else asyncio.Task(coro, loop=loop, **kwargs)
        if not INTERNAL_CREATION.get():
            created_tasks.add(task)
        return task

    loop.set_task_factory(factory)
    loop.set_exception_handler(handler)
    try:
        result = await _execute(target, scenario, plan, limits, digest, emit, created_tasks)
        if unhandled:
            result["diagnostics"].extend(unhandled)
            result["verdict"] = "FAIL"
        return result
    finally:
        loop.set_task_factory(previous)
        loop.set_exception_handler(previous_handler)


async def _execute(target, scenario, plan, limits, digest=None, emit=None, created_tasks=None):
    report = skeleton(scenario, plan, limits, digest)
    probe = Probe(plan, limits, emit)
    engine_task = asyncio.current_task()
    baseline = asyncio.all_tasks()
    probe.forbidden = set(baseline)

    async def invoke():
        await target(probe)

    root = asyncio.create_task(invoke(), name="scenario")
    probe.track(root, "scenario")
    timed_out = False
    _, pending = await asyncio.wait({root}, timeout=limits["timeout"])
    if pending:
        timed_out = True
        root.cancel()
        probe.event("soft_timeout", task="scenario")
        await asyncio.wait({root}, timeout=limits["grace"])
    # Let scheduled cancellation controllers deliver, without waiting indefinitely.
    if probe.controllers:
        await asyncio.wait(probe.controllers, timeout=limits["grace"])
    # Let completion callbacks / async-generator finalizers already queued by a finished
    # request settle. This is a two-turn observation boundary, not harness cancellation.
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    report["outcome"] = ("timeout" if timed_out else "cancelled" if root.cancelled()
                         else "completed" if root.done() and root.exception() is None else "exception")
    failures, unknown = [], []
    related = asyncio.all_tasks() - baseline - probe.controllers
    related.update(created_tasks or ())
    related.update(task for task, _ in probe.tasks.values())
    registered = {t: (name, finish) for name, (t, finish) in probe.tasks.items()}
    for index, task in enumerate(sorted(related, key=lambda t: registered.get(t, ("~",))[0])):
        name, must_finish = registered.get(task, (f"unregistered-{index}", False))
        state = "cancelled" if task.cancelled() else "completed" if task.done() else "pending"
        exempt = task in probe.exempt
        row = dict(name=name, state=state, must_finish=must_finish, excluded=exempt)
        coro = task.get_coro()
        row["coroutine"] = getattr(coro, "__qualname__", type(coro).__name__)
        row["frames"] = [{"file": os.path.basename(f.f_code.co_filename), "line": f.f_lineno,
                          "function": f.f_code.co_name} for f in task.get_stack(limit=2)]
        if exempt:
            row["reason"] = probe.exempt[task]
        if task.done() and not task.cancelled():
            exc = task.exception()
            if exc is not None:
                row["state"] = "exception"
                if task is root:
                    failures.append(dict(code="TASK_EXCEPTION", task=name, exception=exception_info(exc)))
                elif task in probe.allowed_exceptions:
                    row["exception_acknowledged"] = probe.allowed_exceptions[task]
                elif plan["expected"].get(name) != "completed":
                    unknown.append(dict(code="CHILD_EXCEPTION_UNCLASSIFIED", task=name, exception=exception_info(exc)))
        if not task.done() and not exempt:
            if task is root and timed_out:
                unknown.append(dict(code="SOFT_TIMEOUT_PENDING", task=name))
            elif must_finish or probe.no_pending:
                failures.append(dict(code="FINISH_CONTRACT", task=name))
            else:
                unknown.append(dict(code="UNCLASSIFIED_PENDING_TASK", task=name))
        report["tasks"].append(row)
    for name, predicate, category, actual, expected in probe.predicates:
        row = dict(name=name, category=category, expected=expected)
        try:
            value = predicate()
            if inspect.iscoroutine(value):
                value.close()
            if type(value) is not bool:
                raise TypeError("invariant must return bool")
            row["verdict"] = "PASS" if value else "FAIL"
            if actual is not None:
                row["actual"] = json_value(actual() if callable(actual) else actual)
            if not value:
                failures.append(dict(code="INVARIANT_FALSE", invariant=name))
        except Exception as exc:
            row["verdict"] = "INCONCLUSIVE"
            unknown.append(dict(code="INVARIANT_EVALUATION", invariant=name, exception=exception_info(exc)))
        report["invariants"].append(row)
    for name in probe.propagate:
        deliveries = [d for a in probe.actions for d in a["deliveries"] if d["task"] == name and d["accepted"]]
        if deliveries and (name not in probe.tasks or not probe.tasks[name][0].cancelled()):
            failures.append(dict(code="CANCELLATION_PROPAGATION", task=name))
    for name, expected in plan["expected"].items():
        task = probe.tasks.get(name, (None,))[0]
        if task is None:
            unknown.append(dict(code="EXPECTED_TASK_MISSING", task=name))
        elif (expected == "cancelled" and not task.cancelled()) or (
                expected == "completed" and (not task.done() or task.cancelled() or task.exception() is not None)):
            failures.append(dict(code="EXPECTED_OUTCOME", task=name, expected=expected))
    for action in probe.actions:
        if action["status"] == "NOT_RUN" or len(action["deliveries"]) < action["repeat"]:
            unknown.append(dict(code="INJECTION_NOT_COMPLETED", checkpoint=action["checkpoint"]))
        elif not any(d["accepted"] for d in action["deliveries"]):
            unknown.append(dict(code="CANCEL_NOT_ACCEPTED", checkpoint=action["checkpoint"]))
    if probe.truncated:
        unknown.append(dict(code="TRACE_TRUNCATED"))
    # Snapshot above is authoritative. Cleanup only this run's application tasks and controllers.
    cleanup_tasks = (related | probe.controllers) - {engine_task}
    cleanup_pending = {t for t in cleanup_tasks if not t.done()}
    for task in cleanup_pending:
        task.cancel()
    if cleanup_pending:
        _, residual = await asyncio.wait(cleanup_pending, timeout=limits["grace"])
    else:
        residual = set()
    report["cleanup"] = dict(requested=len(cleanup_pending), pending=len(residual), observed_before_cleanup=True)
    if residual:
        unknown.append(dict(code="CLEANUP_PENDING", count=len(residual)))
    for task in cleanup_tasks:
        if task.done() and not task.cancelled():
            exc = task.exception()
            if exc is not None and task in cleanup_pending:
                failures.append(dict(code="CLEANUP_EXCEPTION", exception=exception_info(exc)))
    report.update(actions=probe.actions, events=probe.events, checkpoints=probe.checkpoints,
                  diagnostics=failures + unknown, verdict="FAIL" if failures else "INCONCLUSIVE" if unknown else "PASS")
    return report
