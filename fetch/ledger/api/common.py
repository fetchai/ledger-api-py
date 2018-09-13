import requests
import json


class ApiEndpoint(object):
    def __init__(self, host, port, version):
        self._host = str(host)
        self._port = int(port)
        self._version = int(version)
        self._session = requests.session()

    @property
    def api_version(self):
        return self._version

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    def _post(self, endpoint, data=None):
        """

        :param str endpoint:
        :param data:
        :return:
        """
        if data is None:
            data = dict()

        # string leading '/'
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]

        # format and make the request
        url = 'http://{}:{}/{}'.format(self.host, self.port, endpoint)
        raw_response = self._session.post(url, json=data)

        # check the status code
        if 200 <= raw_response.status_code < 300:
            response = json.loads(raw_response.text)
            return True, response

        return False, None