# LabDebug

A lab-debugging assistant for college practicals (Java and Android XML).
Paste a broken lab program; LabDebug explains each bug in plain words, shows
the fully corrected program, and then strictly re-checks *your* fix like a
lab examiner.

Built by a solo indie developer during the **Meta Global AI Developer
Hackathon** (November 2026), track: **Indie** / **Build for Your World**.

## The problem

In diploma practicals, students lose most of their lab time to trivial
bugs: a missing semicolon, a mistyped XML attribute. The lab instructor
can't get to everyone, so students copy a classmate's working code without
understanding what was wrong.

## What LabDebug does

1. **Debug** - paste the broken program and (optionally) what it should do.
   LabDebug lists every bug as a one-line explanation, plus the corrected
   program and a one-line takeaway.
2. **Fix it yourself** - the corrected code is editable. Students are
   encouraged to type their own fix rather than copy-paste.
3. **Verify** - a strict re-check compares the original task, the broken
   program and the student's fix, returning **PASS** only if the program
   would actually run and meet the task.

## Where Muse Spark Open is load-bearing

Every analysis and every verification is a call to **Muse Spark Open**
(Meta's open-weight coding model) served through the **Baseten Model API**
(`meta-models/muse-spark-open`, OpenAI-compatible endpoint). The app itself
contains no rules, no pattern matching and no hard-coded answers: remove
the model and nothing works. The model's code understanding is the entire
product:

- `POST /api/debug` sends the broken program with a lab-instructor system
  prompt and parses the structured reply (BUGS / FIXED CODE / TAKEAWAY).
- `POST /api/verify` sends task + broken + corrected code with a strict
  examiner prompt and parses VERDICT (PASS/FAIL) + WHY.

We chose Muse Spark Open because practicals are small, self-contained
programs where an open-weight coding model gives fast, accurate, low-cost
answers - exactly what a student tool needs to be free to run.

## Tech stack

- Python 3 + Flask (backend, ~150 lines)
- Vanilla HTML/CSS/JS (frontend, no build step)
- Muse Spark Open via Baseten Model API

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export BASETEN_API_KEY=<your Baseten Model API key>
python app.py
# open http://127.0.0.1:5000
```

Get a free Baseten API key at <https://app.baseten.co> (no card needed for
free credits).

## What was built during the hackathon

Everything in this repository - the Flask backend, the structured prompt
and parsing layer, and the full UI - was written during the event window.
AI coding tools were used under the hackathon's rules; the project was
designed and directed by the author.

## Limitations

LabDebug is an AI static-review tool. It does not compile, run or
execute submitted code; PASS/FAIL verdicts are Muse Spark Open's reasoned
assessment, not a build result.
