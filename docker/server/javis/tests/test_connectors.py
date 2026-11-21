import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import Problem, authorize
from connector import fitness_summary
from tools import validate, catalog
import mcp_service
import stdio_bridge


class ConnectorTests(unittest.TestCase):
    def test_tool_scope_follows_grants(self):
        self.assertEqual([x['name'] for x in catalog({'opengym': 'fixture'})], ['aurora_fitness_summary'])
        self.assertEqual(catalog({}), [])

    def test_no_write_or_shell_tool(self):
        for name in ('bash', 'aurora_finance_add', 'print_start'):
            with self.assertRaises(Problem):
                validate(name, {})

    def test_unknown_parameters_are_rejected(self):
        with self.assertRaises(Problem):
            validate('aurora_recipes', {'url': 'http://example.invalid'})

    def test_invalid_dates_and_boolean_limits(self):
        for args in ({'start': '2026-02-30', 'end': '2026-03-01'}, {'start': '2026-01-01', 'end': '2026-02-01', 'limit': True}):
            with self.assertRaises(Problem):
                validate('aurora_fitness_summary', args)

    def test_last_five_and_absent_measurements(self):
        rows = [{'d': f'2026-01-{i:02d}', 'start': i*100000000, 'end': i*100000000+60000, 'name': 'Fixture', 'garminActivity': {'calories': 20} if i % 2 else {}} for i in range(1, 8)]
        result = fitness_summary({'workouts': rows}, {'start': '2026-01-01', 'end': '2026-01-31', 'limit': 5})
        self.assertEqual([r['date'] for r in result['workouts']], ['2026-01-07','2026-01-06','2026-01-05','2026-01-04','2026-01-03'])
        self.assertEqual((result['count'], result['totalMinutes'], result['knownCalories'], result['missingCalories']), (5, 5, 60, 2))

    def test_private_rpc_denies_wrong_token(self):
        with self.assertRaises(Problem):
            authorize({'Authorization': 'Bearer nope'}, 'x'*48)

    def test_mcp_lists_only_current_permissions(self):
        cfg = {'token': 'x'*48}
        with patch.object(mcp_service, 'configuration', return_value=cfg), patch.object(mcp_service, 'grants', return_value={}):
            result = mcp_service.dispatch('POST', '/mcp', {'Authorization': 'Bearer '+'x'*48}, {'id': 1, 'method': 'tools/list'})
        self.assertEqual(result['result']['tools'], [])

    def test_revoked_grant_blocks_connector_call(self):
        cfg = {'token': 'x'*48}
        with patch.object(mcp_service, 'configuration', return_value=cfg), patch.object(mcp_service, 'grants', return_value={}):
            result = mcp_service.dispatch('POST', '/mcp', {'Authorization': 'Bearer '+'x'*48}, {'id': 1, 'method': 'tools/call', 'params': {'name': 'aurora_recipes', 'arguments': {}}})
        self.assertTrue(result['result']['isError'])

    def test_bridge_rejects_arbitrary_tools_and_paths(self):
        for name, args in [('bash', {}), ('javis_read_file', {'path': '../secret'}), ('javis_write_file', {'path': 'config.json', 'content': 'bad'})]:
            with self.assertRaises(ValueError):
                stdio_bridge.validate({'method': 'tools/call', 'params': {'name': name, 'arguments': args}})


if __name__ == '__main__':
    unittest.main()
