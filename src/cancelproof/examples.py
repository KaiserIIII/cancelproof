"""Small executable defects and controls. These are constructed tests, not historical bugs."""
import asyncio
import time


async def lock_broken(probe):
    lock = asyncio.Lock()
    probe.watch_lock("lock_released", lock)
    await lock.acquire()
    await probe.checkpoint("after_lock")
    lock.release()


async def lock_fixed(probe):
    lock = asyncio.Lock()
    probe.watch_lock("lock_released", lock)
    async with lock:
        await probe.checkpoint("after_lock")


async def swallow_broken(probe):
    probe.expect_cancelled()
    try:
        await probe.checkpoint("work")
    except asyncio.CancelledError:
        probe.event("cancel_swallowed")


async def swallow_fixed(probe):
    probe.expect_cancelled()
    await probe.checkpoint("work")


async def background_broken(probe):
    probe.create_task(asyncio.sleep(30), "background")
    await probe.checkpoint("request")


async def background_fixed(probe):
    child = probe.create_task(asyncio.sleep(30), "background")
    try:
        await probe.checkpoint("request")
    finally:
        child.cancel()
        await asyncio.gather(child, return_exceptions=True)


async def background_allowed(probe):
    task = probe.create_task(asyncio.sleep(30), "background")
    probe.allow_background(task, "intentional service worker")


async def background_unclassified(probe):
    asyncio.create_task(asyncio.sleep(30))


async def _tokens(probe, broken):
    queue = asyncio.Queue(maxsize=1)
    queue.put_nowait("token")
    probe.invariant("token_conserved", lambda: queue.qsize() == 1, category="resource", actual=queue.qsize, expected=1)

    async def worker():
        token = await queue.get()
        if broken:
            await probe.checkpoint("granted")
            queue.put_nowait(token)
        else:
            try:
                await probe.checkpoint("granted")
            finally:
                queue.put_nowait(token)

    first = probe.create_task(worker(), "worker")
    second = probe.create_task(worker(), "competitor")
    # Bounded waiting avoids the broken token example consuming the whole scenario deadline.
    _, pending = await asyncio.wait({first, second}, timeout=.05)
    for task in pending:
        task.cancel()
    await asyncio.gather(first, second, return_exceptions=True)


async def token_broken(probe):
    await _tokens(probe, True)


async def token_fixed(probe):
    await _tokens(probe, False)


async def _cleanup(probe, safe):
    state = {"closed": False, "calls": 0}
    probe.invariant("closed_once", lambda: state["closed"] and state["calls"] == 1,
                    category="resource", actual=lambda: dict(state))

    async def close():
        state["calls"] += 1
        probe.event("cleanup_started")
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        state["closed"] = True
        probe.event("cleanup_completed")

    try:
        await probe.checkpoint("work")
    finally:
        if not safe:
            await close()
        else:
            task = probe.create_task(close(), "cleanup")
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    probe.event("cleanup_shielded")
            task.result()


async def cleanup_broken(probe):
    await _cleanup(probe, False)


async def cleanup_fixed(probe):
    await _cleanup(probe, True)


async def taskgroup_ok(probe):
    async def worker():
        await probe.checkpoint("group_work")

    async with asyncio.TaskGroup() as group:
        probe.track(group.create_task(worker()), "worker")
        probe.track(group.create_task(asyncio.sleep(0)), "peer")


async def invalid_invariant(probe):
    probe.invariant("not_a_boolean", lambda: "truthy")


async def exception_case(probe):
    raise ValueError("secret-value must never appear in default reports")


async def soft_timeout(probe):
    state = {"closed": False}
    probe.invariant("closed", lambda: state["closed"])
    try:
        await asyncio.sleep(30)
    finally:
        state["closed"] = True


async def blocks_loop(probe):
    await probe.checkpoint("before_block")
    time.sleep(30)


async def resists_cancel(probe):
    await probe.checkpoint("before_resist")
    while True:
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass


async def asgi_fixed(probe):
    from .service import exercise
    await exercise(probe, broken=False)


async def asgi_broken(probe):
    from .service import exercise
    await exercise(probe, broken=True)
