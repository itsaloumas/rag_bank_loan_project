"""Pytest configuration for the test suite.

rules_engine.py and related modules are in src/bankingragdemo/ and are
imported, mirroring how api.py adds that directory to sys.path at runtime. We replicate that here so the tests can `import rules_engine`
without installing the package.
"""
import os
import sys

SRC_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "src", "bankingragdemo")
)
sys.path.insert(0, SRC_DIR)
