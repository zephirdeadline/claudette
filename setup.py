#!/usr/bin/env python3
"""
Setup script for Claudette

This is a compatibility shim for older build tools.
Modern Python packaging should use pyproject.toml instead.

For development:
    pip install -e .
    pip install -e ".[dev]"

For building:
    python -m build
    python setup.py sdist bdist_wheel (legacy)
"""

from setuptools import setup

# Configuration is now in pyproject.toml
# This setup.py exists for backward compatibility only
setup()
