import json
import os
import subprocess
import sys

from rex import __version__
from rex.cli import (
    EXIT_IMPORT,
    EXIT_OK,
    EXIT_RUNTIME,
    EXIT_SYNTAX,
    EXIT_USAGE,
    main,
)


def write(tmp_path, name, source):
    path = tmp_path / name
    path.write_text(source, encoding="utf-8")
    return str(path)


def test_version(capsys):
    assert main(["version"]) == EXIT_OK
    assert capsys.readouterr().out.strip() == "Rex %s" % __version__


def test_help_lists_commands(capsys):
    assert main(["help"]) == EXIT_OK
    out = capsys.readouterr().out
    for command in ("run", "repl", "check", "ast", "init"):
        assert command in out


def test_no_arguments_prints_usage(capsys):
    assert main([]) == EXIT_OK
    assert "usage:" in capsys.readouterr().out


def test_run_file(tmp_path, capsys):
    path = write(tmp_path, "hello.rex", 'rex.show("yebo")')
    assert main(["run", path]) == EXIT_OK
    assert capsys.readouterr().out.strip() == "yebo"


def test_bare_file_shorthand(tmp_path, capsys):
    path = write(tmp_path, "hello.rex", 'rex.show("yebo")')
    assert main([path]) == EXIT_OK
    assert capsys.readouterr().out.strip() == "yebo"


def test_script_arguments_are_passed(tmp_path, capsys):
    path = write(tmp_path, "args.rex", "rex.show(rex.args)")
    assert main(["run", path, "a", "b"]) == EXIT_OK
    assert '"a"' in capsys.readouterr().out


def test_missing_file():
    assert main(["run", "definitely_missing.rex"]) == EXIT_IMPORT


def test_runtime_error_exit_code(tmp_path, capsys):
    path = write(tmp_path, "boom.rex", 'rex.throw "nope"')
    assert main(["run", path]) == EXIT_RUNTIME
    assert "Rex Error: nope" in capsys.readouterr().err


def test_syntax_error_exit_code(tmp_path, capsys):
    path = write(tmp_path, "bad.rex", "rex.let = 1")
    assert main(["run", path]) == EXIT_SYNTAX
    assert "Rex Error" in capsys.readouterr().err


def test_exit_code_propagates(tmp_path):
    path = write(tmp_path, "code.rex", "rex.exit(4)")
    assert main(["run", path]) == 4


def test_check_reports_ok(tmp_path, capsys):
    path = write(tmp_path, "good.rex", 'rex.show("hi")')
    assert main(["check", path]) == EXIT_OK
    assert "ok" in capsys.readouterr().out


def test_check_reports_unknown_builtin(tmp_path, capsys):
    path = write(tmp_path, "bad.rex", 'rex.sho("hi")')
    assert main(["check", path]) == EXIT_SYNTAX
    assert "unknown builtin" in capsys.readouterr().out


def test_check_reports_warning_but_passes(tmp_path, capsys):
    path = write(tmp_path, "warn.rex", "rex.show(nope)")
    assert main(["check", path]) == EXIT_OK
    assert "warning" in capsys.readouterr().out


def test_ast_dumps_json(tmp_path, capsys):
    path = write(tmp_path, "hello.rex", 'rex.show("hi")')
    assert main(["ast", path]) == EXIT_OK
    data = json.loads(capsys.readouterr().out)
    assert data["type"] == "Program"


def test_init_creates_project(tmp_path, capsys):
    target = tmp_path / "project"
    assert main(["init", str(target)]) == EXIT_OK
    assert (target / "main.rex").is_file()
    assert (target / "README.md").is_file()


def test_init_refuses_to_overwrite(tmp_path, capsys):
    target = tmp_path / "project"
    target.mkdir()
    (target / "main.rex").write_text("rex.show(1)")
    assert main(["init", str(target)]) == EXIT_USAGE


def test_unknown_command(capsys):
    assert main(["frobnicate"]) == EXIT_USAGE


def test_unknown_option(capsys):
    assert main(["--nope"]) == EXIT_USAGE


def test_max_steps_flag(tmp_path, capsys):
    path = write(tmp_path, "loop.rex", "rex.while true\nrex.end")
    assert main(["run", "--max-steps", "500", path]) == EXIT_RUNTIME
    assert "execution limit" in capsys.readouterr().err


def test_bad_flag_value(tmp_path):
    path = write(tmp_path, "hello.rex", 'rex.show("hi")')
    assert main(["run", "--max-steps", "abc", path]) == EXIT_USAGE


def test_module_entry_point(tmp_path):
    path = write(tmp_path, "hello.rex", 'rex.show("module")')
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run(
        [sys.executable, "-m", "rex", "run", path],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "module"


def test_console_script_is_declared():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "pyproject.toml"), encoding="utf-8") as handle:
        assert 'rex = "rex.cli:main"' in handle.read()
