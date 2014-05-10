#!/usr/bin/env python
from setuptools import setup


requires = [
    'flask',
    'click',
    'trytond',
    'simplejson',
]

setup(
    name="tryton-restful",
    version=0.1,
    description="REST API to access Tryton modules",
    long_description=open('README.rst').read(),
    author="Openlabs Technologies and Consulting (P) Ltd.",
    author_email="info@openlabs.co.in",
    url="http://www.openlabs.co.in/",
    package_dir={'tryton_restful': 'tryton_restful'},
    packages=['tryton_restful'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Tryton',
        'Topic :: Office/Business',
    ],
    license='GPL-3',
    install_requires=requires,
    zip_safe=False,
    entry_points="""
    [console_scripts]
    tryton_restful = tryton_restful.cli:main
    """,
    test_suite='tests',
)
