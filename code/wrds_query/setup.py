from setuptools import setup, find_packages

setup(
    name="wrds_query",  # Replace with your module name
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "wrds",
        "pandas"
    ],
    description="A Python module for querying financial data using wrds",
    author="Mats Walker",
    author_email="matswalker2@gmail.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)