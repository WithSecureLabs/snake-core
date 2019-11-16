from unittest import TestLoader

import setuptools
from setuptools import setup


def snake_test_suite():
    test_loader = TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite


setup(
    name="snake",
    version="1.0.1",
    packages=setuptools.find_packages(exclude=["tests"]),
    install_requires=[
        'celery==4.3.0',
        'celery[redis]==4.3.0',
        'marshmallow==3.0.0b7',
        'motor==2.0.0',
        'redis==3.2.1',
        'python-magic==0.4.15',
        'pyyaml==5.1',
        'requests==2.18.4',
        'tornado==5.0.1',
        'webargs==5.1.3'
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
            'snake = snake.snake_utility:main'
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
    license="https://github.com/countercept/snake-core/blob/master/LICENSE",
    keywords="snake binary malware",
    url="https://github.com/countercept/snake-core",
)
