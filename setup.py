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
    install_requires=[
        'base58==2.0.0',
        'ecdsa==0.15',
        'lark-parser==0.8.1',
        'msgpack==0.6.2',
        'pyaes==1.6.1',
        'requests==2.22.0',
        'semver==2.9.0',
    ],
    extras_require={
        'dev': ['check-manifest', 'pydot'],
        'test': ['coverage', 'pytest'],
    },
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.5'
)
