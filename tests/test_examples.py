"""Every example must parse, pass the static checker, and (when offline) run."""

import os

import pytest

from rex.analyzer import analyze
from rex.interpreter import RexInterpreter

EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")

NETWORK_EXAMPLES = {"api_fetch.rex", "api_crud.rex", "errors.rex"}

EXPECTED_FIRST_LINE = {
    "hello.rex": "Sawubona Mhlaba",
    "fizzbuzz.rex": "1",
    "variables.rex": "Andile",
    "control_flow.rex": "grade B",
    "functions.rex": "Sawubona, Mhlaba!",
    "collections.rex": "count: 4",
    "strings.rex": "cleaned: [Rex,Python,JavaScript]",
    "json_tools.rex": "team: Alysium",
    "env_args.rex": "script arguments: []",
    "word_count.rex": "word counts:",
}


def example_files():
    if not os.path.isdir(EXAMPLES_DIR):
        return []
    return sorted(f for f in os.listdir(EXAMPLES_DIR) if f.endswith(".rex"))


def test_examples_exist():
    assert len(example_files()) >= 10


@pytest.mark.parametrize("name", example_files())
def test_example_passes_static_checks(name):
    with open(os.path.join(EXAMPLES_DIR, name), encoding="utf-8") as handle:
        source = handle.read()
    findings = analyze(source, name)
    errors = [f for f in findings if f.level == "error"]
    assert errors == [], [f.render(name) for f in errors]


@pytest.mark.parametrize("name", [n for n in example_files() if n not in NETWORK_EXAMPLES])
def test_example_runs(name, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    interp = RexInterpreter()
    output = interp.run_file(os.path.join(EXAMPLES_DIR, name))
    assert output, "example printed nothing"
    expected = EXPECTED_FIRST_LINE.get(name)
    if expected is not None:
        assert output[0] == expected
    assert interp.exit_code == 0
