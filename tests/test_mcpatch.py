import copy
import importlib.util
import io
import json
import ssl
import unittest
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/mcd-patch/scripts'


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


engine = module('diagnose')
mcp = module('mcp_readonly')


class DiagnosisTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'skills/mcd-patch/examples/demo.json').read_text())
        self.now = engine.timestamp(self.data['demo_now'])

    def run_case(self):
        return engine.diagnose(self.data, allow_demo=True, now=self.now)

    def test_minimal_changes_preserve_distinct_preferences(self):
        result = self.run_case()
        self.assertEqual(result['status'], 'needs_change')
        self.assertEqual({x['id'] for x in result['patches']}, {'A', 'B', 'C'})
        self.assertNotIn('D', [x['id'] for x in result['patches']])
        self.assertEqual(result['excluded'][0]['id'], 'E')

    def test_higher_budget_keeps_every_requirement(self):
        self.data['budget_cents'] = 4600
        result = self.run_case()
        self.assertEqual(result['status'], 'feasible')
        self.assertEqual([x['id'] for x in result['feasible']], ['A'])
        self.assertEqual(result['patches'], [])

    def test_never_relax_locked_requirement(self):
        self.data['candidates'] = [self.data['candidates'][0]]
        self.data['candidates'][0]['checks']['p2-main']['status'] = 'fail'
        result = self.run_case()
        self.assertFalse(result['patches'])
        self.assertFalse(result['feasible'])

    def test_missing_check_is_unknown(self):
        self.data['candidates'] = [self.data['candidates'][0]]
        del self.data['candidates'][0]['checks']['p2-main']
        self.assertFalse(self.run_case()['patches'])

    def test_missing_evidence_blocks_recommendation(self):
        self.data['candidates'] = [self.data['candidates'][0]]
        self.data['candidates'][0]['checks']['p1-main']['evidence'] = ''
        self.assertFalse(self.run_case()['patches'])

    def test_stale_and_future_prices_are_excluded(self):
        for delta in (timedelta(minutes=20), timedelta(minutes=-20)):
            result = engine.diagnose(self.data, allow_demo=True, now=self.now + delta)
            self.assertEqual(len(result['excluded']), 5)
            self.assertFalse(result['patches'])

    def test_different_store_cannot_reuse_price(self):
        self.data['context']['store_id'] = 'OTHER'
        self.assertEqual(len(self.run_case()['excluded']), 5)

    def test_money_is_nonnegative_integer_not_bool_or_float(self):
        for value in (True, -1, 39.99):
            self.data['budget_cents'] = value
            with self.assertRaises(ValueError):
                self.run_case()

    def test_demo_requires_explicit_flag(self):
        with self.assertRaises(ValueError):
            engine.diagnose(self.data, now=self.now)

    def test_live_mode_uses_current_clock(self):
        self.data['mode'] = 'live'
        result = engine.diagnose(self.data, now=self.now + timedelta(days=1))
        self.assertFalse(result['patches'])

    def test_equivalent_patch_keeps_cheaper_representative(self):
        duplicate = copy.deepcopy(self.data['candidates'][1])
        duplicate['id'] = 'B2'
        duplicate['quote']['total_cents'] = 3800
        self.data['candidates'].append(duplicate)
        ids = {x['id'] for x in self.run_case()['patches']}
        self.assertIn('B2', ids)
        self.assertNotIn('B', ids)


class TransportTests(unittest.TestCase):
    def test_sse_ignores_notifications_and_wrong_ids(self):
        stream = io.BytesIO(b': ping\n\ndata: {"method":"notifications/progress"}\n\n'
                            b'data: {"id":2,"result":{}}\n\n'
                            b'data: {"id":1,\n'
                            b'data: "result":{"ok":true}}\n\n')
        self.assertEqual(mcp.read_sse(stream, 1)['result'], {'ok': True})

    def test_truncated_stream_is_failure(self):
        with self.assertRaises(mcp.MCPError):
            mcp.read_sse(io.BytesIO(b': ping\n\n'), 1)

    def test_mutations_are_denied_before_network(self):
        client = mcp.Client('unit-test-not-a-credential')
        for name in ('create-order', 'auto-bind-coupons', 'mall-create-order', 'draw-lottery'):
            with self.assertRaises(mcp.MCPError):
                client.call(name, {}, [])

    def test_required_parameters_are_discovered(self):
        client = mcp.Client('unit-test-not-a-credential')
        tools = [{'name': 'query-meals', 'inputSchema': {'required': ['store']}}]
        with self.assertRaises(mcp.MCPError):
            client.call('query-meals', {}, tools)

    def test_redirect_does_not_forward_token(self):
        with self.assertRaises(mcp.MCPError):
            mcp.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.org')

    def test_system_certificate_fallback_keeps_verification(self):
        context = mcp.tls_context()
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertGreater(context.cert_store_stats()['x509_ca'], 0)

    def test_business_failure_is_not_successful_query(self):
        client = mcp.Client('unit-test-not-a-credential')
        client.rpc = lambda *a, **k: {'isError': False, 'structuredContent': {'success': False}}
        with self.assertRaises(mcp.MCPError):
            client.call('now-time-info', {}, [{'name': 'now-time-info'}])


if __name__ == '__main__':
    unittest.main()
