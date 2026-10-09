"""Tests for citrus_genetics.scripts.check_loc."""

from __future__ import annotations

from citrus_genetics.scripts.check_loc import (
    collect_python_functions,
    count_file_lines,
    main,
    scan_python_files,
)


class TestCountFileLines:
    def test_counts_lines(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("a\nb\nc\n", encoding="utf-8")
        assert count_file_lines(f) == 3

    def test_missing_file(self, tmp_path):
        f = tmp_path / "missing.py"
        assert count_file_lines(f) == 0


class TestCollectPythonFunctions:
    def test_finds_function(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text("def foo():\n    pass\n", encoding="utf-8")
        funcs = collect_python_functions(f)
        assert len(funcs) == 1
        assert funcs[0][0] == "foo"

    def test_finds_async_function(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text("async def bar():\n    pass\n", encoding="utf-8")
        funcs = collect_python_functions(f)
        assert len(funcs) == 1
        assert funcs[0][0] == "bar"

    def test_finds_method(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text("class C:\n    def m(self):\n        pass\n", encoding="utf-8")
        funcs = collect_python_functions(f)
        assert len(funcs) == 1
        assert funcs[0][0] == "C.m"

    def test_finds_nested_function(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text("def outer():\n    def inner():\n        pass\n", encoding="utf-8")
        funcs = collect_python_functions(f)
        assert len(funcs) == 2
        names = {n for n, _, _ in funcs}
        assert "outer" in names
        assert "outer.inner" in names

    def test_syntax_error_returns_empty(self, tmp_path):
        f = tmp_path / "bad.py"
        f.write_text("def (\n", encoding="utf-8")
        assert collect_python_functions(f) == []


class TestScanPythonFiles:
    def test_file_under_limit(self, tmp_path):
        f = tmp_path / "ok.py"
        f.write_text("x = 1\n" * 10, encoding="utf-8")
        fv, fnv = scan_python_files(tmp_path, 600, 60)
        assert len(fv) == 0
        assert len(fnv) == 0

    def test_file_over_limit(self, tmp_path):
        f = tmp_path / "big.py"
        f.write_text("x = 1\n" * 601, encoding="utf-8")
        fv, _fnv = scan_python_files(tmp_path, 600, 60)
        assert len(fv) == 1
        assert fv[0].line_count == 601

    def test_file_at_limit(self, tmp_path):
        f = tmp_path / "exact.py"
        f.write_text("x = 1\n" * 600, encoding="utf-8")
        fv, _ = scan_python_files(tmp_path, 600, 60)
        assert len(fv) == 0

    def test_function_over_limit(self, tmp_path):
        f = tmp_path / "long_fn.py"
        body = "    x = 1\n" * 60
        f.write_text(f"def big():\n{body}", encoding="utf-8")
        _, fnv = scan_python_files(tmp_path, 600, 60)
        assert len(fnv) == 1
        assert fnv[0].name == "big"
        assert fnv[0].line_count == 61

    def test_function_at_limit(self, tmp_path):
        f = tmp_path / "ok_fn.py"
        body = "    x = 1\n" * 59
        f.write_text(f"def ok():\n{body}", encoding="utf-8")
        _, fnv = scan_python_files(tmp_path, 600, 60)
        assert len(fnv) == 0

    def test_ignores_non_python(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("x\n" * 1000, encoding="utf-8")
        fv, _fnv = scan_python_files(tmp_path, 600, 60)
        assert len(fv) == 0


class TestMain:
    def test_clean_returns_zero(self, tmp_path):
        f = tmp_path / "ok.py"
        f.write_text("x = 1\n", encoding="utf-8")
        rc = main(["--root", str(tmp_path)])
        assert rc == 0

    def test_violation_returns_one(self, tmp_path):
        f = tmp_path / "big.py"
        f.write_text("x = 1\n" * 601, encoding="utf-8")
        rc = main(["--root", str(tmp_path)])
        assert rc == 1

    def test_missing_root_returns_one(self, tmp_path):
        rc = main(["--root", str(tmp_path / "nonexistent")])
        assert rc == 1

    def test_custom_limits(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text("x = 1\n" * 50, encoding="utf-8")
        assert main(["--root", str(tmp_path), "--max-file-lines", "100"]) == 0
        assert main(["--root", str(tmp_path), "--max-file-lines", "40"]) == 1
