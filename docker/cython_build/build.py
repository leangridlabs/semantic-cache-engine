#!/usr/bin/env python3
"""
Cython build script for the Semantic Cache Engine demo wheel.

Extracts the wheel, compiles core IP modules to .so extensions,
strips .py source for compiled modules, and writes the protected
package to <output_dir>.

Usage:
    build.py <wheel.whl> <output_dir>
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path

# Filenames (basename only) that remain as readable .py.
# These are interface contracts, entry points, and config loaders —
# no algorithmic IP lives here.
KEEP_PLAIN: frozenset[str] = frozenset({
    "__init__.py",
    "__main__.py",
    "cli.py",
    "settings.py",
    "direct_chat_contract.py",
    "sidecar_contract.py",
    "sidecar_adapter.py",
    "sidecar_perf.py",
    "telemetry_schema.py",
})


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: build.py <wheel.whl> <output_dir>", file=sys.stderr)
        sys.exit(1)

    wheel_path = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    staging = Path("/build/staging")

    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    # ── 1. Extract wheel ──────────────────────────────────────────────────
    print(f"==> Extracting {wheel_path.name} ...")
    with zipfile.ZipFile(wheel_path) as z:
        z.extractall(staging)

    pkg_dir = staging / "semantic_cache_engine"
    if not pkg_dir.exists():
        print("ERROR: semantic_cache_engine/ not found in wheel", file=sys.stderr)
        sys.exit(1)

    # ── 2. Collect modules to compile ────────────────────────────────────
    py_files: list[Path] = sorted(
        f
        for f in pkg_dir.rglob("*.py")
        if f.name not in KEEP_PLAIN and "__pycache__" not in str(f)
    )
    rel_paths = [str(f.relative_to(staging)) for f in py_files]
    print(f"==> {len(rel_paths)} modules queued for Cython compilation")

    # ── 3. Generate setup_cython.py ───────────────────────────────────────
    setup_py = staging / "setup_cython.py"
    setup_py.write_text(
        textwrap.dedent(
            f"""\
            from setuptools import setup
            from Cython.Build import cythonize

            modules = {rel_paths!r}

            setup(
                ext_modules=cythonize(
                    modules,
                    language_level=3,
                    compiler_directives={{
                        "always_allow_keywords": True,
                        "binding": True,
                    }},
                    nthreads=4,
                    quiet=False,
                ),
                zip_safe=False,
            )
            """
        )
    )

    # ── 4. Compile ────────────────────────────────────────────────────────
    print("==> Running Cython + gcc (this takes 1-2 minutes) ...")
    result = subprocess.run(
        [sys.executable, "setup_cython.py", "build_ext", "--inplace"],
        cwd=staging,
        text=True,
    )
    if result.returncode != 0:
        print("ERROR: Cython build failed", file=sys.stderr)
        sys.exit(result.returncode)

    # ── 5. Strip .py source for compiled modules ──────────────────────────
    stripped: list[str] = []
    compile_failed: list[str] = []
    for py_file in py_files:
        so_files = list(py_file.parent.glob(f"{py_file.stem}.cpython-*.so"))
        if so_files:
            py_file.unlink()
            stripped.append(py_file.name)
        else:
            compile_failed.append(py_file.name)

    print(f"==> Compiled and stripped : {len(stripped)} modules")
    if compile_failed:
        print(f"==> Compile failed (kept as .py): {compile_failed}")

    # ── 6. Clean intermediates ────────────────────────────────────────────
    for c_file in staging.rglob("*.c"):
        c_file.unlink()
    build_dir = staging / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    setup_py.unlink(missing_ok=True)

    # ── 7. Copy to output dir ─────────────────────────────────────────────
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in [pkg_dir, *staging.glob("*.dist-info")]:
        dst = out_dir / src.name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"==> Copied {src.name}/ -> {dst}")

    total_plain = len(KEEP_PLAIN) + len(compile_failed)
    print()
    print("Build complete.")
    print(f"  Compiled (.so) : {len(stripped)}")
    print(f"  Plain (.py)    : {total_plain}")


if __name__ == "__main__":
    main()
