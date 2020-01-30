from setuptools import setup, find_packages

from fetchai.ledger import __version__ as version_string

setup(
    name='fetchai-ledger-api',
    version=version_string,
    description='Tools and utilities for interacting with the Fetch.AI Smart Ledger',
    url='https://github.com/fetchai/ledger-api-py',
    author='Edward FitzGerald',
    author_email='edward.fitzgerald@fetch.ai',
    packages=[
        'fetchai',
        'fetchai.ledger',
        'fetchai.ledger.api',
        'fetchai.ledger.crypto',
        'fetchai.ledger.genesis',
        'fetchai.ledger.parser',
        'fetchai.ledger.serialisation'
    ],
    package_data={'fetchai.ledger.parser': ['etch.grammar']},
    include_package_data=True,
    install_requires=[
        'base58==2.0.0',
        'ecdsa==0.15',
        'lark-parser==0.7.8',
        'msgpack==0.6.2',
        'pyaes==1.6.1',
        'requests==2.22.0',
        'semver==2.9.0'
    ],
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    python_requires='>=3.6'
)
