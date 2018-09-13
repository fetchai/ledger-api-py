from setuptools import setup, find_packages

setup(
    name='fetch-ledger-api',
    version='0.0.1',
    description='Tools and utilities for interacting with the ledger on the fetch network',
    url='https://github.com/fetch/',
    author='Edward FitzGerald',
    author_email='edward.fitzgerald@fetch.ai',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),  # Required
    install_requires=['requests'],
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
