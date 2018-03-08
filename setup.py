from unittest import TestLoader

import setuptools
from setuptools import setup


def snake_test_suite():
    test_loader = TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite


setup(
    name="snake",
    version="1.0",
    packages=setuptools.find_packages(exclude=["tests"]),
    install_requires=[
        'celery',
        'celery[redis]',
        'marshmallow',
        'motor',
        'python-magic',
        'pyyaml',
        'requests',
        'tornado',
        'webargs'
    ],
    extras_require={
        'ssdeep': ['pydeep']
    },
    dependency_links=[
        "git+https://github.com/kbandla/pydeep#egg=pydeep"
    ],

    entry_points={
        'console_scripts': [
            'snaked = snake.snaked:__main__',
            'snake = snake.snake:main'
        ]
    },

    include_package_data=True,
    zip_safe=False,

    setup_requires=[
        'flake8',
        'pylint',
        'pytest-runner',
        'setuptools-lint'
    ],
    tests_require=[
        'pytest',
        'pytest-asyncio',
        'pytest-cov',
        'pytest-mock'
    ],
    test_suite="setup.snake_test_suite",

    author="Alex Kornitzer",
    author_email="alex.kornitzer@countercept.com",
    description="The binary store!",
    license="",
    keywords="snake binary malware",
    url="",
)
