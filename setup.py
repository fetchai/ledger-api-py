from setuptools import setup, find_packages

setup(
    name='fetchai-ledger-api',
    version='0.1.3',
    description='Tools and utilities for interacting with the ledger on the fetch network',
    url='https://github.com/fetchai/ledger-api-py',
    author='Edward FitzGerald',
    author_email='edward.fitzgerald@fetch.ai',
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'scripts']),
    install_requires=['requests', 'ecdsa'],
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage', 'pytest'],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
