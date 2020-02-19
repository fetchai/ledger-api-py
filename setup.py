from os import path

from setuptools import setup, find_packages

from fetchai.ledger import __version__ as version_string

project_root = path.dirname(__file__)

with open(path.join(project_root, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='fetchai-ledger-api',
    version=version_string,
    description='Tools and utilities for interacting with the ledger on the fetch network',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/fetchai/ledger-api-py',
    author='Edward FitzGerald',
    author_email='edward.fitzgerald@fetch.ai',
    packages=find_packages(exclude=['contrib', 'docs', 'examples', 'tests', 'scripts']),
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
    python_requires='>=3.5',
    project_urls={
        'Bug Reports': 'https://github.com/fetchai/ledger-api-py/issues',
        'Developer Site': 'https://developer.fetch.ai/',
        'Documentation': 'https://docs.fetch.ai/',
        'Source': 'https://github.com/fetchai/ledger-api-py',
    },
)
