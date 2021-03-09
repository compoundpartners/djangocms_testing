#!/usr/bin/env python
from setuptools import find_packages, setup
from djangocms_testing import __version__

long_description = open('README.md').read()

setup(
    name='js-testing',
    version=__version__,
    description='Testing utilities for Django CMS',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='BSD',
    author='Nicolas Lara',
    author_email='nicolas@lincolnloop.com',
    url='https://github.com/nicolaslara/djangocms_testing/',
    packages=find_packages(),
    scripts=[
    ],
    package_data={
        'djangocms_testing': ['djangocms_testing/templates/*.*'],
    },
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        'django-cms>=3.4.5',
        'PyYAML>=3.12',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Testing',
        'Framework :: Django',
    ]
)
