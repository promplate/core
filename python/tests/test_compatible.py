"""Tests for the compatibility of promplate."""

from promplate.compatible.chain.node import Template
from promplate.compatible import file_list, file_list_convert
import os
from subprocess import run


def test_compatible():
    """Test the existence of the `promplate.compatible` module."""
    template = Template("Hello, {{ name }}!")
    assert template.render({"name": "World"}) == "Hello, World!"


def test_others():
    """Run all other tests in `tests/`."""
    test_dir = os.path.dirname(__file__)
    test_files = file_list(test_dir)
    test_files.pop(os.path.join(test_dir, "test_compatible.py")) # remove this file

    # convert all files in `tests/` to `tests/compatible/`
    file_list_convert(test_files)

    # use poetry to run all other tests, and raise error if any test fails
    for _, test_file in test_files.items():
        output = run(f"poetry run pytest {test_file}", capture_output=True, shell=True)
        print(output.stdout.decode())
        print(output.stderr.decode())
        assert output.returncode == 0
