"""Secure counterpart sample for false-positive validation.

Uses parameterized queries, environment variables, safe subprocess argument
lists, safe YAML loading, and secure temporary files.
"""
import os
import sqlite3
import subprocess
import tempfile

import yaml

# Secure: loaded from the environment; no credential is committed.
SECRET_API_KEY = os.environ.get("API_KEY")


def safe_query(username: str):
    conn = sqlite3.connect("app.db")
    # Secure: parameterized SQL query
    conn.execute("SELECT * FROM users WHERE name = ?", (username,))


def safe_operation(value: int):
    # Secure: simple arithmetic, no eval
    return value * 2


def safe_process(value: str):
    # Secure: argument list, shell disabled
    return subprocess.run(
        ["echo", value], shell=False, capture_output=True, text=True, timeout=2
    )


def safe_yaml_load(data: bytes):
    # Secure: yaml.safe_load rejects arbitrary object construction
    return yaml.safe_load(data)


def safe_tempfile():
    # Secure: file is created atomically by the standard library
    with tempfile.NamedTemporaryFile(delete=False) as handle:
        return handle.name
