import sys
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import desktop_bridge

class DesktopBridgeTests(unittest.TestCase):
    def test_one_rpc_line_even_with_windows_line_ending(self):
        with patch.object(desktop_bridge.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='{"jsonrpc":"2.0","id":1,"result":{}}\n')) as process:
            result=desktop_bridge.run(['fixture-ssh'],'{"id":1}\r\n')
        self.assertEqual(process.call_args.kwargs['input'],'{"id":1}\n')
        self.assertEqual(result['id'],1)

    def test_notifications_do_not_invent_a_response(self):
        with patch.object(desktop_bridge.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='')):
            self.assertIsNone(desktop_bridge.run(['fixture-ssh'],'{"method":"notifications/initialized"}'))

    def test_connection_failure_does_not_leak_transport_errors(self):
        with patch.object(desktop_bridge.subprocess,'run',return_value=SimpleNamespace(returncode=255,stdout='')):
            with self.assertRaisesRegex(ValueError,'AuroraLAB indisponível'):desktop_bridge.run(['fixture-ssh'],'{}')

if __name__=='__main__':unittest.main()
