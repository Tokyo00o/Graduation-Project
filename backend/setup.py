from setuptools import setup, find_packages

setup(
    name="fuzzguard-cli",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "fuzzguard=cli.main:cli",
        ],
    },
    install_requires=[
        "click>=8.0",
        "httpx>=0.27",
    ],
)
