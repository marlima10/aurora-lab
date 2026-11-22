import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import locale_runtime

class PortugueseTests(unittest.TestCase):
    def test_portuguese_is_a_full_native_locale(self):
        import lang_registry
        locale_runtime.register()
        self.assertEqual(lang_registry.chuan_hoa('pt-BR'),'pt')
        lang=lang_registry.get('pt')
        self.assertEqual(lang.number_locale,'pt-BR')
        self.assertEqual(lang.stt,'pt')
        self.assertEqual(lang.tts['edge'],'pt-BR-FranciscaNeural')
        self.assertEqual(len(lang.weekdays),7)

    def test_portuguese_speech_never_becomes_vietnamese(self):
        import edge_tts,phien_am
        with patch.dict(__import__('os').environ,{'HTTPS_PROXY':'http://fixed-proxy.invalid:3128'}):
            locale_runtime.voice_proxy()
            for hint in (None,True,False):
                for voice in ('pt-BR-FranciscaNeural','pt-BR-AntonioNeural'):
                    self.assertEqual(phien_am.speech_plan('Olá, seus treinos estão aqui.',voice,hint),('Olá, seus treinos estão aqui.',voice))
            obj=edge_tts.Communicate('Teste em português','pt-BR-FranciscaNeural')
            self.assertEqual(obj.proxy,'http://fixed-proxy.invalid:3128')

    def test_dictionary_covers_upstream_and_preserves_placeholders(self):
        translated=json.loads((Path(__file__).resolve().parents[1]/'pt.json').read_text())
        original=json.loads(Path('/app/dashboard/i18n/en.json').read_text())
        self.assertTrue(set(original).issubset(translated))
        for key,value in original.items():
            self.assertIsInstance(translated[key],str)
            self.assertEqual(sorted(re.findall(r'\{\w+\}',value)),sorted(re.findall(r'\{\w+\}',translated[key])),key)

if __name__=='__main__':unittest.main()
