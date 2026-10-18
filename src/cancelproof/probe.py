"""Public asyncio checkpoints and explicit application contracts."""
import asyncio
import inspect
from contextvars import ContextVar
from collections import Counter

from .config import json_value, label

INTERNAL_CREATION = ContextVar("cancelproof_internal_creation", default=False)


class Probe:
    def __init__(self, plan, limits, emit=None):
        self.plan, self.limits, self.emit = plan, limits, emit
        self.tasks = {}
        self.controllers = set()
        self.exempt = {}
        self.predicates = []
        self.events, self.checkpoints = [], []
        self.counts = Counter()
        self.actions = [{**a, "status": "NOT_RUN", "deliveries": []} for a in plan["actions"]]
        self.propagate = set()
        self.no_pending = False
        self.truncated = False
        self.forbidden = set()

    def event(self, name, **details):
        name = label(name)
        details = json_value(details)
        if len(self.events) >= self.limits["max_events"]:
            self.truncated = True
            return
        row = dict(seq=len(self.events) + 1, name=name, details=details)
        self.events.append(row)
        if self.emit:
            self.emit(row)

    def observe(self, name, value):
        self.event("observation", label=label(name), value=value)

    def track(self, task, name, must_finish=True):
        name = label(name)
        if not isinstance(task, asyncio.Task) or task.get_loop() is not asyncio.get_running_loop():
            raise ValueError("track requires a Task on this event loop")
        if task in self.forbidden or task in self.controllers or name in self.tasks or any(t is task for t, _ in self.tasks.values()):
            raise ValueError("task or label already registered, or engine task")
        if len(self.tasks) >= self.limits["max_tasks"]:
            raise ValueError("max_tasks exceeded")
        if type(must_finish) is not bool:
            raise ValueError("must_finish must be bool")
        self.tasks[name] = (task, must_finish)
        return task

    def create_task(self, coro, name, must_finish=True):
        try:
            label(name)
            if name in self.tasks or len(self.tasks) >= self.limits["max_tasks"]:
                raise ValueError("duplicate label or max_tasks exceeded")
            task = asyncio.create_task(coro, name=name)
            return self.track(task, name, must_finish)
        except BaseException:
            if inspect.iscoroutine(coro):
                coro.close()
            raise

    def allow_background(self, task, reason):
        label(reason)
        if not isinstance(task, asyncio.Task) or task.get_loop() is not asyncio.get_running_loop():
            raise ValueError("background exclusion requires local Task")
        self.exempt[task] = reason

    def invariant(self, name, predicate, *, category="business", actual=None, expected=True):
        label(name)
        label(category)
        if not callable(predicate) or len(self.predicates) >= 128 or any(p[0] == name for p in self.predicates):
            raise ValueError("invalid, duplicate, or excessive invariant")
        self.predicates.append((name, predicate, category, actual, json_value(expected)))

    def watch_lock(self, name, lock):
        self.invariant(name, lambda: not lock.locked(), category="resource", actual=lock.locked, expected=False)

    def expect_cancelled(self, name="scenario"):
        self.propagate.add(label(name))

    def require_no_pending(self):
        self.no_pending = True

    def task_label(self, task):
        for name, (registered, _) in self.tasks.items():
            if registered is task:
                return name
        raise ValueError("checkpoint caller must be registered with probe.track/create_task")

    def deliver(self, action, target, target_name):
        accepted = target.cancel()
        row = dict(task=target_name, accepted=accepted, cancelling=target.cancelling())
        action["deliveries"].append(row)
        self.event("cancel_requested", **row)

    async def requests(self, action, target, target_name, first_done=False):
        for index in range(int(first_done), action["repeat"]):
            for _ in range(max(1, action["delay_turns"])):
                await asyncio.sleep(0)
            self.deliver(action, target, target_name)

    async def checkpoint(self, name):
        name = label(name)
        task = asyncio.current_task()
        task_name = self.task_label(task)
        self.counts[(task_name, name)] += 1
        occurrence = self.counts[(task_name, name)]
        if len(self.checkpoints) < self.limits["max_events"]:
            self.checkpoints.append(dict(task=task_name, checkpoint=name, occurrence=occurrence,
                                         event_seq=len(self.events) + 1))
        else:
            self.truncated = True
        self.event("checkpoint", task=task_name, checkpoint=name, occurrence=occurrence)
        for action in self.actions:
            # task is both caller selector and cancellation target; no unrelated task cancellation.
            if (action["status"] == "NOT_RUN" and action["checkpoint"] == name
                    and action["occurrence"] == occurrence and action["task"] in (None, task_name)):
                action["status"] = "HIT"
                first_done = action["delay_turns"] == 0
                if first_done:
                    self.deliver(action, task, task_name)
                if not first_done or action["repeat"] > 1:
                    token = INTERNAL_CREATION.set(True)
                    try:
                        controller = asyncio.create_task(self.requests(action, task, task_name, first_done))
                    finally:
                        INTERNAL_CREATION.reset(token)
                    self.controllers.add(controller)
        await asyncio.sleep(0)
