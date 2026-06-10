# LeetCode Coach Kit

A reusable system for coaching LeetCode prep with an AI voice partner + honest logging. Clone it, make it yours, run it every session.

## How it works — a voice coach + the `lc` CLI

- **The voice coach** — a Claude app chat with `voice-coach-brief.md` uploaded, run in **voice mode**. Coaches your *thinking* (approach, complexity, edge cases), then reviews your code *with the context of your spoken reasoning*. It does **not** write your code.
- **The `lc` companion CLI** (`lc.py`) — a tiny local tool that gives a second, *habit-aware* opinion on the code (`lc review`) and **logs your session** into the `logs/` files (`lc log`). ~400 lines, one dependency, your own API key. Design + safety model in [`APP-SYSTEM-DESIGN.md`](APP-SYSTEM-DESIGN.md).

Talking problems through aloud builds interview fluency (the skill that sinks quiet coders); the code review + honest logging keep you from fooling yourself, because verbal fluency hides real bugs.

## What's in here

```
lc-coach-kit/
├── README.md                   ← you are here
├── voice-coach-brief.md        ← paste this into a Claude voice session
├── session-report-template.md  ← the end-of-session report format
├── lc.py                       ← the companion CLI (review + logging)
├── Makefile                    ← make install / setup / status / review / ...
├── requirements.txt            ← one dependency: anthropic
├── MANUAL.html                 ← the full system manual (open with `make docs`)
├── APP-SYSTEM-DESIGN.md/.html  ← deeper architecture + safety model
├── sets/                       ← bundled problem sets — pick one at setup
│   ├── neetcode150.md           ← NeetCode 150
│   └── blind75.md               ← Blind 75
└── logs/
    ├── problem-tracker.md       ← check off problems as you clean-solve them (seeded at setup)
    ├── spaced-rep-queue.md      ← +14d / +30d re-attempt schedule
    ├── weak-areas.md            ← your recurring mistakes (the engine)
    └── habits.md                ← optional daily tracking
```

## Prerequisites

**Python 3.10+**, **git**, and an **Anthropic API key** ([console.anthropic.com](https://console.anthropic.com)). Nothing else — no Node, Docker, or database.

| OS | Install Python + git |
|---|---|
| **macOS** | `brew install python git` |
| **Linux** (Debian/Ubuntu) | `sudo apt install python3 python3-venv git make` |
| **Linux** (Fedora) | `sudo dnf install python3 git make` |
| **Windows** | `winget install Python.Python.3.12 Git.Git` (or python.org + git-scm.com) |

## Install — macOS / Linux

```bash
git clone https://github.com/william-burks/lc-coach-kit.git
cd lc-coach-kit
python3 -m venv .venv && source .venv/bin/activate   # isolated; avoids system-pip issues
pip install -r requirements.txt                      # one dependency: anthropic
export ANTHROPIC_API_KEY=sk-...                       # add to ~/.zshrc (or ~/.bashrc) to persist
python lc.py setup                                   # name + language(s) + problem set — does NOT store your key
python lc.py status                                  # verify it reads your files
```

**Or skip the venv dance with the included Makefile** (macOS/Linux):

```bash
make install                       # creates the venv + installs deps
export ANTHROPIC_API_KEY=sk-...
make setup && make status          # then: make review / make log / make gap
make arm P="11 Container" M=INTERVIEW
make help                          # all targets
```

## Install — Windows (PowerShell)

```powershell
git clone https://github.com/william-burks/lc-coach-kit.git
cd lc-coach-kit
python -m venv .venv; .venv\Scripts\Activate.ps1     # cmd.exe: .venv\Scripts\activate.bat
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-..."                    # persist: setx ANTHROPIC_API_KEY "sk-..."
python lc.py setup
python lc.py status
```

Windows notes: use `python` (not `python3`); end a paste with **Ctrl-Z then Enter** (not Ctrl-D); the `Makefile` needs `make` (`winget install GnuWin32.Make`) — or just run everything in **WSL**, where the macOS/Linux steps work unchanged.

Your **API key is read from the environment, never written to a file** — set it once in your shell profile (`~/.zshrc` / `~/.bashrc`). The CLI reads/writes **only inside this folder** and **never runs AI output as code** — the model returns text, this code does the writes, and `lc log` shows a diff before saving. Full safety model in [`APP-SYSTEM-DESIGN.md`](APP-SYSTEM-DESIGN.md).

## Workflow — the exact steps

1. **Open a Claude chat** (the voice-capable app).
2. **Upload [`voice-coach-brief.md`](voice-coach-brief.md)** — no extra text needed; the doc *is* the prompt. (Fill its `[YOUR ...]` placeholders first.)
3. **Let Claude respond in text first**, and read it. *Don't* immediately jump to voice — let it process the brief. (Uploading then instantly hitting stop + "I uploaded a doc" is the wrong way.)
4. **Activate voice mode** in that same chat.
5. **Respond via voice** — pick your problem + mode, then run the whole session aloud. Complete the mode (TEACH or INTERVIEW).
6. **Paste your code into that same chat.** The coach already has the context of your spoken reasoning, so its review is informed.
7. **(Recommended) Also run `lc review`** for a second, *habit-aware* opinion on the code — checked against your tracked weak-spots.
8. **Debrief** — discuss, diagnose, and generate the session report ([`session-report-template.md`](session-report-template.md)).
9. **Run `lc log`** to record the session into your `logs/` files, and set the next-attempt date in [`logs/spaced-rep-queue.md`](logs/spaced-rep-queue.md).

## The two modes

- **TEACH** — you're learning or stuck. Socratic, guided, smallest hints, never the answer.
- **INTERVIEW** — you know it and want to perform. The coach goes quiet and acts as a real technical interviewer: verbal problem, no IDE, pseudocode-then-code, no help. (Full protocol in the brief.)

**Mode discipline:** re-attempt on/before the due date → INTERVIEW (a real retention test). Slipped past due → TEACH (relearn cleanly; a slipped INTERVIEW gives noisy data).

## The one rule that makes it work

**[`logs/weak-areas.md`](logs/weak-areas.md) is the engine.** Every repeated mistake goes on it. When one hits 3+ times, next week adds problems targeting it. This is what turns grinding volume into actual improvement.

And **grade honestly** — "clean" must mean clean-cold-solo. Over-crediting a coached solve drops a problem from review before it's stuck, and the whole system quietly stops working.

## Language note

Examples use C++. The *system* is language-agnostic — adapt the "standards" gate in the brief (the dependencies/syntax you keep forgetting) to whatever you interview in.
