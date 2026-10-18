"""Real HTTPX ASGI transport integration; no socket or external service required."""
import asyncio


class RequestService:
    def __init__(self, probe, broken=False, delay=.02):
        self.probe, self.broken = probe, broken
        self.delay = delay
        self.active, self.closed, self.committed = 0, 0, 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            raise ValueError("HTTP only demo")
        if scope["path"] != "/work":
            await send({"type": "http.response.start", "status": 404, "headers": []})
            await send({"type": "http.response.body", "body": b"not found"})
            return
        await receive()
        self.active += 1
        self.probe.event("request_opened")
        background = self.probe.create_task(asyncio.sleep(30), "request-background")
        try:
            await self.probe.checkpoint("request_received")
            await asyncio.sleep(self.delay)
            self.committed += 1
            await send({"type": "http.response.start", "status": 200,
                        "headers": [(b"content-type", b"text/plain; charset=utf-8")]})
            await send({"type": "http.response.body", "body": "完成".encode()})
        finally:
            if not self.broken:
                background.cancel()
                await asyncio.gather(background, return_exceptions=True)
                self.active -= 1
                self.closed += 1
                self.probe.event("request_closed")


async def exercise(probe, broken=False, delay=.02):
    import httpx
    app = RequestService(probe, broken, delay)
    probe.invariant("request_resources_closed", lambda: app.active == 0 and app.closed == 1,
                    category="resource", actual=lambda: {"active": app.active, "closed": app.closed})
    probe.require_no_pending()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://cancelproof.local") as client:
        task = probe.create_task(client.post("/work", content=b"public test body"), "request")
        probe.expect_cancelled("request")
        try:
            response = await task
            probe.invariant("response_unicode", lambda: response.status_code == 200 and response.text == "完成")
        except asyncio.CancelledError:
            probe.invariant("no_cancelled_commit", lambda: app.committed == 0, actual=lambda: app.committed)
            if asyncio.current_task().cancelling():
                raise


async def timeout_exercise(probe):
    await exercise(probe, delay=30)
