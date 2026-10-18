"""Strict, bounded, JSON-only execution requests."""
import json
import math
import re

VERSION = "0.1.0"
LIMITATIONS = [
    "Trusted local Python targets only; subprocess containment is not a security sandbox.",
    "Only named checkpoints are controlled. Ordinary asyncio scheduling remains uncontrolled.",
    "A bounded passing run does not prove race freedom or real-world false-positive rates.",
    "Source digest covers the scenario module only, not transitive dependencies or environment.",
    "No hard memory quota or descendant-process isolation; user-shared events may contain sensitive data.",
]
DEFAULTS = dict(timeout=1.0, grace=.15, wall_timeout=5.0, max_tasks=32, max_events=2000)


def label(value):
    if not isinstance(value, str) or not value or len(value) > 128:
        raise ValueError("labels must be nonempty strings of at most 128 characters")
    return value


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"expected integer in [{low}, {high}]")
    return value


def validate(scenario, plan=None, limits=None):
    if not isinstance(scenario, str) or not re.fullmatch(r"[A-Za-z_][\w.]*:[A-Za-z_]\w*", scenario, re.ASCII):
        raise ValueError("scenario must be an importable module:async_callable")
    if plan is None:
        plan = {}
    if type(plan) is not dict or set(plan) - {"actions", "expected"}:
        raise ValueError("unknown plan fields")
    actions = plan.get("actions", [])
    expected = plan.get("expected", {})
    if type(actions) is not list or len(actions) > 32 or type(expected) is not dict or len(expected) > 64:
        raise ValueError("plan exceeds bounds")
    normalized = []
    for action in actions:
        if type(action) is not dict or set(action) - {"checkpoint", "task", "occurrence", "repeat", "delay_turns"}:
            raise ValueError("invalid action fields")
        normalized.append(dict(checkpoint=label(action.get("checkpoint")),
                               task=label(action["task"]) if action.get("task") is not None else None,
                               occurrence=integer(action.get("occurrence", 1), 1, 1000),
                               repeat=integer(action.get("repeat", 1), 1, 4),
                               delay_turns=integer(action.get("delay_turns", 0), 0, 10)))
    for key, value in expected.items():
        label(key)
        if value not in ("completed", "cancelled"):
            raise ValueError("expected outcomes are completed or cancelled")
    if limits is None:
        limits = {}
    if type(limits) is not dict or set(limits) - set(DEFAULTS):
        raise ValueError("unknown limits")
    lim = {**DEFAULTS, **limits}
    for key, low, high in (("timeout", .05, 30), ("grace", .01, 5), ("wall_timeout", .2, 60)):
        v = lim[key]
        if type(v) not in (int, float) or not math.isfinite(v) or not low <= v <= high:
            raise ValueError(f"invalid {key}")
    integer(lim["max_tasks"], 1, 128)
    integer(lim["max_events"], 16, 10000)
    if lim["wall_timeout"] < lim["timeout"] + lim["grace"] + .1:
        raise ValueError("wall_timeout must exceed timeout + grace + 0.1 seconds")
    return {"actions": normalized, "expected": expected}, lim


def json_value(value):
    encoded = json.dumps(value, ensure_ascii=True, allow_nan=False)
    if len(encoded) > 16384:
        raise ValueError("individual evidence value exceeds 16 KiB")
    return json.loads(encoded)
