# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------
from .common import ApiEndpoint, ApiError


class ServerApi(ApiEndpoint):

    def status(self):
        """
        Gets the status of a constellation server

        :return: dict of info returned by the /api/status endpoint
        """
        url = '{}://{}:{}/api/status'.format(self.protocol, self.host, self.port)

        response = self._session.get(url)
        if not 200 <= response.status_code < 300:
            raise ApiError('Error accessing status URL: {}'.format(url))

        try:
            response = response.json()
        except Exception as ex:
            raise ApiError('Error decoding response from status API: {}'.format(ex))

        return response

    def num_lanes(self):
        """Queries the ledger for the number of lanes currently active"""
        return self.status()['lanes']

    def version(self):
        return self.status()['version']
