import unittest
from cancelproof import run_scenario


class ServiceTests(unittest.TestCase):
    def test_real_asgi_normal_response(self):
        r=run_scenario('cancelproof.examples:asgi_fixed')
        self.assertEqual((r['verdict'],r['outcome']),('PASS','completed'),r['diagnostics'])

    def test_real_asgi_cancel_broken_and_fixed(self):
        plan={'actions':[{'checkpoint':'request_received','task':'request'}]}
        for name,expected in [('asgi_broken','FAIL'),('asgi_fixed','PASS')]:
            with self.subTest(name=name):
                r=run_scenario('cancelproof.examples:'+name,plan)
                self.assertEqual(r['verdict'],expected,r['diagnostics'])
                self.assertTrue(r['actions'][0]['deliveries'][0]['accepted'])

    def test_real_asgi_timeout_cleanup(self):
        # Delay the first request cancellation so the handler is still active at the soft deadline.
        # A separate short timeout target uses the same transport and service, below.
        r=run_scenario('cancelproof.service:timeout_exercise',limits={'timeout':.3})
        self.assertEqual((r['verdict'],r['outcome']),('PASS','timeout'),r['diagnostics'])
