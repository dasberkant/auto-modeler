#!/usr/bin/env python
"""Setup script for Auto-Modeler."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="auto-modeler",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An AI-driven Operations Research assistant for solving deterministic OR problems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/auto-modeler",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "auto-modeler=app.main:main",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "isort>=5.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 