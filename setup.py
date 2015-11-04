from setuptools import setup


setup(
    name='ebi',
    version='0.1',
    install_requires=[
        'awsebcli==3.5.5',
    ],
    packages=['ebi'],
    entry_points={
        'console_scripts': [
            'ebi = ebi.core:main',
        ]
    }
)
