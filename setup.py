from setuptools import setup, find_packages
from fetchai.ledger import __version__ as version_string

setup(
    name='fetchai-ledger-api',
    version=version_string,
    description='Tools and utilities for interacting with the ledger on the fetch network',
    url='https://github.com/fetchai/ledger-api-py',
    author='Edward FitzGerald',
    author_email='edward.fitzgerald@fetch.ai',
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'scripts']),
    package_data={'fetchai': ['ledger/parser/etch.grammar']},
    install_requires=['requests', 'ecdsa', 'msgpack', 'base58', 'lark-parser', 'semver', 'pyaes'],
    extras_require={
        'dev': ['check-manifest', 'pydot'],
        'test': ['coverage', 'pytest'],
    },
    classifiers=[
        'Programming Language :: Python :: 3'
    ],
    python_requires='>=3.5'
)
