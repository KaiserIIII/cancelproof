import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cancelproof.reports import write_reports


class InterfaceTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'cancelproof', *args], capture_output=True, text=True,
                              encoding='utf-8', timeout=20)

    def test_run_exit_codes_and_reports(self):
        with tempfile.TemporaryDirectory() as td:
            plan=Path(td)/'plan.json'
            plan.write_text(json.dumps({'actions':[{'checkpoint':'after_lock'}]}),encoding='utf-8')
            for target,code in [('lock_fixed',0),('lock_broken',2)]:
                out=Path(td)/target
                p=self.cli('run','cancelproof.examples:'+target,'--plan',str(plan),'--output',str(out))
                self.assertEqual(p.returncode,code,p.stderr)
                r=json.loads(p.stdout)
                self.assertEqual(json.loads((out/'report.json').read_text())['verdict'],r['verdict'])
                self.assertTrue((out/'replay.json').exists())
                q=self.cli('replay',str(out/'replay.json'))
                self.assertEqual(q.returncode,code,q.stderr)

    def test_invalid_and_unknown_exit_codes(self):
        self.assertEqual(self.cli('run','missing_cancelproof:bad').returncode,1)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'p.json';p.write_text('{"actions":[{"checkpoint":"missing"}]}')
            self.assertEqual(self.cli('run','cancelproof.examples:lock_fixed','--plan',str(p)).returncode,3)

    def test_report_inert_unicode_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'report'
            r={'schema_version':1,'scenario':'测试<script>alert(1)</script>','verdict':'PASS','plan':{},'limits':{}}
            write_reports(r,p)
            text=(p/'report.html').read_text(encoding='utf-8')
            self.assertNotIn('<script>',text)
            self.assertIn('测试',text)
            with self.assertRaises(FileExistsError):write_reports(r,p)

    def test_explore(self):
        r=self.cli('explore','cancelproof.examples:lock_fixed','--max-runs','2')
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(len(json.loads(r.stdout)['runs']),2)
        self.assertEqual(json.loads(r.stdout)['version'],'0.1.0')
        self.assertIn('CancelProof: PASS',r.stderr)

    def test_replay_validates_entire_batch_before_execution(self):
        from cancelproof.cli import main
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/'replay.json'
            for limits in (None,{'wall_timeout':-1000}):
                data={'schema_version':1,'scenario':'cancelproof.examples:lock_fixed','runs':[
                    {'plan':{},'limits':{'wall_timeout':60},'source_sha256':'a'*64}]*3+
                    [{'plan':{},'limits':limits,'source_sha256':'a'*64}]}
                file.write_text(json.dumps(data),encoding='utf-8')
                with patch('cancelproof.cli.run_scenario') as run:
                    self.assertEqual(main(['replay',str(file)]),1)
                    run.assert_not_called()
