from .common import ApiEndpoint


class ServerApi(ApiEndpoint):

    def status(self):
        """
        Gets the status of a constellation server

        :return: dict of info returned by the /api/status endpoint
        """
        url = 'http://{}:{}/api/status'.format(self.host, self.port)

        response = self._session.get(url).json()

        return response

    def num_lanes(self):
        """Queries the ledger for the number of lanes currently active"""
        return self.status()['lanes']
