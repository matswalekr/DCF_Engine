from setuptools import setup, find_packages

setup(
    name="database_query",  # Replace with your module name
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlite3",
        "pandas"
    ],
    description="A Python module for querying financial data from a database",
    author="Mats Walker",
    author_email="matswalker2@gmail.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)