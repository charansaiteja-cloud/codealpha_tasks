"""INTENTIONALLY INSECURE. Use only for static source review."""
import pickle
import sqlite3
import subprocess
import tempfile

import requests
import yaml


def unsafe_lookup(db: sqlite3.Connection, name: str):
    # SQL injection risk: untrusted input is concatenated into SQL.
    return db.execute(
        "SELECT id, name FROM users WHERE name = '" + name + "'"
    ).fetchall()


def unsafe_preview(filename: str):
    # Shell injection risk: never use this with untrusted input.
    return subprocess.run(
        "echo preview " + filename,
        shell=True, capture_output=True, text=True, timeout=2,
    )


def unsafe_load(data: bytes):
    # Unsafe if data is attacker-controlled.
    return pickle.loads(data)


def unsafe_eval(expression: str):
    # Dynamic code execution: the expression is treated as Python code.
    return eval(expression)


def unsafe_yaml(data: bytes):
    # yaml.Loader can construct arbitrary Python objects.
    return yaml.load(data, Loader=yaml.Loader)


def unsafe_request(url: str):
    # Certificate verification is disabled.
    return requests.get(url, verify=False, timeout=2)


def unsafe_tempfile():
    # Race condition between filename generation and file creation.
    return tempfile.mktemp()


# Fictional placeholder, not a real credential.
DEMO_PASSWORD = "lab-placeholder-only"


def unsafe_divide(value: int):
    try:
        return 100 // value
    except Exception as exc:
        return {"error": str(exc), "debug": repr(exc)}
