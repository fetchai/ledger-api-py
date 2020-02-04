from unittest import TestCase
from unittest.mock import MagicMock

from fetchai.ledger.api.server import ServerApi, ApiError


class MockRequestResponse:
    def __init__(self, value, status_code=None, throw=False):
        self._value = value
        self._raise = bool(throw)
        self.status_code = status_code or 200

    def json(self):
        if self._raise:
            raise RuntimeError('Simulating JSON decode error')
        return self._value


class TokenAPITests(TestCase):
    def setUp(self) -> None:
        self.api = ServerApi('127.0.0.1', 9090)

    def test_status_call(self):
        data = {}

        self.api._session = MagicMock()
        self.api._session.get.side_effect = [MockRequestResponse(data)]

        resp = self.api.status()
        self.assertEqual(data, resp)

        self.api._session.get.assert_called_once_with('http://127.0.0.1:9090/api/status')

    def test_status_call_failure(self):
        self.api._session = MagicMock()
        self.api._session.get.side_effect = [MockRequestResponse({}, 400)]

        with self.assertRaises(ApiError):
            self.api.status()

        self.api._session.get.assert_called_once_with('http://127.0.0.1:9090/api/status')

    def test_status_call_json_decode_error(self):
        self.api._session = MagicMock()
        self.api._session.get.side_effect = [MockRequestResponse({}, throw=True)]

        with self.assertRaises(ApiError):
            self.api.status()

        self.api._session.get.assert_called_once_with('http://127.0.0.1:9090/api/status')

    def test_num_lanes(self):
        self.api.status = MagicMock()
        self.api.status.side_effect = [dict(lanes=2048)]

        self.assertEqual(self.api.num_lanes(), 2048)

    def test_version(self):
        self.api.status = MagicMock()
        self.api.status.side_effect = [dict(version='the wise mans fear')]

        self.assertEqual(self.api.version(), 'the wise mans fear')
