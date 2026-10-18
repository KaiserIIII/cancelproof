import asyncio


def test_sync_fixture(cancelproof):
    r=cancelproof('cancelproof.examples:lock_fixed',{'actions':[{'checkpoint':'after_lock'}]})
    assert r['verdict']=='PASS'


def test_async_fixture(cancelproof_async):
    async def test():
        r=await cancelproof_async('cancelproof.examples:lock_fixed')
        assert r['verdict']=='PASS'
    asyncio.run(test())
