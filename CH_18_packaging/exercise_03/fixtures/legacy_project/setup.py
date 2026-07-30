"""Intentionally legacy packaging fixture for the migration exercise."""

from setuptools import find_packages, setup

setup(
    name="greeting-demo",
    version="1.2.3",
    description="A tiny migration fixture",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={"console_scripts": ["greet=greeting_demo:main"]},
)
