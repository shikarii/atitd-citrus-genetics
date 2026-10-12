"""LOC (lines of code) limit enforcement for the citrus-genetics project.

Scans Python, TypeScript, and C++ files for LOC violations:
- Python files (python/): per-file (600) and per-function (60) limits.
- TypeScript files (web/src/): per-file (400) limits.
- C++ files (native/): per-file (500) limits.

Exit code 0 means no violations. Exit code 1 means at least one violation was
found. All violation output is written to stderr.

Usage::

    python -m citrus_genetics.scripts.check_loc [options]

Options:
    --max-file-lines INT         Maximum lines per Python file (default: 600).
    --max-function-lines INT     Maximum lines per function/method (default: 60).
    --max-ts-file-lines INT      Maximum lines per TypeScript file (default: 400).
    --max-cpp-file-lines INT     Maximum lines per C++ file (default: 500).
    --root PATH                  Root directory to scan (default: python/).
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class FileViolation(NamedTuple):
    """A file-level LOC violation."""

    path: Path
    line_count: int
    limit: int


class FunctionViolation(NamedTuple):
    """A function or method LOC violation."""

    path: Path
    name: str
    start_line: int
    end_line: int
    line_count: int
    limit: int


# ---------------------------------------------------------------------------
# Counting helpers
# ---------------------------------------------------------------------------


def count_file_lines(path: Path) -> int:
    """Return the number of lines in *path*.

    Args:
        path: The file to count.

    Returns:
        Total line count (including blank lines and comments).
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return len(text.splitlines())


def collect_python_functions(path: Path) -> list[tuple[str, int, int]]:
    """Parse *path* with the AST and return all function/method spans.

    Args:
        path: A Python source file to parse.

    Returns:
        A list of ``(qualified_name, start_line, end_line)`` tuples for every
        ``FunctionDef`` and ``AsyncFunctionDef`` node in the module.  Returns
        an empty list if the file cannot be parsed.
    """
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    except OSError:
        return []

    results: list[tuple[str, int, int]] = []
    _walk_functions(tree, results, prefix="")
    return results


