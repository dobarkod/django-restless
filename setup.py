#!/usr/bin/env python

from setuptools import setup, find_packages, Command
import os
import sys


class BaseCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class TestCommand(BaseCommand):

    description = "run self-tests"

    def run(self):
        os.chdir('testproject')
        ret = os.system('python manage.py test testapp')
        if ret != 0:
            sys.exit(-1)


class CoverageCommand(BaseCommand):
    description = "run self-tests and report coverage (requires coverage.py)"

    def run(self):
        os.chdir('testproject')
        r = os.system('coverage run --source=restless manage.py test testapp')
        if r != 0:
            sys.exit(-1)
        os.system('coverage html')


setup(
    name='DjangoRestless',
    version='0.0.8',
    author='Senko Rasic',
    author_email='senko.rasic@goodcode.io',
    description='A RESTful framework for Django',
    license='MIT',
    url='github.com/dobarkod/django-restless',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(),
    install_requires=['Django>=1.5', 'six>=1.3.0'],
    cmdclass={
        'test': TestCommand,
        'coverage': CoverageCommand
    }
)
