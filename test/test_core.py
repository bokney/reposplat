
from pathlib import Path

from typer.testing import CliRunner

from reposplat.core import (
    build_pathspec,
    should_include_file,
    combine_files,
    get_files,
)
from reposplat.models import File
from reposplat.main import app


class TestBuildPathspec:
    def test_creates_valid_pathspec(self):
        spec = build_pathspec(["**/*.py", "*.txt"])
        assert spec is not None
        assert spec.match_file("test.py")
        assert spec.match_file("sub/test.py")
        assert spec.match_file("readme.txt")


class TestShouldIncludeFile:
    def test_includes_matching_file(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        file_a = repo / "a.py"
        file_a.write_text("print('hello')")

        include_spec = build_pathspec(["**/*.py"])
        exclude_spec = build_pathspec([])

        assert should_include_file(file_a, repo, include_spec, exclude_spec)

    def test_excludes_non_matching_file(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        file_ignore = repo / "ignore.me"
        file_ignore.write_text("x")

        include_spec = build_pathspec(["**/*.py"])
        exclude_spec = build_pathspec(["ignore.me"])

        assert not should_include_file(
            file_ignore, repo, include_spec, exclude_spec
        )

    def test_includes_hidden_files(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        hidden_file = repo / ".hidden.py"
        hidden_file.write_text("hidden")

        include_spec = build_pathspec(["**/*.py"])
        exclude_spec = build_pathspec([])

        assert should_include_file(
            hidden_file, repo, include_spec, exclude_spec
        )

    def test_includes_files_in_subfolders(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        sub_folder = repo / "sub"
        sub_folder.mkdir()
        sub_file = sub_folder / "file.py"
        sub_file.write_text("subfile")

        include_spec = build_pathspec(["**/*.py"])
        exclude_spec = build_pathspec([])

        assert should_include_file(sub_file, repo, include_spec, exclude_spec)

    def test_excludes_file_outside_repo(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        outside_file = tmp_path / "outside.py"
        outside_file.write_text("x")

        include_spec = build_pathspec(["**/*.py"])
        exclude_spec = build_pathspec([])

        assert not should_include_file(
            outside_file, repo, include_spec, exclude_spec
        )


class TestGetFiles:
    def test_finds_matching_files(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        file1 = repo / "one.py"
        file2 = repo / "sub" / "two.py"
        file2.parent.mkdir()
        file1.write_text("a=1")
        file2.write_text("b=2")

        files = get_files(repo, ["**/*.py"], [])

        assert len(files) == 2
        paths = [f.path.name for f in files]
        assert "one.py" in paths
        assert "two.py" in paths

    def test_respects_exclude_patterns(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        file1 = repo / "include.py"
        file2 = repo / "exclude.py"
        file1.write_text("a=1")
        file2.write_text("b=2")

        files = get_files(repo, ["**/*.py"], ["exclude.py"])

        assert len(files) == 1
        assert files[0].path.name == "include.py"

    def test_reads_file_contents(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        test_file = repo / "test.py"
        test_content = "print('hello world')"
        test_file.write_text(test_content)

        files = get_files(repo, ["**/*.py"], [])

        assert len(files) == 1
        assert files[0].contents == test_content


class TestCombineFiles:
    def test_combines_single_file(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        file1 = repo / "test.py"
        file1.write_text("content")

        files = [File(path=file1, contents="content")]
        combined = combine_files(files, repo_path=repo)

        assert "=== FILE START: test.py ===" in combined.text
        assert "=== FILE END: test.py ===" in combined.text
        assert "content" in combined.text

    def test_combines_multiple_files(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        file1 = repo / "one.py"
        file2 = repo / "sub" / "two.py"
        file2.parent.mkdir()

        files = [
            File(path=file1, contents="a=1"),
            File(path=file2, contents="b=2")
        ]
        combined = combine_files(files, repo_path=repo)

        for f in ["one.py", "sub/two.py"]:
            assert f"=== FILE START: {f} ===" in combined.text
            assert f"=== FILE END: {f} ===" in combined.text
        assert "a=1" in combined.text
        assert "b=2" in combined.text

    def test_handles_file_outside_repo(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        outside_file = tmp_path / "outside.py"
        outside_file.write_text("print('x')")

        file_obj = File(path=outside_file, contents=outside_file.read_text())
        combined = combine_files([file_obj], repo_path=repo)

        assert "=== FILE START: outside.py ===" in combined.text
        assert "print('x')" in combined.text

    def test_empty_file_list(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()

        combined = combine_files([], repo_path=repo)

        assert combined.text.strip() == ""


class TestCLI:
    """Tests for CLI interface"""

    def test_creates_combined_file(self, tmp_path):
        runner = CliRunner()
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

    def test_handles_empty_repo(self, tmp_path):
        runner = CliRunner()
        repo = tmp_path / "empty_repo"
        repo.mkdir()
        output_file = tmp_path / "combined.txt"

        result = runner.invoke(app, [str(repo), "--output", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert content.strip() == ""

    def test_default_output_path(self, tmp_path, monkeypatch):
        runner = CliRunner()
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("print('hello')")

        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, [str(repo)])

        assert result.exit_code == 0
        default_output = tmp_path / "combined.txt"
        assert default_output.exists()
        content = default_output.read_text()
        assert "=== FILE START: a.py ===" in content

    def test_custom_include_patterns(self, tmp_path):
        runner = CliRunner()
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "test.js").write_text("console.log('hi')")
        (repo / "test.py").write_text("print('hi')")
        output_file = tmp_path / "combined.txt"

        result = runner.invoke(
            app,
            [str(repo), "--include", "**/*.js", "--output", str(output_file)]
        )

        assert result.exit_code == 0
        content = output_file.read_text()
        assert "test.js" in content
        assert "test.py" not in content

    def test_custom_exclude_patterns(self, tmp_path):
        runner = CliRunner()
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "keep.py").write_text("keep")
        (repo / "skip.py").write_text("skip")
        output_file = tmp_path / "combined.txt"

        result = runner.invoke(
            app,
            [
                str(repo),
                "--exclude", "skip.py",
                "--output", str(output_file)
            ]
        )

        assert result.exit_code == 0
        content = output_file.read_text()
        assert "keep.py" in content
        assert "skip.py" not in content
