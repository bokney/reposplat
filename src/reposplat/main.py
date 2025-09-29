
from typing import List
from pathlib import Path

import typer

from .core import get_files, combine_files, save_combined_files

app = typer.Typer(add_completion=False)

DEFAULT_INCLUDES = [
    "**/*.py",
    "**/pyproject.toml"
]

DEFAULT_EXCLUDES = [
    ".git/**",
    "__pycache__/**",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".venv/**",
    "venv/**",
    ".env/**",
    "env/**",
    "node_modules/**",
    ".DS_Store",
    "Thumbs.db",
    "*.log",
    ".pytest_cache/**",
    ".mypy_cache/**",
    ".coverage",
    "htmlcov/**",
    "*.egg-info/**",
    "dist/**",
    "build/**",
    ".ruff_cache/**",
    "*.so",
    "*.dylib",
    "*.dll",
    ".tox/**",
]


def _normalize_patterns(
    values: List[str] | None, default: List[str]
) -> List[str]:
    return values if values else list(default)


@app.command()
def main(
    repo_path: Path = typer.Argument(..., help="Path to the repository root"),
    include: List[str] = typer.Option(
        None,
        "--include",
        "-i",
        help="Glob patterns to include (can be repeated)"
    ),
    exclude: List[str] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Glob patterns to exclude (can be repeated)"
    ),
    output_path: Path = typer.Option(
        Path("combined"),
        "--output",
        "-o",
        help="File to write combined output to"
    )
) -> None:
    includes = _normalize_patterns(include, DEFAULT_INCLUDES)
    excludes = _normalize_patterns(exclude, DEFAULT_EXCLUDES)

    output_path = Path(output_path)
    if output_path.suffix != ".txt":
        output_path = output_path.with_suffix(".txt")

    files = get_files(repo_path, includes, excludes)
    combined = combine_files(files, repo_path=repo_path)
    save_combined_files(combined, output_path)
    typer.echo(f"Wrote {len(files)} files to {output_path}")


if __name__ == "__main__":
    app()
