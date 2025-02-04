from setuptools import setup, find_packages

setup(
    name="yfinance_query",  # Replace with your module name
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "yfinance",
        "pandas", 
        "numpy"
    ],
    description="A Python module for querying financial data using yfinance",
    author="Mats Walker",
    author_email="matswalker2@gmail.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)