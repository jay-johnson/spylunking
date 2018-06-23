import os
import sys
import warnings
import unittest

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', 'Arguments to pass to pytest')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def run_tests(self):
        import shlex
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


cur_path, cur_script = os.path.split(sys.argv[0])
os.chdir(os.path.abspath(cur_path))

install_requires = [
    'colorlog',
    'coverage',
    'flake8<=3.4.1',
    'pep8>=1.7.1',
    'pipenv',
    'pycodestyle<=2.3.1',
    'pylint',
    'python-json-logger',
    'pytest',
    'recommonmark',
    'requests',
    'sphinx',
    'sphinx-autobuild',
    'sphinx_rtd_theme',
    'splunk_handler',
    'tox',
    'unittest2',
    'mock'
]


if sys.version_info < (3, 5):
    warnings.warn(
        'Less than Python 3.5 is not supported.',
        DeprecationWarning)


# Do not import spylunking module here, since deps may not be installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'spylunking'))

setup(
    name='spylunking',
    cmdclass={'test': PyTest},
    version='1.0.12',
    description=(
        'Splunk-ready python logging integration, Docker demos and tools'),
    long_description=(
        'Splunk-ready python logging integration, docker demos and tools'),
    author='Jay Johnson',
    author_email='jay.p.h.johnson@gmail.com',
    url='https://github.com/jay-johnson/spylunking',
    packages=[
        'spylunking',
        'spylunking.scripts',
        'spylunking.log'
    ],
    package_data={},
    install_requires=install_requires,
    test_suite='setup.spylunking_test_suite',
    tests_require=[
        'pytest'
    ],
    scripts=[
        './spylunking/scripts/logs.sh',
        './spylunking/scripts/get_splunk_token.py',
        './spylunking/scripts/show_service_token.py',
        './spylunking/scripts/search_splunk.py',
        './spylunking/scripts/test_logging.py',
        './spylunking/scripts/sp'
    ],
    use_2to3=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ])
