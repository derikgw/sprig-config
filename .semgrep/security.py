"""Synthetic rule fixtures; these functions are never executed."""
import os
import subprocess
import yaml


def examples(text, value):
    # ruleid: unsafe-yaml-loader
    yaml.load(text, Loader=yaml.Loader)
    # ruleid: unsafe-yaml-loader
    yaml.unsafe_load(text)
    # ruleid: unsafe-yaml-loader
    yaml.full_load(text)
    # ok: unsafe-yaml-loader
    yaml.safe_load(text)
    # ruleid: dynamic-evaluation
    eval(text)
    # ruleid: dynamic-evaluation
    exec(text)
    # ruleid: shell-command-execution
    subprocess.run(text, shell=True)
    # ruleid: shell-command-execution
    os.system(text)
    # ruleid: shell-command-execution
    os.popen(text)
    # ok: shell-command-execution
    subprocess.run(["echo", "synthetic"], check=True)
    # ruleid: sensitive-value-in-diagnostic
    raise ValueError(f"Value: {value!r}")
