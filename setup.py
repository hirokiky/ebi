from setuptools import setup, find_packages

long_description = open('./README.rst').read()

setup(
    name='ebi',
    version='0.6.3',
    install_requires=[
        'awsebcli>=3.7.3,<4',
        'boto3>=1.2.6,<2',
    ],
    description='Simple CLI tool for ElasticBeanstalk with Docker',
    long_description=long_description,
    url='https://github.com/hirokiky/ebi',
    author='Hiroki KIYOHARA',
    author_email='hirokiky@gmail.com',
    license='MIT',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ebi = ebi.core:main',
        ]
    }
)
