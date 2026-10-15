# orchestrate-kit

Reusable scaffold for **HackerRank Orchestrate** 24-hour hackathons.
Built around one principle: **the model proposes, deterministic code decides, the receipt keeps evidence.**

This is exactly the judging rubric Orchestrate rewards — code that runs, an agent that actually works, a clear architecture you can defend to the AI judge, and a transcript of how you used AI tools.

> The August 2026 problem (`Message Notification Router`) is included as a **practice target** under `dataset/`. It is NOT the October 26 problem — treat it as a dry run to learn the scaffold. When the real challenge arrives, you only fill in a new `problems/*.py`.

## Architecture

```
messages.csv ──▶ loader ──▶ agent.propose() ──▶ verifier.verify() ──▶ output.csv
                         │                         │
                  LLM (OPENAI_API_KEY)       deterministic guards:
                  or offline heuristic        • action ∈ {notify,digest,mute}
                                             • message_type ∈ allowed set
                                             • confidence ∈ [0,1]
                                             • evidence ids filtered to known history
                                             • reason never empty
```

Every prediction flows the same path: **load → propose → verify → receipt**. No single LLM call is the whole agent; the boundaries (context build, schema validation, retry/abstain) are explicit and inspectable.

## Quick start

```bash
# offline heuristic — no API key needed, always produces a valid output.csv
python solve.py

# with an LLM (set your key; falls back to heuristic on any failure)
export OPENAI_API_KEY=sk-...
ORC_MODE=llm python solve.py

# score the practice target against ground truth
python eval.py
```

## Files

| File | Role |
|---|---|
| `orchestrate_kit/loader.py` | Generic CSV reader + context join |
| `orchestrate_kit/agent.py` | LLM propose layer + offline heuristic fallback |
| `orchestrate_kit/verifier.py` | Deterministic adjudication — never trusts raw model output |
| `orchestrate_kit/log_utils.py` | AI chat transcript logger (`chat_transcript`) |
| `orchestrate_kit/solve.py` | Generic engine — swaps problems, reuses everything |
| `problems/whatsapp_router.py` | Concrete problem implementation (the August dry run) |
| `eval.py` | Accuracy check on `sample_messages.csv` + invariant asserts |

## How to adapt to a new problem (the 24-hour playbook)

1. Copy `problems/whatsapp_router.py` → `problems/<new>.py`.
2. Set `ALLOWED_ACTIONS` / `ALLOWED_TYPES` from the new problem statement.
3. Point `extra_context()` at the new dataset's CSVs.
4. Rewrite `system_prompt()` / `build_prompt()` / `heuristic()` / `extract_evidence()`.
5. `python solve.py` to emit `output.csv`; `python eval.py` to sanity-check.
6. Zip the repo (with LICENSE + README) → submit as `code.zip`, plus `output.csv` and the generated `log.txt` as `chat_transcript`.

## Why this wins the AI-judge interview

- **Trace one input through the system**: read → clean → contextualize → propose → verify → flag-or-emit. Every step has a home.
- **Failure modes are documented**, not hidden. The verifier's degrade-and-defer path is the honest story.
- **Evidence over guesswork**: predictions cite real `message_id`s from history; the judge can audit them.
- **Reproducible**: zero hard-coded secrets, zero dependencies beyond the standard library.

MIT License.
