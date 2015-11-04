from setuptools import setup

long_description = open('./README.rst').read()

setup(
    name='ebi',
    version='0.1.1',
    install_requires=[
        'awsebcli==3.5.5',
        'boto3==1.2.1',
    ],
    description='Simple CLI tool for ElasticBeanstalk',
    long_description=long_description,
    url='https://github.com/hirokiky/ebi',
    author='Hiroki KIYOHARA',
    author_email='hirokiky@gmail.com',
    license='MIT',
    packages=['ebi'],
    entry_points={
        'console_scripts': [
            'ebi = ebi.core:main',
        ]
    }
)
