import asyncio
import unittest
from cancelproof import run_scenario
from cancelproof.engine import execute
from cancelproof.config import validate


class BoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def execute(self, target, plan=None, limits=None):
        plan,limits=validate('test:target',plan,limits)
        return await execute(target,'test:target',plan,limits)

    async def test_cannot_register_framework_task(self):
        framework=asyncio.current_task()
        async def target(p):
            with self.assertRaises(ValueError):p.track(framework,'framework')
        self.assertEqual((await self.execute(target))['verdict'],'PASS')
        self.assertEqual(framework.cancelling(),0)

    async def test_predicate_error_and_async_predicate(self):
        async def async_predicate():return True
        async def target(p):
            p.invariant('bad',lambda:1/0)
            p.invariant('async',async_predicate)
        r=await self.execute(target)
        self.assertEqual(r['verdict'],'INCONCLUSIVE')
        self.assertEqual([i['verdict'] for i in r['invariants']],['INCONCLUSIVE']*2)

    async def test_taskgroup_exception_classified(self):
        async def bad():raise RuntimeError('private error text')
        async def target(p):
            async with asyncio.TaskGroup() as g:p.track(g.create_task(bad()),'child')
        r=await self.execute(target)
        self.assertEqual(r['verdict'],'FAIL')
        self.assertNotIn('private error text',str(r))

    async def test_cleanup_exception_is_failure(self):
        async def worker():
            try:await asyncio.sleep(10)
            finally:raise ValueError('cleanup private')
        async def target(p):
            t=p.create_task(worker(),'background')
            p.allow_background(t,'explicit background')
            await asyncio.sleep(0)
        r=await self.execute(target)
        self.assertEqual(r['verdict'],'FAIL')
        self.assertIn('CLEANUP_EXCEPTION',[d['code'] for d in r['diagnostics']])

    async def test_task_bound_and_duplicate_names(self):
        async def target(p):
            t=p.create_task(asyncio.sleep(10),'worker')
            with self.assertRaises(ValueError):p.create_task(asyncio.sleep(0),'worker')
            with self.assertRaises(ValueError):p.create_task(asyncio.sleep(0),'overflow')
            t.cancel();await asyncio.gather(t,return_exceptions=True)
        self.assertEqual((await self.execute(target,limits={'max_tasks':2}))['verdict'],'PASS')

    async def test_unregistered_task_creation_budget(self):
        async def target(p):
            task=asyncio.create_task(asyncio.sleep(10))
            with self.assertRaises(ValueError):asyncio.create_task(asyncio.sleep(0))
            task.cancel();await asyncio.gather(task,return_exceptions=True)
        self.assertEqual((await self.execute(target,limits={'max_tasks':2}))['verdict'],'PASS')

    async def test_trace_limit_inconclusive(self):
        async def target(p):
            for i in range(40):p.event('many',index=i)
        r=await self.execute(target,limits={'max_events':16})
        self.assertEqual(r['verdict'],'INCONCLUSIVE')
        self.assertEqual(len(r['events']),16)

    async def test_joint_task_occurrence_selection(self):
        async def target(p):
            async def worker():
                for _ in range(3):await p.checkpoint('point')
            a=p.create_task(worker(),'a');b=p.create_task(worker(),'b')
            await asyncio.gather(a,b,return_exceptions=True)
        r=await self.execute(target,{'actions':[{'checkpoint':'point','task':'b','occurrence':2}]})
        self.assertEqual(r['verdict'],'PASS')
        states={t['name']:t['state'] for t in r['tasks']}
        self.assertEqual((states['a'],states['b']),('completed','cancelled'))

    async def test_file_and_business_contract(self):
        import tempfile
        async def target(p):
            f=tempfile.TemporaryFile();balance=[10,0]
            p.invariant('file_closed',lambda:f.closed,category='resource')
            p.invariant('balance',lambda:sum(balance)==10)
            try:
                balance[:]=[6,4]
                await p.checkpoint('commit')
            finally:f.close()
        self.assertEqual((await self.execute(target,{'actions':[{'checkpoint':'commit'}]}))['verdict'],'PASS')
