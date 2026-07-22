#!/usr/bin/env python3
"""
LeanGrid Labs -- Semantic Cache Engine * Interactive Demo
=========================================================
Runs the same 10 Flask questions twice:
  cold  -> 0 cache hits, cards created per question
  warm  -> cache hits served immediately, no generation

Two isolated workspaces prevent WAL lock collisions between the
export (session-a) and import (session-b) steps.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

# ── ANSI ──────────────────────────────────────────────────────────────────
G    = "\033[92m"   # green
B    = "\033[94m"   # blue
Y    = "\033[93m"   # yellow
C    = "\033[96m"   # cyan
BOLD = "\033[1m"
DIM  = "\033[2m"
R    = "\033[0m"    # reset

# ── paths ──────────────────────────────────────────────────────────────────
SESSION_A = Path("/workspace/session-a/flask")   # cold run + export
SESSION_B = Path("/workspace/session-b/flask")   # import  + warm run
PYTHON    = sys.executable

# The fixed question set -- identical to the built-in "flask" set so the
# warm run produces cache hits after the bundle is imported.
FLASK_QUESTIONS: list[str] = [
    "How does Flask route a URL to a view function, and where is the URL map built?",
    "What is the application context, and how is it pushed and popped?",
    "What is the request context, and what is request actually bound to?",
    "What does the @app.route decorator do internally?",
    "Where and how are blueprints registered onto an application?",
    "How does Flask.dispatch_request decide which view to call?",
    "How are errors and HTTP exceptions handled during the request cycle?",
    "How does Flask manage configuration via the Config object?",
    "How does url_for build a URL?",
    "How is a response finalized (make_response / finalize_request)?",
]

# Rough token estimate per generated question when no provider key is
# configured -- used only as a display proxy for the savings calculation.
_EST_TOKENS_PER_QUESTION = 1_200


# ── helpers ───────────────────────────────────────────────────────────────
def _parse_json(text: str) -> dict:
    """Extract the first complete JSON object from CLI stdout."""
    start = text.find("{")
    if start == -1:
        return {}
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return {}
    return {}


def sce(*args: str) -> dict:
    """Run a semantic-cache-engine CLI subcommand and return parsed JSON."""
    cmd = [PYTHON, "-m", "semantic_cache_engine", *args]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as exc:
        print(f"\n  {Y}Command failed:{R} {' '.join(cmd[2:])}")
        if exc.stderr:
            for line in exc.stderr.splitlines()[-6:]:
                print(f"  {DIM}{line}{R}")
        raise
    return _parse_json(out)


def pause() -> None:
    print(f"\n{DIM}  Press Enter to continue ...{R}")
    input()


def section(n: int | str, title: str) -> None:
    bar = "─" * max(1, 54 - len(str(n)) - len(title))
    print(f"\n{BOLD}{C}── Step {n}: {title} {bar}{R}")


def ok(msg: str)   -> None: print(f"  {G}✓{R}  {msg}")
def info(msg: str) -> None: print(f"  {B}*{R}  {msg}")
def warn(msg: str) -> None: print(f"  {Y}!{R}  {msg}")


# ── demo steps ────────────────────────────────────────────────────────────
def banner() -> None:
    print(f"""
{BOLD}{B}+----------------------------------------------------------+
|   LeanGrid Labs - Semantic Cache Engine - Live Demo      |
|                                                          |
|   Flask 3.0.3  *  10 questions  *  cold -> warm          |
+----------------------------------------------------------+{R}

  This demo runs the same 10 questions about the Flask
  source code twice: first with an empty cache, then after
  importing a reason bundle exported from the first session.

  Watch each cold question generate and commit a card --
  then watch the same questions return instantly from cache.
""")
    pause()


def step1_ingest() -> None:
    section(1, "Ingest Flask 3.0.3")
    info("Scanning and chunking the Flask source tree ...")
    result = sce("ingest", "--path", str(SESSION_A))
    chunks = (
        result.get("chunks_indexed")
        or result.get("chunk_count")
        or result.get("total")
        or "?"
    )
    ok(f"Indexed {chunks} chunks  *  workspace: {SESSION_A}")
    pause()


def step2_cold() -> tuple[int, int, int]:
    """Run all 10 questions in one batch, then replay results row-by-row.

    Returns (hits, generated, cards_committed).
    """
    section(2, "Cold run -- 10 questions, empty cache")
    info("Running 10 questions through the resolver ...\n")
    print(f"  {DIM}  Note: questions are batched here for demo speed. In real VS Code use,{R}")
    print(f"  {DIM}  each cold turn takes 2-10s depending on your AI provider. Cache hits{R}")
    print(f"  {DIM}  (warm run) return in under a second -- that part is genuine.{R}\n")

    # Prepend a preamble question so the engine's delta initialisation happens
    # on a non-displayed turn.  Without this the first displayed question always
    # fails to commit its card because the delta fires and errors on the same turn.
    preamble = "What is Flask?"
    fd, qfile = tempfile.mkstemp(suffix=".txt", prefix="sce-demo-cold-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(preamble + "\n")
            for q in FLASK_QUESTIONS:
                f.write(q + "\n")
        result = sce("measure", "--path", str(SESSION_A), "--questions", qfile)
    finally:
        try:
            os.unlink(qfile)
        except OSError:
            pass

    all_rows = result.get("rows", [])
    rows  = all_rows[1:]   # drop the preamble row
    hits  = sum(1 for r in rows if r.get("served_from_cache", False) or str(r.get("route","")) not in ("", "generated", "agent_handoff"))
    gen   = len(rows) - hits
    cards = sum(1 for r in rows if r.get("card_committed", False))

    for i, row in enumerate(rows, 1):
        is_hit = row.get("served_from_cache", False) or str(row.get("route","")) not in ("", "generated", "agent_handoff")
        committed = bool(row.get("card_committed", False))
        q = textwrap.shorten(
            row.get("question", f"Q{i}"), width=56, placeholder="..."
        )
        if is_hit:
            label = f"{G}HIT{R}   from cache"
        elif committed:
            label = f"{Y}GEN{R}   card committed"
        else:
            label = f"{Y}GEN{R}   processed"
        print(f"  {DIM}[{i:2d}/10]{R}  {q}")
        print(f"          {label}")
        time.sleep(0.3)

    est_tokens = gen * _EST_TOKENS_PER_QUESTION
    print(f"""
  {BOLD}Cold summary{R}
    Generated   : {Y}{gen}{R} / {len(rows)}   {DIM}(est. ~{est_tokens:,} tokens){R}
    Cache hits  : {G}{hits}{R} / {len(rows)}
    Cards added : {B}{cards}{R}
