from setuptools import setup, find_packages

setup(
    name='fetchai-ledger-api',
    version='0.9.0a1',
    description='Tools and utilities for interacting with the ledger on the fetch network',
    url='https://github.com/fetchai/ledger-api-py',
    author='Edward FitzGerald',
    author_email='edward.fitzgerald@fetch.ai',
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'scripts']),
    package_data={'fetchai': ['ledger/parser/etch.grammar']},
    install_requires=['requests', 'ecdsa', 'msgpack', 'base58', 'lark-parser'],
    extras_require={
        'dev': ['check-manifest', 'pydot'],
        'test': ['coverage', 'pytest'],
    }
)
