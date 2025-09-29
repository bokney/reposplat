# 🗜️ reposplat

CLI tool to flatten repositories into LLM-friendly text dumps.

## Purpose

Combines all matching files into a single text file with clear delimiters.

## Usage

Basic usage (defaults to Python projects):

```bash
reposplat /path/to/repo
```

This creates `combined.txt` with all `.py` files and `pyproject.toml`.

### Custom patterns

```bash
# Include specific file types
reposplat . --include "**/*.js" --include "**/*.ts"

# Exclude patterns
reposplat . --exclude "tests/**" --exclude "*.min.js"

# Custom output location
reposplat . --output my-dump.txt
```

## Default Behavior

By default, `reposplat` includes:
- `**/*.py`
- `**/pyproject.toml`

And excludes common build/cache directories:
- `.git/`, `__pycache__/`, `.venv/`, `node_modules/`
- Build artifacts, logs, and cache files

## Output Format

```
=== FILE START: src/main.py ===

your code here

=== FILE END: src/main.py ===

=== FILE START: src/utils.py ===

more code

=== FILE END: src/utils.py ===
```

## License

MIT
