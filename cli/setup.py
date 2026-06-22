from setuptools import find_packages, setup

setup(
    name="fuzzguard-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0",
        "httpx>=0.27",
        "rich>=13.0",
    ],
    entry_points={
        "console_scripts": [
            "fuzzguard=fuzzguard.cli:cli",
        ],
    },
)
