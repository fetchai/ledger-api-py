#
#------------------------------------------------------------------------------
#
#   Copyright 2018 Fetch.AI Limited
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
#------------------------------------------------------------------------------


from fetch.ledger.chain import Tx
from fetch.ledger.crypto import Signing

import pytest
import unittest

import binascii
import io
import hashlib
import base64
import json

import string
import random

class TxTest(unittest.TestCase):

    def setUp(self):
        self.private_key = Signing.privKeyFromBin(base64.b64decode("7fDTiiCsCKG43Z8YlNelveKGwir6EpCHUhrcHDbFBgg="))

    @classmethod
    def generate_random_string(cls, size=6, chars=string.ascii_letters + string.digits):
       return ''.join(random.choice(chars) for x in range(size))

    @classmethod
    def generate_random_tx(cls, private_keys = None, resources_count=1):
        tx = Tx()
        tx.contract_name = cls.generate_random_string(10).encode()
        tx.fee = random.randint(0, 10000)

        resources = set()
        for _ in range(0, resources_count):
            resources.add(cls.generate_random_string(10).encode())
        tx.resources = resources

        tx.data = cls.generate_random_string(10).encode()

        if private_keys is None:
            private_keys=[]
            private_keys.append(Signing.generatePrivKey().to_string())

        for pk in private_keys:
            tx.sign(pk)

        return tx

    @classmethod
    def verify_wire_tx(cls, tx_in_wire_format, verbose_dbg_output=False):
        if verbose_dbg_output:
            print("ORIG  Tx wire:\n{}".format(tx_in_wire_format))

        tx = Tx.fromWireFormat(tx_in_wire_format)
        if verbose_dbg_output:
            print("DESER Tx wire:\n{}".format(tx))

        is_verified = tx.verify()
        print("DESER Tx: verified = {}".format(is_verified))

        #if not is_verified:
        #    raise RuntimeError("Transaction failed to verify")
        return is_verified

    def test_basic_sign_verify_cycle(self):
        contract_name = b'contract name'
        fee = 2
        resources = set([b'res 1', b'res 0'])
        data = b'contract data'

        tx = Tx(contract_name=contract_name, fee=fee, resources=resources, data=data)
        tx.sign(private_key=self.private_key)

        tx_des = Tx()
        stream = io.BytesIO()
        with stream:
            stream.seek(0)
            tx.serialise(stream)

            stream.seek(0)
            tx_des.deserialise(stream)

        assert tx_des.verify, "Tx: {}".format(tx)
        assert tx_des == tx

    def test_basic_to_from_wire_format_cycle(self):
        contract_name = b'contract name'
        fee = 2
        resources = set([b'res 1', b'res 0'])
        data = b'contract data'

        tx = Tx(contract_name=contract_name, fee=fee, resources=resources, data=data)
        tx.sign(private_key=self.private_key)

        tx_wire = tx.toWireFormat(True)
        tx_des = Tx.fromWireFormat(tx_wire)

        assert tx_des.verify, "Tx: {}".format(tx)
        assert tx_des == tx

    def test_sign_verify_cycle_for_random_generated_transactions(self):
        private_keys = []

        for _ in range(0, random.randint(1,5)):
            private_keys.append(Signing.generatePrivKey())

        for _ in range(0, 5):
            tx = self.generate_random_tx(private_keys=private_keys, resources_count=random.randint(1,5))
            assert tx.verify(), "Tx: {}".format(tx)

    def test_sign_to_from_wire_verify_cycle_for_random_generated_transactions(self):
        private_keys = []

        for _ in range(0, random.randint(1,5)):
            private_keys.append(Signing.generatePrivKey())

        for _ in range(0, 5):
            tx = self.generate_random_tx(private_keys=private_keys, resources_count=random.randint(1,5))
            tx_wire = tx.toWireFormat(include_metadata=True)
            tx_des = Tx.fromWireFormat(tx_wire)

            assert tx.verify(), "Tx: {}\n{}".format(tx, tx_wire)
            assert tx_des.verify(), "Tx: {}".format(tx_des)
            assert tx_des == tx, "Tx:\n{}\nTx des:\n{}".format(tx, tx_des)

    def test_verify_wire_transactions_generated_by_cpp_ecosystem(self):
        transactions_generated_by_cpp_ecosystem =[
            '{"ver": "1.0", "metadata": {"data": "MTE5ODUwNTkwNTYyNzEwNDUxOTA=", "fee": 1134839535, "contract_name": "10600339527879263983", "resources": ["MTEzMjc0MTMwMTMxNjc3MzA5MzU=", "MTIwMzY1MTQ1MzY2MTk2MzA0NzU=", "MTg4NzI0MTQyNzIyNDIyMTUzNg=="], "signatures": [{"QAAAAAAAAAD9R1pSSrM+hNiofmysOh/XxIsSzHAVrvV0z7JLOrur0hS45AX75sCGHWtpoII4/NYd3JbEenU0X0dMfmQp5eKGCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAABfM22/2Igv+t1PFnlfDa1XA8bC+2SPOoFyswLNxN5F8DBdgaNcH19pTXXfFL6KMrbo4X/Jc/kxR0H59KIOLEPwCQAAAAAAAABzZWNwMjU2azE="}]}, "data": "FAAAAAAAAAAxMDYwMDMzOTUyNzg3OTI2Mzk4M+9GpEMAAAAAAwAAAAAAAAAUAAAAAAAAADExMzI3NDEzMDEzMTY3NzMwOTM1FAAAAAAAAAAxMjAzNjUxNDUzNjYxOTYzMDQ3NRMAAAAAAAAAMTg4NzI0MTQyNzIyNDIyMTUzNhQAAAAAAAAAMTE5ODUwNTkwNTYyNzEwNDUxOTABAAAAAAAAAEAAAAAAAAAA/UdaUkqzPoTYqH5srDof18SLEsxwFa71dM+ySzq7q9IUuOQF++bAhh1raaCCOPzWHdyWxHp1NF9HTH5kKeXihgkAAAAAAAAAc2VjcDI1NmsxQAAAAAAAAABfM22/2Igv+t1PFnlfDa1XA8bC+2SPOoFyswLNxN5F8DBdgaNcH19pTXXfFL6KMrbo4X/Jc/kxR0H59KIOLEPwCQAAAAAAAABzZWNwMjU2azE="}',

            '{"ver": "1.0", "metadata": {"data": "MTM0NzA1MzYyNjQzODE5NDQwNjE=", "fee": 6973127472713372808, "contract_name": "17622906998505930329", "resources": ["MTUzNDc5MDk4NjUzNjcxMTgwMDg=", "MTcxMzcwNTE1NjQ2MDM1NDAxMzc=", "MjcyMTAyMDM3NTc1MTczNjk2Mw=="], "signatures": [{"QAAAAAAAAAA1o3WNRItzCTpQ9SPC/iltiS1ZVaq3v0RUqXoMo+pOfZCzjTrdbpEwbDzRwUCtd1I7d1mun3BBGO6ZYNmzdJLuCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAACZ5SDG9uHNs7qZF3DHK6b9sZevEZeCWmKkofqijJ2bi9P0mKomGpyXSelv6jGj+XofVhKyQVZZgUFBMZrNhDqVCQAAAAAAAABzZWNwMjU2azE="}, {"QAAAAAAAAAA4u/NuBkQ1PGX8Sti59ZtOnyY5EsixqZ5xJEJtpk6HVRphL/OQqj+JQiTClFNbtyX1ROYsVclDVYXZoUyMTAmpCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAAAizwXq/l7xT0mbx/EEDXranOZDqsh3rNItIOriz6kLRjrTtfaraj65bS+R9O9z9m8iIE+3HSkLj7cbn1x2O/cVCQAAAAAAAABzZWNwMjU2azE="}, {"QAAAAAAAAAAelCR4rAdGFcF0YfU6SRvGtueG8Yf7ku9yXej+Gq/jBkvA4zS+kv+aX5PqGGPJe3C9yYsH8U41/p4bOwqYTLilCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAAANbhJ14ODxMXqHI5h5IjRe9+xjSOzLSzL+RInqjsxlgNUgUZRPXiDd6YXgAybA6blxajpAE2SHxewfQW6sEtqhCQAAAAAAAABzZWNwMjU2azE="}]}, "data": "FAAAAAAAAAAxNzYyMjkwNjk5ODUwNTkzMDMyOYgUmcB9hsVgAwAAAAAAAAAUAAAAAAAAADE1MzQ3OTA5ODY1MzY3MTE4MDA4FAAAAAAAAAAxNzEzNzA1MTU2NDYwMzU0MDEzNxMAAAAAAAAAMjcyMTAyMDM3NTc1MTczNjk2MxQAAAAAAAAAMTM0NzA1MzYyNjQzODE5NDQwNjEDAAAAAAAAAEAAAAAAAAAANaN1jUSLcwk6UPUjwv4pbYktWVWqt79EVKl6DKPqTn2Qs4063W6RMGw80cFArXdSO3dZrp9wQRjumWDZs3SS7gkAAAAAAAAAc2VjcDI1NmsxQAAAAAAAAACZ5SDG9uHNs7qZF3DHK6b9sZevEZeCWmKkofqijJ2bi9P0mKomGpyXSelv6jGj+XofVhKyQVZZgUFBMZrNhDqVCQAAAAAAAABzZWNwMjU2azFAAAAAAAAAADi7824GRDU8ZfxK2Ln1m06fJjkSyLGpnnEkQm2mTodVGmEv85CqP4lCJMKUU1u3JfVE5ixVyUNVhdmhTIxMCakJAAAAAAAAAHNlY3AyNTZrMUAAAAAAAAAAIs8F6v5e8U9Jm8fxBA162pzmQ6rId6zSLSDq4s+pC0Y607X2q2o+uW0vkfTvc/ZvIiBPtx0pC4+3G59cdjv3FQkAAAAAAAAAc2VjcDI1NmsxQAAAAAAAAAAelCR4rAdGFcF0YfU6SRvGtueG8Yf7ku9yXej+Gq/jBkvA4zS+kv+aX5PqGGPJe3C9yYsH8U41/p4bOwqYTLilCQAAAAAAAABzZWNwMjU2azFAAAAAAAAAAA1uEnXg4PExeocjmHkiNF737GNI7MtLMv5EieqOzGWA1SBRlE9eIN3pheADJsDpuXFqOkATZIfF7B9BbqwS2qEJAAAAAAAAAHNlY3AyNTZrMQ=="}',

            '{"ver": "1.0", "metadata": {"data": "MjY0NjE4MTk1Nzc5MzQ2MTAyMw==", "fee": -1367423982844084623, "contract_name": "6529243440370974146", "resources": ["MTQwOTY1NjQ1MzY3OTQwODI1NjE=", "MTgyNTE0MTUwMzQ3MTQ0MjI5NA==", "NDQ5Njk0Mzk4NzQ0ODg3NTExNQ=="], "signatures": [{"QAAAAAAAAAAn1WbujVXFOwOj20nv11YROev4zfFYB8r50tAN8teIsRYkYmvT0g0FZCqleY4qVQp0IqenOd6Cjm6MDlcTbOlACQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAAAOb2p4JdUvpk8alPzt0YWK68YDjr5Dojz6wI2Y1a6th3P6pfvCBZaOT/d+Xrurw73BrJkAj52UntAHG64lWe/nCQAAAAAAAABzZWNwMjU2azE="}, {"QAAAAAAAAABWWqzNh8Dh+EybAfG+WyEhKicPWsti2RFUHfHYmLYbYAJBrgynu8z+xt0TKNCKXgyJ1/7vdPIvSlkiwmpRaF4DCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAABjz0NZgziaecQUcphkoFQ6CFfWwl8fetjTQv3HIH+q7No9KRiFgZbGOtMtnYI2veBI7c3/oI8RU2uI9f92rV8zCQAAAAAAAABzZWNwMjU2azE="}, {"QAAAAAAAAAAXTLJrCrNCYl3NcTHsfey0A16LaMvhPN3+m7c9rTCvajwdTYxzoV17NcbA7EJ9HSYzTZPAPYGOjGADurrdq3hxCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAACM2U8F3Shul8tyBAhBnjgH/YSa69lGuJjtMTdm6vsjlezIwR3uCaQKQKCB+6xotByQc2X5Ylkev3qZcD6NCn+lCQAAAAAAAABzZWNwMjU2azE="}]}, "data": "EwAAAAAAAAA2NTI5MjQzNDQwMzcwOTc0MTQ2cX467SHvBe0DAAAAAAAAABQAAAAAAAAAMTQwOTY1NjQ1MzY3OTQwODI1NjETAAAAAAAAADE4MjUxNDE1MDM0NzE0NDIyOTQTAAAAAAAAADQ0OTY5NDM5ODc0NDg4NzUxMTUTAAAAAAAAADI2NDYxODE5NTc3OTM0NjEwMjMDAAAAAAAAAEAAAAAAAAAAJ9Vm7o1VxTsDo9tJ79dWETnr+M3xWAfK+dLQDfLXiLEWJGJr09INBWQqpXmOKlUKdCKnpznego5ujA5XE2zpQAkAAAAAAAAAc2VjcDI1NmsxQAAAAAAAAAAOb2p4JdUvpk8alPzt0YWK68YDjr5Dojz6wI2Y1a6th3P6pfvCBZaOT/d+Xrurw73BrJkAj52UntAHG64lWe/nCQAAAAAAAABzZWNwMjU2azFAAAAAAAAAAFZarM2HwOH4TJsB8b5bISEqJw9ay2LZEVQd8diYthtgAkGuDKe7zP7G3RMo0IpeDInX/u908i9KWSLCalFoXgMJAAAAAAAAAHNlY3AyNTZrMUAAAAAAAAAAY89DWYM4mnnEFHKYZKBUOghX1sJfH3rY00L9xyB/quzaPSkYhYGWxjrTLZ2CNr3gSO3N/6CPEVNriPX/dq1fMwkAAAAAAAAAc2VjcDI1NmsxQAAAAAAAAAAXTLJrCrNCYl3NcTHsfey0A16LaMvhPN3+m7c9rTCvajwdTYxzoV17NcbA7EJ9HSYzTZPAPYGOjGADurrdq3hxCQAAAAAAAABzZWNwMjU2azFAAAAAAAAAAIzZTwXdKG6Xy3IECEGeOAf9hJrr2Ua4mO0xN2bq+yOV7MjBHe4JpApAoIH7rGi0HJBzZfliWR6/eplwPo0Kf6UJAAAAAAAAAHNlY3AyNTZrMQ=="}',

            '{"ver": "1.0", "metadata": {"data": "Nzk1NDEwNDcwNTA4MDQ1NzEzNw==", "fee": -8617752852343797544, "contract_name": "2055278979515003637", "resources": ["MTIwODU4ODY3MzQ2OTcyMTU0NDk=", "MTM0NTQ2MjIxNDY2ODczNTgyMDI=", "NTA1NTA1MTE3MDI3NTI1MzExMw=="], "signatures": [{"QAAAAAAAAAAXu2RPNy7RLrizJNb1uK7fngUzB4UXVCaWjzpp7jKQBTdhArd1uiKLNBXHj/tjZSCgol95vWoDNjZQVXSN73j7CQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAABxGcmbhvuhJwIC2eM4NuiXAxoveI7HpOHvMM85BGjAS/ggBSMhOCkvqLfGAHegs34pu8XfbLVhiHIpMOfq/ZMfCQAAAAAAAABzZWNwMjU2azE="}, {"QAAAAAAAAABpeAKo6MeQMK0nk4jTNlACgHObw/GGAyJxm33gvasVuUeOiwfFSc7i9nxeOcbGIHMMuK1ZNVlToKniUwik6EQiCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAADYgZ+XOWXOX1WUub2Y6ZSKLAmk2I31n7TPbZKqUanPd0KMDpkj5Ciedra/21FXvi1tgkOoWB4Z6sX+wo9D3t2cCQAAAAAAAABzZWNwMjU2azE="}, {"QAAAAAAAAABQF/pmeaBpXUiNJcDf8gPxsLH+f+IDm6se0kMoB7CjGbkZNDsrA3VIHuC+j3M/uEvrPicv00nnHZuh0OLw/aoaCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAABNNqkAuuWOCQd0JjPNrVakLlq2MxdUf9O8Kh/EZJvkkfC5WiBq+VPfrYuzmVpOno7KloWqYwvpyBvQrkeCFyiyCQAAAAAAAABzZWNwMjU2azE="}]}, "data": "EwAAAAAAAAAyMDU1Mjc4OTc5NTE1MDAzNjM32EjwiXCXZ4gDAAAAAAAAABQAAAAAAAAAMTIwODU4ODY3MzQ2OTcyMTU0NDkUAAAAAAAAADEzNDU0NjIyMTQ2Njg3MzU4MjAyEwAAAAAAAAA1MDU1MDUxMTcwMjc1MjUzMTEzEwAAAAAAAAA3OTU0MTA0NzA1MDgwNDU3MTM3AwAAAAAAAABAAAAAAAAAABe7ZE83LtEuuLMk1vW4rt+eBTMHhRdUJpaPOmnuMpAFN2ECt3W6Ios0FceP+2NlIKCiX3m9agM2NlBVdI3vePsJAAAAAAAAAHNlY3AyNTZrMUAAAAAAAAAAcRnJm4b7oScCAtnjODbolwMaL3iOx6Th7zDPOQRowEv4IAUjITgpL6i3xgB3oLN+KbvF32y1YYhyKTDn6v2THwkAAAAAAAAAc2VjcDI1NmsxQAAAAAAAAABpeAKo6MeQMK0nk4jTNlACgHObw/GGAyJxm33gvasVuUeOiwfFSc7i9nxeOcbGIHMMuK1ZNVlToKniUwik6EQiCQAAAAAAAABzZWNwMjU2azFAAAAAAAAAANiBn5c5Zc5fVZS5vZjplIosCaTYjfWftM9tkqpRqc93QowOmSPkKJ52tr/bUVe+LW2CQ6hYHhnqxf7Cj0Pe3ZwJAAAAAAAAAHNlY3AyNTZrMUAAAAAAAAAAUBf6ZnmgaV1IjSXA3/ID8bCx/n/iA5urHtJDKAewoxm5GTQ7KwN1SB7gvo9zP7hL6z4nL9NJ5x2bodDi8P2qGgkAAAAAAAAAc2VjcDI1NmsxQAAAAAAAAABNNqkAuuWOCQd0JjPNrVakLlq2MxdUf9O8Kh/EZJvkkfC5WiBq+VPfrYuzmVpOno7KloWqYwvpyBvQrkeCFyiyCQAAAAAAAABzZWNwMjU2azE="}',

            '{"ver": "1.0", "metadata": {"data": "MzM3MjEzMDYwMTcyNDA5Njc5NQ==", "fee": 5744757968086979116, "contract_name": "2662784214362382229", "resources": ["MzkxNTc3MjUwNDI3MzAyOTk1Nw==", "NjgyMDczMTc0MjE5MzYwODc4MA==", "NzgwNzYyMjc2NDY3NDIwOTg2Nw=="], "signatures": [{"QAAAAAAAAAB8nwfV+B/vVM0vYBX1YdiNYydd/K0Xqzz8c6naCK6o67SDURYuimL27Lq5EYQHsXa0ZsSKlQJI4d/RrcIhqq2FCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAAD0jjqKEV+CjQ//RGZOdqHm97L4bRmNsGwPGseMqZCNyy8fqPd/C9XDB7+7Ivc8bykU3pxWg0Pu9BYHvpUmU0vpCQAAAAAAAABzZWNwMjU2azE="}, {"QAAAAAAAAACCrZNXLRL/Ac4wBeir8Q8PR2TYIThBohYCoeKSF3Z0+Vz1xdaZWcS3Z6QkP7UZV6IPlO5y3FSjrWmp3XHpCA1iCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAACEXAGU5cVUThp4tfKhasCcKMGrcHfbjC17vn/tuc6AyeqTgh3x/Wge9OraqVq2rf0baWkfDAZ1t55RTt2CvhBNCQAAAAAAAABzZWNwMjU2azE="}, {"QAAAAAAAAADt7gVf1VkFafGn60OPjh4DSF5BTNta0d4J89WP5+/Y/IC6YGf9vweCV1e7SqMeR/crAKgCp/8gEHC9uE220kS7CQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAAA1JX6Un3lhgD2gyre5FDoVRnQEFGo8LgnK+I+ic8mCRMXlejMXljEU7W/zC98HZXYaeA9OUMs14/bhBw1QyjX6CQAAAAAAAABzZWNwMjU2azE="}]}, "data": "EwAAAAAAAAAyNjYyNzg0MjE0MzYyMzgyMjI5LFJrWO96uU8DAAAAAAAAABMAAAAAAAAAMzkxNTc3MjUwNDI3MzAyOTk1NxMAAAAAAAAANjgyMDczMTc0MjE5MzYwODc4MBMAAAAAAAAANzgwNzYyMjc2NDY3NDIwOTg2NxMAAAAAAAAAMzM3MjEzMDYwMTcyNDA5Njc5NQMAAAAAAAAAQAAAAAAAAAB8nwfV+B/vVM0vYBX1YdiNYydd/K0Xqzz8c6naCK6o67SDURYuimL27Lq5EYQHsXa0ZsSKlQJI4d/RrcIhqq2FCQAAAAAAAABzZWNwMjU2azFAAAAAAAAAAPSOOooRX4KND/9EZk52oeb3svhtGY2wbA8ax4ypkI3LLx+o938L1cMHv7si9zxvKRTenFaDQ+70Fge+lSZTS+kJAAAAAAAAAHNlY3AyNTZrMUAAAAAAAAAAgq2TVy0S/wHOMAXoq/EPD0dk2CE4QaIWAqHikhd2dPlc9cXWmVnEt2ekJD+1GVeiD5TuctxUo61pqd1x6QgNYgkAAAAAAAAAc2VjcDI1NmsxQAAAAAAAAACEXAGU5cVUThp4tfKhasCcKMGrcHfbjC17vn/tuc6AyeqTgh3x/Wge9OraqVq2rf0baWkfDAZ1t55RTt2CvhBNCQAAAAAAAABzZWNwMjU2azFAAAAAAAAAAO3uBV/VWQVp8afrQ4+OHgNIXkFM21rR3gnz1Y/n79j8gLpgZ/2/B4JXV7tKox5H9ysAqAKn/yAQcL24TbbSRLsJAAAAAAAAAHNlY3AyNTZrMUAAAAAAAAAANSV+lJ95YYA9oMq3uRQ6FUZ0BBRqPC4JyviPonPJgkTF5XozF5YxFO1v8wvfB2V2GngPTlDLNeP24QcNUMo1+gkAAAAAAAAAc2VjcDI1Nmsx"}',

            '{"ver": "1.0", "metadata": {"data": "MzI1OTAzMTA2NDg3MTA0MzkyMQ==", "fee": -6204361832096331726, "contract_name": "4674913937326737575", "resources": ["MTE2MTcxNjM0MzU2NDA3MTM5Njg=", "MTY3OTQxMjIyMzY2NzEyNTgxMTU=", "ODYxNjQyNTE3NjA5MzQ3ODY2OQ=="], "signatures": [{"QAAAAAAAAACRKGJGGRaIXz1lcwrvcPHaiqpdfqO0cp78FwP3SDF3PfrBAWkpsJ7fUkIGk3PtkWyj8aLGC56tBNTpInLaUhV/CQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAADRrvyZ6J1IfMED6kg5AQa/xQLDeF3oLtUs55aMXSTTlLOjx163gHg896y90FKfyZuAur2RUSK2Sw9Syc7VqJDkCQAAAAAAAABzZWNwMjU2azE="}, {"QAAAAAAAAABvFRpaUUuaa0sP7H/Hu1qakANTuBrAL7JSZVakOMLjb0B/X2v1K2lK1yk5zpNLpUW4XsqDg0bMuk+TE3wxeydECQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAACkCrH+eefF9CRJoeZGxxlw8HdC807anrdWEyHIucg8EtdaZCa24MA6lfP00e5lJutyrVrgcQHIFgDUAReX0lTLCQAAAAAAAABzZWNwMjU2azE="}, {"QAAAAAAAAADkNcPg9uq6juhYKBgYtpKe5l9RthRH/ZBSKSyDMgmnezpr0TOp+iV1g+/oP5Y/vQGF97R76JDpq/IAV0zT1edbCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAAAHo0YPrx+xtenEvPaZVCRzttt+DfxHMUFbduBcDXcCTTqitNrHma9QScTbajMqda+maNqB/iM9hcfbl9HoUSx/CQAAAAAAAABzZWNwMjU2azE="}]}, "data": "EwAAAAAAAAA0Njc0OTEzOTM3MzI2NzM3NTc1MgjoK8mt5akDAAAAAAAAABQAAAAAAAAAMTE2MTcxNjM0MzU2NDA3MTM5NjgUAAAAAAAAADE2Nzk0MTIyMjM2NjcxMjU4MTE1EwAAAAAAAAA4NjE2NDI1MTc2MDkzNDc4NjY5EwAAAAAAAAAzMjU5MDMxMDY0ODcxMDQzOTIxAwAAAAAAAABAAAAAAAAAAJEoYkYZFohfPWVzCu9w8dqKql1+o7RynvwXA/dIMXc9+sEBaSmwnt9SQgaTc+2RbKPxosYLnq0E1OkictpSFX8JAAAAAAAAAHNlY3AyNTZrMUAAAAAAAAAA0a78meidSHzBA+pIOQEGv8UCw3hd6C7VLOeWjF0k05Szo8det4B4PPesvdBSn8mbgLq9kVEitksPUsnO1aiQ5AkAAAAAAAAAc2VjcDI1NmsxQAAAAAAAAABvFRpaUUuaa0sP7H/Hu1qakANTuBrAL7JSZVakOMLjb0B/X2v1K2lK1yk5zpNLpUW4XsqDg0bMuk+TE3wxeydECQAAAAAAAABzZWNwMjU2azFAAAAAAAAAAKQKsf5558X0JEmh5kbHGXDwd0LzTtqet1YTIci5yDwS11pkJrbgwDqV8/TR7mUm63KtWuBxAcgWANQBF5fSVMsJAAAAAAAAAHNlY3AyNTZrMUAAAAAAAAAA5DXD4Pbquo7oWCgYGLaSnuZfUbYUR/2QUiksgzIJp3s6a9EzqfoldYPv6D+WP70Bhfe0e+iQ6avyAFdM09XnWwkAAAAAAAAAc2VjcDI1NmsxQAAAAAAAAAAHo0YPrx+xtenEvPaZVCRzttt+DfxHMUFbduBcDXcCTTqitNrHma9QScTbajMqda+maNqB/iM9hcfbl9HoUSx/CQAAAAAAAABzZWNwMjU2azE="}',

            '{"ver": "1.0", "metadata": {"data": "Mzc5NzYwNTM1Mjg2NjQxODYzNQ==", "fee": 5634587528413326057, "contract_name": "16569740041036351731", "resources": ["NTczODk1MDg4NzgwNDgyOTg4NQ==", "OTI2OTEyNDgwNjU3NzAzNTc4NQ==", "OTg0ODk1MjYzNDMxMDYxMzAzMQ=="], "signatures": [{"QAAAAAAAAACcedF96SlD01v/57JdEX1L9kVLcOU0Pnm3BXhbu7imtz6A2dso9Rp/dEXDKapIR1ExHhTQnzk9foznwW1fZDrkCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAADFEY3inTGYqdZMMUOH+4pDytZDJpAeBLvApw+Ce8NIh1BnYQYZITRGt0pKGvRSo07jfmsbMK20pcVZh80XmULKCQAAAAAAAABzZWNwMjU2azE="}, {"QAAAAAAAAABov7xkwMP/75/2EOHBfPq2YhtkOY892daI1kBpSTeAAo1BR6xsf48rebvm0J5wUtYGwBIo2mwIw92V/Jr8blC8CQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAADLnAnBk2Do19ywG2GkZOaYyy3NIpXrue30xlCbEKrgJdblxR9lDeai73n+KyCHBuXxttMwqhlbCQGQFx+SYtviCQAAAAAAAABzZWNwMjU2azE="}, {"QAAAAAAAAACQ06SeiIkYCvtPuUnESE3vax1BSYSgJvgmPXKK94Um6ZUZEmILdA6FniocCEC6RMCbZROLS8g9FiVhoMVb/bCoCQAAAAAAAABzZWNwMjU2azE=": "QAAAAAAAAADBEFa/uRquBO2AH6VyKlawkr/RYRhcS4fowPM9jPvBkxAZbc9087adOIMNs2njfBzjhtcYWaJ1ke+HapSZBvcOCQAAAAAAAABzZWNwMjU2azE="}]}, "data": "FAAAAAAAAAAxNjU2OTc0MDA0MTAzNjM1MTczMekq7PaAEzJOAwAAAAAAAAATAAAAAAAAADU3Mzg5NTA4ODc4MDQ4Mjk4ODUTAAAAAAAAADkyNjkxMjQ4MDY1NzcwMzU3ODUTAAAAAAAAADk4NDg5NTI2MzQzMTA2MTMwMzETAAAAAAAAADM3OTc2MDUzNTI4NjY0MTg2MzUDAAAAAAAAAEAAAAAAAAAAnHnRfekpQ9Nb/+eyXRF9S/ZFS3DlND55twV4W7u4prc+gNnbKPUaf3RFwymqSEdRMR4U0J85PX6M58FtX2Q65AkAAAAAAAAAc2VjcDI1NmsxQAAAAAAAAADFEY3inTGYqdZMMUOH+4pDytZDJpAeBLvApw+Ce8NIh1BnYQYZITRGt0pKGvRSo07jfmsbMK20pcVZh80XmULKCQAAAAAAAABzZWNwMjU2azFAAAAAAAAAAGi/vGTAw//vn/YQ4cF8+rZiG2Q5jz3Z1ojWQGlJN4ACjUFHrGx/jyt5u+bQnnBS1gbAEijabAjD3ZX8mvxuULwJAAAAAAAAAHNlY3AyNTZrMUAAAAAAAAAAy5wJwZNg6NfcsBthpGTmmMstzSKV67nt9MZQmxCq4CXW5cUfZQ3mou95/isghwbl8bbTMKoZWwkBkBcfkmLb4gkAAAAAAAAAc2VjcDI1NmsxQAAAAAAAAACQ06SeiIkYCvtPuUnESE3vax1BSYSgJvgmPXKK94Um6ZUZEmILdA6FniocCEC6RMCbZROLS8g9FiVhoMVb/bCoCQAAAAAAAABzZWNwMjU2azFAAAAAAAAAAMEQVr+5Gq4E7YAfpXIqVrCSv9FhGFxLh+jA8z2M+8GTEBltz3Tztp04gw2zaeN8HOOG1xhZonWR74dqlJkG9w4JAAAAAAAAAHNlY3AyNTZrMQ=="}'
        ]

        for wire_tx in transactions_generated_by_cpp_ecosystem:
            assert self.verify_wire_tx(wire_tx), "Tx wire: {}".format(wire_tx)

