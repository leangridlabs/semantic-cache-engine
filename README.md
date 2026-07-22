# Semantic Cache Engine — LeanGrid Labs

Stop paying Copilot to re-read your codebase every session.

Semantic Cache Engine sits alongside GitHub Copilot and caches your reasoning
context locally. Warm sessions answer from cache — zero tokens, instant recall.

---

## About LeanGrid Labs

Every new Copilot session starts blind. The model re-reads and re-familiarizes
with your codebase before it can help with anything — and every developer on
your team pays that cost independently, every day.

We measured the overhead and built something to stop it. Semantic Cache Engine
caches the familiarization context locally so warm sessions skip straight to
useful. The cache gets smarter the longer you use it, and when a teammate
imports your bundle they start day one already warm.

Local-first, no server, no API key. VS Code is the first surface — an open API
for other editors and agents is on the roadmap.

---

## What we can prove

**75–78% fewer tokens at session start**
Measured against realistic top-K retrieval — not a naive full-repo dump.
Real OpenAI API calls (gpt-4o-mini), two separate machines, same result.
This is before the first question. The cache hasn't even been used yet.

| Run | Result |
|---|---|
| Founder machine (Jun 15, 2026) | 75.12% savings vs top-K |
| Alpha tester (Jun 29, 2026) | 78.0% savings vs top-K |

**Zero tokens on a cache hit**
When the engine recalls a cached answer, your model is not called.
The answer comes from local SQLite. Token count: 0.
The Docker demo shows this directly — watch the output.

**Portable across machines**
Export your reasoning cache as an encrypted bundle. A teammate imports it
and starts their first session warm. They do not pay the cold-start cost
you already paid. The Docker demo runs this end-to-end: session-a exports,
session-b imports cold, answers 10/10 questions without calling the model.

**Zero outbound connections except your LLM**
Verified via `netstat` on two separate machines during a full measurement run.
1,694 chunks ingested. The only remote connection was the configured provider.
No telemetry. No analytics. No third-party hosts. Nothing phoning home.

| What was checked | Run 1 (Founder) | Run 2 (Alpha tester · Jun 29, 2026) |
|---|---|---|
| Remote hosts during full run | ✅ Only provider endpoint | ✅ 0 remote connections |
| Telemetry / analytics hosts | ✅ None observed | ✅ Rejected by schema at runtime |

Full methodology and raw artifacts: `EVIDENCE.md` in the
[main repository](https://github.com/leangridlabs/semantic-cache-engine).

The 75–78% figure is per-developer, per-session. When teams share bundles,
each teammate starts warm — the same savings, without paying the cold-start
cost again.

---

## How savings compound over time

Every question the engine answers commits a reasoning card to the local cache.
The more questions asked against a codebase, the more cards accumulate. When
you export a bundle and a teammate imports it, they start their first session
with your full question history already warm — they do not pay the cold-start
cost you already paid.

The hit rate on any given question depends on how many similar questions have
been asked before. A team that asks more questions builds a deeper cache; a
deeper cache answers more questions without calling the model. That relationship
is by design, not a guarantee — it depends on how your team's questions overlap.

---

## Install the VS Code extension

Download the VSIX from [GitHub Releases](https://github.com/leangridlabs/semantic-cache-engine/releases)
and install it in VS Code:

```
Extensions panel → ⋯ → Install from VSIX…
```

No account required. No API key. Data stays on your machine.

---

## Run the interactive demo

Docker required. Shows the cold → warm savings story end-to-end in ~2 minutes.

```bash
docker run -it ghcr.io/leangridlabs/semantic-cache-engine-demo:latest
```

Or build locally from this repo:

```bash
cd docker
docker build -t ghcr.io/leangridlabs/semantic-cache-engine-demo:latest .
docker run -it ghcr.io/leangridlabs/semantic-cache-engine-demo:latest
```

The demo:
1. Ingests the Flask 3.0.3 source tree
2. Runs 10 questions cold — 0 cache hits, 10 cards created
3. Exports an AES-256-GCM encrypted bundle (open the file: it's unreadable)
4. Imports the bundle into a fresh workspace
5. Runs the same 10 questions warm — 10 hits, 0 tokens used

---

## Repository structure

```
docker/
  Dockerfile      Demo image definition
  demo/
    demo.py       Interactive 5-step terminal walkthrough
```

---

## Help us prove this works (optional, but it matters)

We can show you our own numbers. What we can't show you — yet — is whether
this holds up across dozens of codebases, teams, and workflows we've never
seen.

That's where you come in.

The extension includes a one-command telemetry export that produces an
anonymized JSON report: cache hit rates, token savings, latency reduction.
No source code. No file paths. No workspace names. Just numbers.

**To export your report:**

Open the Command Palette (`Ctrl+Shift+P`) and run:
```
Semantic Cache: Export LeanGrid Telemetry Report
```

Select a window (7, 14, or 30 days). The extension auto-detects your Copilot
model and writes the file to `.reason/runs/telemetry/` in your workspace.

**To share it:** post the JSON in a
[GitHub Discussion](https://github.com/leangridlabs/semantic-cache-engine/discussions)
or email it to [support@leangridlabs.com](mailto:support@leangridlabs.com).

Every report we receive is a data point on a codebase we didn't write. Enough
of those, and the savings claim stops being a lab result and becomes a
cross-codebase record. That record is what drives the roadmap — the features
that get built next are the ones the data says matter most.

Sharing is entirely optional and always will be. But if the tool is working for
you, sharing takes 30 seconds and directly shapes what comes next.

After 14 days of use, the extension will prompt you once with the option to
export and share your report. You can share, skip, or be reminded again later —
no data leaves your machine unless you choose to send it.

---

## Contributing and feedback

Found a bug or have a question? [Open a GitHub issue](https://github.com/leangridlabs/semantic-cache-engine/issues).

Found a security vulnerability? Please do not open a public issue.
Email [support@leangridlabs.com](mailto:support@leangridlabs.com) instead so
it can be addressed prior to public disclosure.

---

&copy; 2026 LeanGrid Labs
