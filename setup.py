import os
from setuptools import setup, find_packages

setup(
    name='smfhcp',
    version='1.0.0',
    description='social media for healthcare professionals',
    packages=find_packages(),
    install_requires=['elasticsearch', 'django', 'social-auth-app-django', 'python-social-auth', 'textile']
)