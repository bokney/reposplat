
from typer.testing import CliRunner

from reposplat.core import (
    build_pathspec,
    should_include_file,
    combine_files,
    get_files,
)
from reposplat.models import File
from reposplat.main import app

runner = CliRunner()


def test_build_and_should_include(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    file_a = repo / "a.py"
    file_a.write_text("print('hello')")
    file_ignore = repo / "ignore.me"
    file_ignore.write_text("x")

    include_spec = build_pathspec(["**/*.py"])
    exclude_spec = build_pathspec(["ignore.me"])

    assert should_include_file(file_a, repo, include_spec, exclude_spec)
    assert not should_include_file(
        file_ignore, repo, include_spec, exclude_spec
    )


def test_get_files_and_combine_files(tmp_path):
    repo = tmp_path / "repo2"
    repo.mkdir()
    file1 = repo / "one.py"
    file2 = repo / "sub" / "two.py"
    file2.parent.mkdir()
    file1.write_text("a=1")
    file2.write_text("b=2")

    files = get_files(repo, ["**/*.py"], [])
    assert len(files) == 2

    combined = combine_files(files, repo_path=repo)
    for f in ["one.py", "sub/two.py"]:
        assert f"=== FILE START: {f} ===" in combined.text
        assert f"=== FILE END: {f} ===" in combined.text
    assert "a=1" in combined.text
    assert "b=2" in combined.text


def test_combine_file_outside_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside_file = tmp_path / "outside.py"
    outside_file.write_text("print('x')")
    file_obj = File(path=outside_file, contents=outside_file.read_text())
    combined = combine_files([file_obj], repo_path=repo)
    # fallback uses file name
    assert "=== FILE START: outside.py ===" in combined.text
    assert "print('x')" in combined.text


def test_cli_creates_combined_file(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("print('hello')")
    output_file = tmp_path / "combined.txt"

    result = runner.invoke(app, [str(repo), "--output", str(output_file)])
    assert result.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "=== FILE START: a.py ===" in content
    assert "print('hello')" in content


def test_cli_empty_repo(tmp_path):
    repo = tmp_path / "empty_repo"
    repo.mkdir()
    output_file = tmp_path / "combined.txt"

    result = runner.invoke(app, [str(repo), "--output", str(output_file)])
    assert result.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert content.strip() == ""


def test_should_include_hidden_and_subfolders(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    hidden_file = repo / ".hidden.py"
    sub_folder = repo / "sub"
    sub_folder.mkdir()
    sub_file = sub_folder / "file.py"

    hidden_file.write_text("hidden")
    sub_file.write_text("subfile")

    include_spec = build_pathspec(["**/*.py"])
    exclude_spec = build_pathspec([])

    assert should_include_file(hidden_file, repo, include_spec, exclude_spec)
    assert should_include_file(sub_file, repo, include_spec, exclude_spec)
