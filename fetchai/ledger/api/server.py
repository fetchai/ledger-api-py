from .common import ApiEndpoint
from base64 import b64encode

class ServerApi(ApiEndpoint):

    def status(self):
        """
        Gets the status of a constellation server

        :return: dict of info returned by the /api/status endpoint
        """
        url = '{}://{}:{}/api/status'.format(self.protocol, self.host, self.port)
        raw_resp = self._session.get(url)
        try:
            response = raw_resp.json()
        except:
            try:
                str_resp = raw_resp.decode()
            except:
                str_resp = b64encode(raw_res).decode()

            response = {"error": str_resp}

        return response

    def num_lanes(self):
        """Queries the ledger for the number of lanes currently active"""
        return self.status()['lanes']

    def version(self):
        return self.status()['version']
