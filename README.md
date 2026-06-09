# LeetCode Coach Kit

A reusable system for coaching LeetCode prep with an AI voice partner + honest logging. Clone it, make it yours, run it every session.

## How it works — a voice coach + the `lc` CLI

- **The voice coach** — a Claude app chat with `voice-coach-brief.md` uploaded, run in **voice mode**. Coaches your *thinking* (approach, complexity, edge cases), then reviews your code *with the context of your spoken reasoning*. It does **not** write your code.
- **The `lc` companion CLI** — a tiny local tool that gives a second, *habit-aware* opinion on the code and **logs your session** into the `logs/` files. Its full design is in [`APP-SYSTEM-DESIGN.md`](APP-SYSTEM-DESIGN.md) — build it (≈a weekend), or run the review/log steps by hand until you do.

Talking problems through aloud builds interview fluency (the skill that sinks quiet coders); the code review + honest logging keep you from fooling yourself, because verbal fluency hides real bugs.

## What's in here

```
lc-coach-kit/
├── README.md                   ← you are here
├── voice-coach-brief.md        ← paste this into a Claude voice session
├── session-report-template.md  ← the end-of-session report format
└── logs/
    ├── problem-tracker.md       ← check off problems as you clean-solve them
    ├── spaced-rep-queue.md      ← +14d / +30d re-attempt schedule
    ├── weak-areas.md            ← your recurring mistakes (the engine — see below)
    └── habits.md                ← optional daily tracking
```

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
