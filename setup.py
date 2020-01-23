""" package aries_protocol_test_suite """

from setuptools import setup, find_packages


def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


VERSION = '0.1.0'


if __name__ == '__main__':
    with open('README.md', 'r') as fh:
        LONG_DESCRIPTION = fh.read()

    setup(
        name='aries-protocol-test-suite',
        version=VERSION,
        author='Daniel Bluhm <daniel.bluhm@sovrin.org>',
        description='Suite for testing protocol compliance of Aries Agents',
        long_description=LONG_DESCRIPTION,
        long_description_content_type='text/markdown',
        url='https://github.com/dbluhm/aries-protocol-test-suite',
        license='Apache 2.0',
        packages=find_packages(),
        install_requires=parse_requirements('requirements.txt'),
        extras_require={
            'indy': parse_requirements('requirements.indy.txt'),
        },
        python_requires='>=3.6',
        classifiers=[
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent'
        ],
        scripts=[
            'scripts/protocoltest',
            'scripts/apts'
        ]
    )
