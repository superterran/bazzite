import http.client
import importlib.util
import json
from pathlib import Path
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

spec = importlib.util.spec_from_file_location('push', Path(__file__).parents[1] / 'bin/productivity-push.py')
push = importlib.util.module_from_spec(spec)
spec.loader.exec_module(push)


class ApprovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = push.http.server.ThreadingHTTPServer(('127.0.0.1', 0), push.Web)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        push.PENDING.clear()
        push.LAST_REQUEST = 0

    def post(self, path, body, cookie='', origin=push.BASE):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        connection.request('POST', path, body, {'Host': push.BASE[8:], 'Origin': origin, 'Cookie': cookie})
        response = connection.getresponse()
        result = response.status, response.read().decode(), response.getheader('Set-Cookie')
        connection.close()
        return result

    def request(self):
        with patch.object(push, 'notify'):
            self.assertTrue(push.request_unlock()['ok'])
        return next(iter(push.PENDING))

    def claim(self, token):
        status, body, cookie = self.post('/claim', json.dumps({'token': token}))
        self.assertEqual(status, 200)
        self.assertIn('Secure; HttpOnly; SameSite=Strict', cookie)
        return json.loads(body)['csrf'], cookie.split(';')[0]

    def test_link_alone_does_not_unlock_and_claim_is_single_use(self):
        token = self.request()
        with patch.object(push, 'broker') as broker:
            self.claim(token)
            self.assertEqual(self.post('/claim', json.dumps({'token': token}))[0], 410)
            broker.assert_not_called()

    def test_expiration_origin_and_notification_rate_limit(self):
        token = self.request()
        self.assertFalse(push.request_unlock()['ok'])
        self.assertEqual(self.post('/claim', json.dumps({'token': token}), origin='https://attacker.invalid')[0], 403)
        push.PENDING[token]['expires'] = time.monotonic() - 1
        self.assertEqual(self.post('/claim', json.dumps({'token': token}))[0], 410)

    def test_csrf_and_cookie_required_then_success_cannot_be_replayed(self):
        token = self.request()
        csrf, cookie = self.claim(token)
        body = urlencode({'username': 'desktop-secure', 'password': 'test-only', 'csrf': csrf})
        with patch.object(push, 'broker', return_value=True) as broker:
            self.assertEqual(self.post('/unlock', body)[0], 400)
            self.assertEqual(self.post('/unlock', body.replace(csrf, 'wrong'), cookie)[0], 403)
            broker.assert_not_called()
            self.assertEqual(self.post('/unlock', body, cookie)[0], 200)
            self.assertEqual(self.post('/unlock', body, cookie)[0], 403)
            broker.assert_called_once_with('test-only')

    def test_three_attempt_limit(self):
        csrf, cookie = self.claim(self.request())
        body = urlencode({'username': 'desktop-secure', 'password': 'incorrect', 'csrf': csrf})
        with patch.object(push, 'broker', return_value=False) as broker:
            for _ in range(3):
                self.assertEqual(self.post('/unlock', body, cookie)[0], 401)
            self.assertEqual(self.post('/unlock', body, cookie)[0], 403)
            self.assertEqual(broker.call_count, 3)

    def test_delivery_failure_revokes_request(self):
        with patch.object(push, 'notify', side_effect=RuntimeError('private transport detail')):
            result = push.request_unlock()
        self.assertFalse(result['ok'])
        self.assertNotIn('private', json.dumps(result))
        self.assertEqual(push.PENDING, {})

if __name__ == '__main__':
    unittest.main()
