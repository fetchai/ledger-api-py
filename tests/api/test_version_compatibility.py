from unittest import TestCase

from fetchai.ledger.api import check_version_compatibility


class VersionCompatibilityTests(TestCase):
    def test_build_version(self):
        check_version_compatibility('v0.11.0-alpha10-3-gecd810986', ['>=0.11.0-alpha.7'])

    def test_simple_range_with_build(self):
        check_version_compatibility('v0.11.0-alpha10-3-gecd810986', ['>=0.11.0-alpha.7', '<0.11.0-alpha.11'])

    def test_without_build_number(self):
        check_version_compatibility('v0.11.0-alpha10', ['>=0.11.0-alpha.10', '<0.11.0-alpha.11'])
