import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
import httpx

from fastapi.testclient import TestClient
import app as console


class ConsoleTests(unittest.TestCase):
    def setUp(self):
        console.SESSIONS.clear(); console.LOGIN_ATTEMPTS.clear(); console.PLANS.clear()
        self.c = TestClient(console.app, base_url='http://127.0.0.1:7788')
        self.origin = {'Origin': 'http://127.0.0.1:7788'}

    def login(self):
        r = self.c.post('/api/login', headers=self.origin, json={'token': console.BOOTSTRAP_TOKEN})
        self.assertEqual(r.status_code, 200)
        self.assertIn('HttpOnly', r.headers['set-cookie'])
        return {**self.origin, 'X-Console-CSRF': r.json()['csrf']}

    def test_auth_origin_and_csrf(self):
        self.assertEqual(self.c.get('/api/files').status_code, 401)
        self.assertEqual(self.c.get('/admin').status_code, 401)
        self.assertEqual(self.c.get('/api/status', headers={'Host': 'attacker.example'}).status_code, 400)
        headers = self.login()
        self.assertEqual(self.c.get('/api/files').status_code, 200)
        self.assertEqual(self.c.post('/api/deploy/api', headers={'Origin': 'http://evil.example'}, json={'dry_run': True}).status_code, 403)
        self.assertEqual(self.c.post('/api/deploy/api', headers=self.origin, json={'dry_run': True}).status_code, 403)
        self.assertEqual(self.c.post('/api/deploy/api', headers=headers, json={'dry_run': True}).status_code, 200)
        self.assertEqual(self.c.post('/api/logout', headers=headers).status_code, 200)
        self.assertEqual(self.c.get('/admin').status_code, 401)

    def test_selective_publish_and_stale_plan(self):
        headers = self.login()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / 'workready-portal').mkdir()
            path = root / 'workready-portal/config.js'; path.write_text('example')
            calls = []
            def git(repo, *args):
                calls.append(args)
                if args[:2] == ('rev-parse', 'HEAD'): return 'head'
                if args[:2] == ('branch', '--show-current'): return 'main'
                return ''
            with patch.object(console, 'ROOT', root), patch.object(console, 'git', git):
                plan = {'paths': ['workready-portal/config.js'], 'repos': ['workready-portal'], 'owner': headers['X-Console-CSRF'], 'expires': time.monotonic()+100}
                plan['stamp'] = console.fingerprint(plan['paths'], plan['repos'])
                console.PLANS['test'] = plan
                path.write_text('changed after review')
                self.assertEqual(self.c.post('/api/deploy/site', headers=headers, json={'plan': 'test'}).status_code, 409)
                plan['stamp'] = console.fingerprint(plan['paths'], plan['repos'])
                self.assertEqual(self.c.post('/api/deploy/site', headers=headers, json={'plan': 'test'}).status_code, 200)
                self.assertIn(('add', '--', 'config.js'), calls)
                self.assertFalse(any('-A' in call for call in calls))

    def test_preview_cannot_post_or_connect_to_production(self):
        with TestClient(console.preview_app, base_url='http://localhost:7789') as preview:
            self.assertEqual(preview.post('/api/deploy/site').status_code, 405)
            response = preview.get('/missing')
            self.assertIn("connect-src 'self'", response.headers['content-security-policy'])
            self.assertIn("form-action 'none'", response.headers['content-security-policy'])

    def test_admin_proxy_keeps_credential_server_side(self):
        headers = self.login()
        r = self.c.get('/api/admin/health')
        self.assertEqual(r.status_code, 401)
        self.assertNotIn('admin_token', self.c.get('/api/session').json())
        with patch.object(console.httpx, 'Client') as remote:
            remote.return_value.__enter__.return_value.get.return_value = httpx.Response(200, json={'status': 'ok'})
            connected = self.c.post('/api/admin/connect', headers=headers, json={'token': 'sensitive-admin-token'})
        self.assertEqual(connected.status_code, 200)
        transport = AsyncMock(return_value=httpx.Response(200, json={'status': 'ok'}))
        with patch.object(console.httpx, 'AsyncClient') as remote:
            remote.return_value.__aenter__.return_value.request = transport
            response = self.c.get('/api/admin/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(transport.call_args.kwargs['headers']['Authorization'], 'Bearer sensitive-admin-token')
        self.assertNotIn('sensitive-admin-token', self.c.get('/api/session').text)

    def test_preset_validation_and_expansion(self):
        self.assertEqual(console.validate_pacing({'SIMULATION_PRESET': 'workshop'})['LUNCHROOM_INVITE_LEAD_HOURS'], '0')
        self.assertEqual(console.validate_pacing({'SIMULATION_PRESET': 'semester'})['TASK_FEEDBACK_DELAY_MINUTES'], '120')
        with self.assertRaises(ValueError):
            console.validate_pacing({'WORKREADY_ADMIN_TOKEN': 'secret'})


if __name__ == '__main__':
    unittest.main()
