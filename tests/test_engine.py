import asyncio
import unittest

from cancelproof import run_scenario, arun_scenario, campaign


class EngineTests(unittest.TestCase):
    def run_case(self, name, checkpoint=None, **action):
        plan = {"actions": [{"checkpoint": checkpoint, **action}]} if checkpoint else None
        return run_scenario("cancelproof.examples:" + name, plan)

    def test_lock_broken_and_fixed(self):
        self.assertEqual(self.run_case("lock_broken", "after_lock")["verdict"], "FAIL")
        r = self.run_case("lock_fixed", "after_lock")
        self.assertEqual((r["verdict"], r["outcome"]), ("PASS", "cancelled"))
        self.assertTrue(r["actions"][0]["deliveries"][0]["accepted"])

    def test_swallowed_cancellation_requires_contract(self):
        self.assertEqual(self.run_case("swallow_broken", "work")["verdict"], "FAIL")
        self.assertEqual(self.run_case("swallow_fixed", "work")["verdict"], "PASS")

    def test_background_contract(self):
        self.assertEqual(self.run_case("background_broken", "request")["verdict"], "FAIL")
        self.assertEqual(self.run_case("background_fixed", "request")["verdict"], "PASS")
        self.assertEqual(self.run_case("background_allowed")["verdict"], "PASS")
        self.assertEqual(self.run_case("background_unclassified")["verdict"], "INCONCLUSIVE")

    def test_token_workers(self):
        self.assertEqual(self.run_case("token_broken", "granted", task="worker")["verdict"], "FAIL")
        self.assertEqual(self.run_case("token_fixed", "granted", task="worker")["verdict"], "PASS")

    def test_cleanup_repeated_cancel(self):
        for name, verdict in [("cleanup_broken", "FAIL"), ("cleanup_fixed", "PASS")]:
            with self.subTest(name=name):
                self.assertEqual(self.run_case(name, "work", repeat=2)["verdict"], verdict)

    def test_taskgroup_normal_and_cancellation(self):
        self.assertEqual(self.run_case("taskgroup_ok")["verdict"], "PASS")
        self.assertEqual(self.run_case("taskgroup_ok", "group_work", task="worker")["verdict"], "PASS")

    def test_missing_checkpoint(self):
        r = self.run_case("lock_fixed", "missing")
        self.assertEqual(r["verdict"], "INCONCLUSIVE")
        self.assertEqual(r["actions"][0]["status"], "NOT_RUN")

    def test_invalid_invariant_is_unknown(self):
        self.assertEqual(self.run_case("invalid_invariant")["verdict"], "INCONCLUSIVE")

    def test_exception_redaction(self):
        r = self.run_case("exception_case")
        self.assertEqual(r["verdict"], "FAIL")
        self.assertNotIn("secret-value", str(r))
        self.assertEqual(r["diagnostics"][0]["exception"]["type"], "ValueError")

    def test_timeout_and_hard_deadline(self):
        r = run_scenario("cancelproof.examples:soft_timeout", limits={"timeout": .05})
        self.assertEqual((r["outcome"], r["verdict"]), ("timeout", "PASS"))
        for name in ("blocks_loop", "resists_cancel"):
            r = run_scenario("cancelproof.examples:" + name,
                             limits={"timeout": .05, "grace": .02, "wall_timeout": .5})
            self.assertEqual((r["outcome"], r["verdict"]), ("hard_timeout", "INCONCLUSIVE"))

    def test_invalid_input(self):
        for plan in ({"actions": [{"checkpoint": "x", "repeat": True}]}, {"surprise": 1}):
            with self.assertRaises(ValueError):
                run_scenario("cancelproof.examples:lock_fixed", plan)
        r = run_scenario("nonexistent_cancelproof_module:target")
        self.assertEqual(r["verdict"], "NOT_RUN")

    def test_source_mismatch_does_not_execute(self):
        r = run_scenario("cancelproof.examples:exception_case", expected_source_sha256="0" * 64)
        self.assertEqual(r["verdict"], "INCONCLUSIVE")
        self.assertEqual(r["outcome"], "not_run")

    def test_campaign_is_bounded(self):
        r = campaign("cancelproof.examples:lock_fixed", max_runs=3, seed=7)
        self.assertLessEqual(len(r["runs"]), 3)
        self.assertEqual(r["verdict"], "PASS")


class AsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_caller_survives(self):
        own = asyncio.current_task()
        r = await arun_scenario("cancelproof.examples:lock_fixed", {"actions": [{"checkpoint": "after_lock"}]})
        self.assertEqual(r["verdict"], "PASS")
        self.assertEqual(own.cancelling(), 0)

    async def test_caller_cancellation_reaps_child(self):
        pending_before = asyncio.all_tasks()
        task = asyncio.create_task(arun_scenario("cancelproof.examples:blocks_loop"))
        await asyncio.sleep(.15)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(asyncio.all_tasks(), pending_before)


if __name__ == "__main__":
    unittest.main()
