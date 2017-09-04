#!/usr/bin/env python

from setuptools import setup, find_packages

install_requires = [
    'bintrees==2.0.7',
    'requests==2.13.0',
    'six==1.10.0',
    'websocket-client==0.40.0',
    'gdax==1.0.6'
]

tests_require = [
    'pytest',
    ]

setup(
    name='schaefcoin',
    version='0.0.1',
    author='Martin Schaef',
    author_email='fakeaddress@gmail.com',
    license='MIT',
    url='https://github.com/martinschaef/coinstuff',
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=tests_require,
    description='My trading stuff',
    download_url='https://github.com/martinschaef/coinstuff',
    keywords=['mystuff'],
    classifiers=[
        'Programming Language :: Python :: 2.7',
    ],
)