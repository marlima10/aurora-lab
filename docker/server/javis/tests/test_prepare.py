import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import prepare
import stdio_bridge

class PreparationTests(unittest.TestCase):
    def test_private_configuration_is_idempotent_and_separated(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(prepare.os,'chown'), contextlib.redirect_stdout(io.StringIO()):
            root=Path(directory);(root/'secrets/sso').mkdir(parents=True)
            (root/'secrets/sso/apps.json').write_text(json.dumps({k:{'ready':True,'secret':k+'-synthetic','identities':{'fixture':'native'}} for k in ('opengym','actual','mealie','manyfold')}))
            prepare.prepare(root)
            before={p.name:p.read_bytes() for p in (root/'secrets/javis').iterdir()}
            prepare.prepare(root)
            self.assertEqual(before,{p.name:p.read_bytes() for p in (root/'secrets/javis').iterdir()})
            mcp=json.loads(before['mcp.json']);boot=json.loads(before['bootstrap.json'])
            self.assertEqual(set(boot),{'token'});self.assertEqual(boot['token'],mcp['token'])
            self.assertEqual(len(set(mcp['connectors'].values())),5)
            for role in ('fitness','food','finance'):
                config=json.loads(before[role+'.json']);self.assertNotIn('connectors',config);self.assertEqual(config['token'],mcp['connectors'][role])

    def test_notes_cannot_overwrite_or_escape(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(stdio_bridge,'VAULT',Path(directory)):
            root=Path(directory);(root/'notes').mkdir();(root/'notes/existing.md').write_text('fixture')
            def check(path):stdio_bridge.validate({'method':'tools/call','params':{'name':'javis_write_file','arguments':{'path':path,'content':'fixture'}}})
            check('notes/new.md')
            for path in ('notes/existing.md','/etc/passwd','notes/../../outside.md','notes/.secret.md','notes/file.txt','config.md'):
                with self.subTest(path=path),self.assertRaises(ValueError):check(path)
            self.assertEqual((root/'notes/existing.md').read_text(),'fixture')

if __name__=='__main__':unittest.main()