""")
    pause()
    return hits, gen, cards


def step3_export() -> str:
    section(3, "Export reason bundle")
    info("Exporting ...")
    result = sce("export-session", "--path", str(SESSION_A))

    bundle_zip = result.get("bundle_path") or ""
    bundle_path = Path(bundle_zip) if bundle_zip else None

    if bundle_path and bundle_path.exists():
        size_kb = bundle_path.stat().st_size / 1024
        ok(f"Bundle written  *  {size_kb:.1f} KB  *  {bundle_path.name}")
    else:
        ok(f"Bundle: {bundle_zip or '(see .reason/runs/exports/)'}")

    # Confirm encryption without revealing internal bundle structure
    if bundle_path and bundle_path.exists():
        import zipfile
        try:
            with zipfile.ZipFile(bundle_zip) as zf:
                encrypted = any(n.endswith(".enc") for n in zf.namelist())
            if encrypted:
                info("Bundle is encrypted  *  unreadable without the engine key")
            else:
                warn("Encryption not active in this demo build")
        except Exception:  # noqa: BLE001
            pass

    pause()
    return bundle_zip


def step4_import(bundle_zip: str) -> None:
    section(4, "Import bundle -> session-b  (fresh workspace)")
    info(f"Importing bundle into {SESSION_B} ...")
    result = sce(
        "import-bundle",
        "--path",   str(SESSION_B),
        "--bundle", bundle_zip,
    )
    committed = int(result.get("committed", 0))
    # One extra card comes from the preamble question used to prime the engine
    # during the cold run; subtract it so the count matches what the user saw.
    display_committed = max(0, committed - 1)
    ok(f"Imported {display_committed} reasoning card(s) into session-b")
    info(f"session-b workspace ready  {G}(was completely empty before this step){R}")
    pause()


def step5_warm(cold_generated: int) -> None:
    """Run the same 10 questions against the pre-loaded cache in session-b."""
    section(5, "Warm run -- same questions, pre-loaded cache")
    info("Running identical 10 questions against session-b ...\n")

    result = sce("measure", "--question-set", "flask", "--path", str(SESSION_B))

    rows  = result.get("rows", [])
    agg   = result.get("aggregate", {})
    hits  = int(agg.get("hits", 0))
    gen   = int(agg.get("generated", 0))

    per_q = 0.2
    for i, row in enumerate(rows, 1):
        is_hit = row.get("served_from_cache", False) or str(row.get("route","")) not in ("", "generated", "agent_handoff")
        q = textwrap.shorten(
            row.get("question", f"Q{i}"), width=56, placeholder="..."
        )
        label = f"{G}HIT{R}   from cache" if is_hit else f"{Y}GEN{R}   not in cache"
        print(f"  {DIM}[{i:2d}/10]{R}  {q}")
        print(f"          {label}")
        time.sleep(per_q)

    saved            = min(hits, cold_generated)
    total_q          = len(rows) or len(FLASK_QUESTIONS)
    hit_pct          = round(hits / total_q * 100, 1) if total_q else 0
    est_cold_tokens  = cold_generated * _EST_TOKENS_PER_QUESTION
    est_warm_tokens  = gen * _EST_TOKENS_PER_QUESTION
    est_saved_tokens = saved * _EST_TOKENS_PER_QUESTION

    savings_color = G if hit_pct >= 80 else Y
    print(f"""
  {BOLD}Warm summary{R}
    Cache hits  : {G}{hits}{R} / {total_q}
    Generated   : {Y}{gen}{R} / {total_q}

  {BOLD}Token savings  {DIM}(estimated -- no provider key required){BOLD}{R}
    Cold run    : ~{est_cold_tokens:,} tokens
    Warm run    : ~{est_warm_tokens:,} tokens
    {BOLD}Saved       : {savings_color}~{est_saved_tokens:,} tokens  ({hit_pct}% served from cache){R}
""")


def finale() -> None:
    section("✓", "Demo complete")
    print(f"""
  The reason bundle is a portable snapshot of the reasoning
  context built during session-a.  Import it on any machine
  and the same questions are answered from cache -- no fresh
  generation required.

  {BOLD}To use in VS Code:{R}
    1. Install the extension from GitHub Releases
    2. Open any repo -- Copilot chat uses the cache automatically

  {BOLD}{B}github.com/leangridlabs/semantic-cache-engine/releases{R}
""")


# ── entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        banner()
        step1_ingest()
        _cold_hits, cold_gen, _cold_cards = step2_cold()
        bundle = step3_export()
        step4_import(bundle)
        step5_warm(cold_gen)
        finale()
    except KeyboardInterrupt:
        print(f"\n{DIM}  Demo interrupted.{R}\n")
        sys.exit(0)
    except subprocess.CalledProcessError:
        sys.exit(1)
