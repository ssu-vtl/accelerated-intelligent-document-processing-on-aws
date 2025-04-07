#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="idp_common",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "boto3>=1.28.0",
        "Pillow>=9.5.0",
    ],
)