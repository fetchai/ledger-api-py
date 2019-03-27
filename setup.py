from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='fetchai-ledger-api',
    version='0.1.4',
    description='Tools and utilities for interacting with the ledger on the fetch network',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/fetchai/ledger-api-py',
    author='Edward FitzGerald',
    author_email='edward.fitzgerald@fetch.ai',
    classifiers=[  # Optional
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',

        'License :: OSI Approved :: Apache Software License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
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
