from setuptools import setup, find_packages

setup(
    name="DCF",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlite3",
        "pandas",
        "wrds",
        "openpyxl",
        "pycel",
        "fmpsdk",
        "openai", # Only necessary if API_KEY
        "numpy",
        "yfinance",
        "git+https://github.com/matswalekr/Excel_Engine" # Own github repository for working with Excel

    ],
    description="A Python module to write DCFs automatically into Excel files",
    author="Mats Walker",
    author_email="matswalker2@gmail.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)