import shutil
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from cancelproof.runner import _Workspace


class WorkspaceTests(TestCase):
    def test_transient_lock_retry(self):
        original=shutil.rmtree
        attempts=[]
        def remove(path):
            attempts.append(path)
            if len(attempts)<3:raise PermissionError('simulated Windows transient handle')
            return original(path)
        workspace=_Workspace()
        with patch('cancelproof.runner.shutil.rmtree',side_effect=remove):
            with workspace as path:Path(path,'trace.jsonl').write_text('public')
        self.assertTrue(workspace.cleaned)
        self.assertEqual(len(attempts),3)

    def test_cleanup_never_masks_original_error(self):
        workspace=_Workspace()
        try:
            with patch('cancelproof.runner.shutil.rmtree',side_effect=PermissionError),patch('cancelproof.runner.time.sleep'):
                with self.assertRaisesRegex(RuntimeError,'original'):
                    with workspace:raise RuntimeError('original')
            self.assertFalse(workspace.cleaned)
        finally:shutil.rmtree(workspace.name)
