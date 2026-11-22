import inspect
from pathlib import Path
import sys
import unittest
import asyncio
import types
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import gemini_egress
import gemini_runtime

class GeminiIsolationTests(unittest.TestCase):
    def test_only_google_api_tls_destination_is_allowed(self):
        self.assertTrue(gemini_egress.allowed('generativelanguage.googleapis.com:443'))
        for host in ('google.com:443','generativelanguage.googleapis.com:80','127.0.0.1:443','generativelanguage.googleapis.com.evil.invalid:443','user@generativelanguage.googleapis.com:443'):
            self.assertFalse(gemini_egress.allowed(host))
    def signature(self):
        def original(mode='full',vault_root=None,include_plugins=True,include_ambient=False,staging=False,workspace_root=None,coding_ctx_cua_phien=None,force_lazy=False,tool_allowlist=None):pass
        return inspect.signature(original)
    def test_native_tool_scope_cannot_expand_vault_or_add_shell(self):
        values=gemini_runtime.scoped(self.signature(),('full','/etc'),{'include_plugins':True,'workspace_root':['/'],'staging':True,'tool_allowlist':['*']})
        self.assertEqual(values['vault_root'],'/brains/auroralab')
        self.assertFalse(values['include_plugins']);self.assertFalse(values['staging']);self.assertIsNone(values['workspace_root'])
        self.assertEqual(values['tool_allowlist'],list(gemini_runtime.READ_TOOLS))
        self.assertNotIn('javis_write_file',values['tool_allowlist'])
    def test_requested_scope_is_intersected_not_replaced(self):
        self.assertEqual(gemini_runtime.scoped(self.signature(),(),{'tool_allowlist':['javis_read_file','bash']})['tool_allowlist'],['javis_read_file'])
        self.assertEqual(gemini_runtime.scoped(self.signature(),(),{'tool_allowlist':[]})['tool_allowlist'],[])
    def test_native_fn_namespace_is_preserved_and_inventory_is_filtered(self):
        sample=[{'fn':'auroralab__aurora_recipes','name':'aurora_recipes'},{'fn':'bash','name':'bash'}]
        def inventory(mode='full',vault_root=None):return sample,{'auroralab__aurora_recipes':{},'bash':{}}
        async def discover(mode='full',vault_root=None,tool_allowlist=None):return inventory()
        async def fetch(provider,settings):return []
        hub=types.SimpleNamespace(discover_all=discover,registry_inventory=inventory)
        main=types.SimpleNamespace(_fetch_provider_models=fetch)
        with patch.dict(sys.modules,{'mcp_hub':hub}):gemini_runtime.install(main)
        tools,route=asyncio.run(hub.discover_all('full',vault_root='/etc'))
        self.assertEqual([x['fn'] for x in tools],['auroralab__aurora_recipes'])
        self.assertEqual(list(route),['auroralab__aurora_recipes'])
        tools,route=hub.registry_inventory('full',vault_root='/etc')
        self.assertEqual([x['fn'] for x in tools],['auroralab__aurora_recipes'])
        self.assertNotIn('bash',route)

if __name__=='__main__':unittest.main()
