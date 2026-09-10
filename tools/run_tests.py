"""Run nested unittest scripts and reject empty discovery or silent test files."""

from pathlib import Path
import re
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / "tests").rglob("test_*.py"))
    if not paths:
        print("FAIL: no test files discovered", file=sys.stderr)
        return 1
    failures = 0
    total = 0
    skipped = 0
    for path in paths:
        try:
            result = subprocess.run(
                [sys.executable, str(path)],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired:
            print(f"FAIL {path.relative_to(root)}: exceeded 120 seconds")
            failures += 1
            continue
        output = result.stdout + result.stderr
        counts = re.findall(r"^Ran (\d+) tests? in ", output, re.MULTILINE)
        count = sum(map(int, counts))
        total += count
        skipped += sum(map(int, re.findall(r"skipped=(\d+)", output)))
        passed = result.returncode == 0 and count > 0
        failures += not passed
        print(f"{'PASS' if passed else 'FAIL'} {path.relative_to(root)}: {count} tests")
        if not passed:
            print(output)
    print(f"{len(paths)} files; {total} tests; {skipped} skipped; {failures} failed files")
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
