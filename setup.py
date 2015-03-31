#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# setup.py
#
"""Setup file for zatodeploy package."""

from os.path import dirname, join, realpath

from setuptools import setup, find_packages


def parse_requirements(requirements):
    """Read dependencies from file and strip off version numbers."""
    ignored = ('#', 'setuptools', '-r', '--')

    with open(requirements) as f:
        packages = []
        for line in f:
            line = line.strip()
            if any(line.startswith(prefix) for prefix in ignored):
                continue
            if '#egg=' in line:
                packages.append(line.split('#egg=')[1])
            else:
                packages.append(line.split('==')[0])
        return packages

setup(
    name='zato-deploy-cli',
    version='0.1b',
    description='Zato service deployment scripts',
    license='GPL2',
    author='pi-lar GmbH',
    author_email='info@pi-lar.net',
    url='https://github.com/pi-lar/zato-deploy-cli',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    entry_points={
        'console_scripts': [
            'zato-deploy = zatodeploy.main:main',
            'zato-deleteservices = zatodeploy.deleteservices:main',
            'zato-createchannels = zatodeploy.createchannels:main',
            'zato-createoutgoings = zatodeploy.createoutgoings:main',
            'zato-createsecdefs = zatodeploy.createsecdefs:main',
            'zato-setpassword = zatodeploy.setpassword:main',
            'zato-storesettings = zatodeploy.storesettings:main',
            'zato-uploadmodules = zatodeploy.uploadmodules:main'
        ]
    },
    install_requires=parse_requirements(join(dirname(realpath(__file__)),
                                             'requirements.txt')),
    setup_requires=parse_requirements(join(dirname(realpath(__file__)),
                                             'requirements-dev.txt')),
    tests_require=['nose'],
    test_suite='nose.collector',
    classifiers=[
        # complete classifier list:
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: '
        'GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        #'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration',
    ],
    keywords=['zato', 'deployment', 'enterprise service bus'],
    zip_safe=True
)