def _walk_functions(
    node: ast.AST,
    results: list[tuple[str, int, int]],
    prefix: str,
) -> None:
    """Recursively walk *node* and append function spans to *results*.

    Args:
        node: The current AST node.
        results: Accumulator for ``(name, start_line, end_line)`` entries.
        prefix: Dotted name prefix from enclosing classes/functions.
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            class_prefix = f"{prefix}{child.name}." if prefix else f"{child.name}."
            _walk_functions(child, results, class_prefix)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qualified = f"{prefix}{child.name}"
            start = child.lineno
            end = child.end_lineno if child.end_lineno is not None else child.lineno
            results.append((qualified, start, end))
            _walk_functions(child, results, f"{qualified}.")
        else:
            _walk_functions(child, results, prefix)


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


def scan_python_files(
    root: Path,
    max_file_lines: int,
    max_function_lines: int,
) -> tuple[list[FileViolation], list[FunctionViolation]]:
    """Scan all Python files under *root* for LOC violations.

    Args:
        root: Directory to scan recursively.
        max_file_lines: Maximum allowed lines per file.
        max_function_lines: Maximum allowed lines per function/method.

    Returns:
        A pair ``(file_violations, function_violations)``.
    """
    file_violations: list[FileViolation] = []
    function_violations: list[FunctionViolation] = []

    for path in sorted(root.rglob("*.py")):
        line_count = count_file_lines(path)
        if line_count > max_file_lines:
            file_violations.append(FileViolation(path, line_count, max_file_lines))

        for name, start, end in collect_python_functions(path):
            func_lines = end - start + 1
            if func_lines > max_function_lines:
                function_violations.append(FunctionViolation(path, name, start, end, func_lines, max_function_lines))

    return file_violations, function_violations


def scan_typed_files(
    root: Path,
    max_file_lines: int,
    extensions: tuple[str, ...],
) -> list[FileViolation]:
    """Scan files with given extensions under *root* for file-level LOC violations.

    Args:
        root: Directory to scan recursively.
        max_file_lines: Maximum allowed lines per file.
        extensions: File extensions to match (e.g., ('.ts', '.tsx')).

    Returns:
        A list of file-level violations.
    """
    violations: list[FileViolation] = []

    if not root.is_dir():
        return violations

    for ext in extensions:
        for path in sorted(root.rglob(f"*{ext}")):
            # Skip node_modules, dist, build directories
            parts = path.parts
            if any(p in ("node_modules", "dist", "build", "__pycache__") for p in parts):
                continue
            line_count = count_file_lines(path)
            if line_count > max_file_lines:
                violations.append(FileViolation(path, line_count, max_file_lines))

    return violations


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def report_violations(
    file_violations: list[FileViolation],
    function_violations: list[FunctionViolation],
) -> None:
    """Write all violation messages to stderr.

    Args:
        file_violations: File-level LOC violations to report.
        function_violations: Function-level LOC violations to report.
    """
    stderr = sys.stderr

    if file_violations:
        stderr.write("LOC check: file line-count violations\n")
        stderr.write(f"  Limit: {file_violations[0].limit} lines per file\n")
        for fv in file_violations:
            stderr.write(f"  {fv.path}  ({fv.line_count} lines)\n")
        stderr.write("\n")

    if function_violations:
        stderr.write("LOC check: function/method line-count violations\n")
        stderr.write(f"  Limit: {function_violations[0].limit} lines per function\n")
        for fn in function_violations:
            stderr.write(
                f"  {fn.path}:{fn.start_line}  {fn.name}"
                f"  ({fn.line_count} lines, lines {fn.start_line}-{fn.end_line})\n"
            )
        stderr.write("\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser.

    Returns:
        Configured ``ArgumentParser`` instance.
    """
    parser = argparse.ArgumentParser(
        prog="check_loc",
        description="Enforce per-file and per-function LOC limits across all languages.",
    )
    parser.add_argument(
        "--max-file-lines",
        type=int,
        default=600,
        metavar="INT",
        help="Maximum lines per Python file (default: 600).",
    )
    parser.add_argument(
        "--max-function-lines",
        type=int,
        default=60,
        metavar="INT",
        help="Maximum lines per Python function/method (default: 60).",
    )
    parser.add_argument(
        "--max-ts-file-lines",
        type=int,
        default=400,
        metavar="INT",
        help="Maximum lines per TypeScript file (default: 400).",
    )
    parser.add_argument(
        "--max-cpp-file-lines",
        type=int,
        default=500,
        metavar="INT",
        help="Maximum lines per C++ file (default: 500).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("python"),
        metavar="PATH",
        help="Root directory for Python scan (default: python/).",
    )
    return parser


def _scan_and_report_typed(
    label: str,
    roots: list[Path],
    max_lines: int,
    extensions: tuple[str, ...],
) -> list[FileViolation]:
    """Scan typed files across roots and report violations."""
    violations: list[FileViolation] = []
    for r in roots:
        violations.extend(scan_typed_files(r, max_lines, extensions))
    if violations:
        sys.stderr.write(f"LOC check: {label} file violations (limit: {max_lines})\n")
        for fv in violations:
            sys.stderr.write(f"  {fv.path}  ({fv.line_count} lines)\n")
        sys.stderr.write("\n")
    return violations


def main(argv: list[str] | None = None) -> int:
    """Entry point for the LOC check script.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]`` when ``None``.

    Returns:
        Exit code: 0 for no violations, 1 for one or more violations.
    """
    args = build_parser().parse_args(argv)

    all_fv: list[FileViolation] = []
    all_fnv: list[FunctionViolation] = []

    # Python
    if args.root.is_dir():
        fv, fnv = scan_python_files(args.root, args.max_file_lines, args.max_function_lines)
        all_fv.extend(fv)
        all_fnv.extend(fnv)
        report_violations(fv, fnv)

    # TypeScript
    all_fv.extend(_scan_and_report_typed("TypeScript", [Path("web/src")], args.max_ts_file_lines, (".ts", ".tsx")))

    # C++
    all_fv.extend(_scan_and_report_typed(
        "C++", [Path("native/src"), Path("native/include")], args.max_cpp_file_lines, (".cpp", ".h", ".hpp", ".cu"),
    ))

    total = len(all_fv) + len(all_fnv)
    if total:
        sys.stderr.write(f"check_loc: {total} violation(s) found ({len(all_fv)} file, {len(all_fnv)} function)\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
