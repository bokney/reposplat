
from typing import List
from pathlib import Path

from pathspec import PathSpec

from .models import CombinedFiles, File


def build_pathspec(patterns: list[str]) -> PathSpec:
    return PathSpec.from_lines("gitwildmatch", patterns)


def should_include_file(
    file_path: Path,
    repo_path: Path,
    include_spec: PathSpec,
    exclude_spec: PathSpec
) -> bool:
    try:
        rel = file_path.relative_to(repo_path)
    except ValueError:
        return False

    rel_str = str(rel.as_posix())
    included = include_spec.match_file(rel_str)
    excluded = exclude_spec.match_file(rel_str)
    return bool(included) and not bool(excluded)


def scan_repository(
    repo_path: Path,
    include_spec: PathSpec,
    exclude_spec: PathSpec
) -> List[Path]:
    repo_path = repo_path.resolve()
    results = []
    for path in repo_path.rglob("*"):
        if (
            path.is_file()
            and should_include_file(
                path, repo_path, include_spec, exclude_spec
            )
        ):
            results.append(path.resolve())
    return results


def get_files(
    repo_path: Path, include: List[str], exclude: List[str]
) -> List[File]:
    include_spec = build_pathspec(include)
    exclude_spec = build_pathspec(exclude)

    paths = scan_repository(repo_path, include_spec, exclude_spec)

    files: List[File] = []
    for path in paths:
        contents = path.read_text(encoding="utf-8")
        files.append(File(path=path, contents=contents))

    return files


def combine_files(files: List[File], repo_path: Path) -> CombinedFiles:
    repo_path = repo_path.resolve()
    parts: list[str] = []

    for f in files:
        file_path = f.path.resolve()
        try:
            rel_path = file_path.relative_to(repo_path)
        except ValueError:
            rel_path = Path(file_path.name)

        parts.append(f"=== FILE START: {rel_path} ===")
        parts.append(f.contents)
        parts.append(f"=== FILE END: {rel_path} ===")

    text = "\n\n".join(parts)
    return CombinedFiles(text=text)


def save_combined_files(
    combined_files: CombinedFiles,
    output_path: Path,
) -> None:
    output_path = output_path.resolve()
    output_path.write_text(combined_files.text, encoding="utf-8")
