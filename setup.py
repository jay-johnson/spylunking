import os
import sys
import warnings

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    """PyTest"""

    user_options = [('pytest-args=', 'a', 'Arguments to pass to pytest')]

    def initialize_options(
            self):
        """initialize_options"""
        TestCommand.initialize_options(self)
        self.pytest_args = ''
    # end of initialize_options

    def finalize_options(
            self):
        """finalize_options"""
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    # end of finalize_options

    def run_tests(
            self):
        """run_tests"""
        import pytest
        import sys

        errno = pytest.main(self.test_args)
        self.handle_exit()
        sys.exit(errno)
    # end of run_tests

    @staticmethod
    def handle_exit():
        """handle_exit"""
        import atexit
        atexit._run_exitfuncs()
    # end of handle_exit

# end of PyTest


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
    'tox',
    'unittest2',
    'mock'
]

if sys.version_info < (2, 7):
    warnings.warn(
        'Python 2.6 is no longer officially supported by Fractal. '
        'If you have any questions, please file an issue on Github '
        'https://github.com/jay-johnson/spylunking',
        DeprecationWarning)


# Do not import spylunking module here, since deps may not be installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'spylunking'))

setup(
    name='spylunking',
    cmdclass={'test': PyTest},
    version='1.2.0',
    description=(
        'Spylunking - Drill down into your logs with an integrated, '
        'colorized logger with search tools. Includes a Splunk sandbox '
        'running in docker.'
        ''),
    long_description=(
        'Spylunking - Drill down into your logs with an integrated, '
        'colorized logger with search tools. Includes a Splunk sandbox '
        'running in docker and working Python handlers for sending logs '
        'over TCP or the Splunk HEC REST API. The HEC REST API handler '
        'can use either '
        'a non-blocking thread or a non-blocking multiprocessing process '
        'to send logs to Splunk.'
        '\n'
        ''),
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
        './spylunking/scripts/start_logging_loader.py',
        './spylunking/scripts/test_publish_to_splunk.py',
        './spylunking/scripts/sp'
    ],
    use_2to3=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ])
