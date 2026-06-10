#!/usr/bin/env python3
"""lc — LeetCode Coach companion CLI.

The "second tool" in the LC Coach Kit loop: a habit-aware code review and
session logging into your local logs/ files. See APP-SYSTEM-DESIGN.md.

Safety: the AI only returns TEXT. All file writes are done by this code,
scoped to the LC folder, with a diff shown before `log` saves. No eval,
no shell-out to model output. BYO ANTHROPIC_API_KEY.
"""
import argparse
import datetime
import json
import os
import pathlib
import random
import re
import sys

EOF_HINT = "Ctrl-Z then Enter" if os.name == "nt" else "Ctrl-D"

KIT = {
    "brief": "voice-coach-brief.md",
    "weak": "logs/weak-areas.md",
    "queue": "logs/spaced-rep-queue.md",
    "tracker": "logs/problem-tracker.md",
    "habits": "logs/habits.md",
    "config": "config.md",
    "gaplog": "gap-analysis-log.md",
    "session": ".session",
    "pack": "session-pack.md",
}

# Bundled problem sets, selectable at setup → seed logs/problem-tracker.md.
SETS = {
    "1": ("NeetCode 150", "sets/neetcode150.md"),
    "2": ("Blind 75", "sets/blind75.md"),
}


# ---------- scoped file store ----------

def lc_dir():
    return pathlib.Path(os.environ.get("LC_DIR") or os.getcwd()).resolve()


def _resolve(rel):
    base = lc_dir()
    p = (base / rel).resolve()
    if p != base and base not in p.parents:
        raise SystemExit(f"refusing path outside the LC folder: {rel}")
    return p


def read(rel):
    p = _resolve(rel)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def write(rel, text):
    p = _resolve(rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def today():
    return datetime.date.today().isoformat()


def now():
    return datetime.datetime.now()


# ---------- Claude client ----------

def ask(system, user, max_tokens=1000):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("Set ANTHROPIC_API_KEY to your own Anthropic API key.")
    try:
        import anthropic
    except ImportError:
        raise SystemExit("Missing dependency. Run: pip install anthropic")
    model = os.environ.get("LC_MODEL", "claude-sonnet-4-6")
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


def read_input(args, prompt):
    """Code/report from --file, or pasted on stdin (Ctrl-D to end)."""
    if getattr(args, "file", None):
        return read(args.file)
    print(f"{prompt} (paste, then {EOF_HINT}):", file=sys.stderr)
    return sys.stdin.read()


def parse_json(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?|\n?```$", "", raw).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise SystemExit("Could not parse a JSON response from the model.")
    return json.loads(raw[start:end + 1])


def get_config():
    cfg = {}
    for line in read(KIT["config"]).splitlines():
        m = re.match(r"-\s*([\w ]+?):\s*(.+)", line)
        if m:
            cfg[m.group(1).strip().lower()] = m.group(2).strip()
    return cfg


# ---------- timer (.session) ----------

def start_timer(problem):
    write(KIT["session"], json.dumps({"problem": problem, "start": now().isoformat()}))


def stop_timer():
    txt = read(KIT["session"]).strip()
    if not txt:
        return None
    s = json.loads(txt)
    mins = (now() - datetime.datetime.fromisoformat(s["start"])).total_seconds() / 60
    write(KIT["session"], "")
    return s.get("problem"), round(mins, 1)


# ---------- table helpers (deterministic writes) ----------

def insert_table_row(text, header_sub, row):
    """Insert `row` after the last contiguous |-row of the table whose header
    line contains `header_sub`. Falls back to appending at end of file."""
    lines = text.splitlines()
    out, i, done = [], 0, False
    while i < len(lines):
        out.append(lines[i])
        if (not done and header_sub in lines[i]
                and lines[i].lstrip().startswith("|")):
            j = i + 1
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                out.append(lines[j])
                j += 1
            out.append(row)
            done = True
            i = j
            continue
        i += 1
    if not done:
        out.append(row)
    return "\n".join(out) + "\n"


def tick_tracker(text, problem_num, date):
    pat = re.compile(rf"- \[ \] {re.escape(problem_num)}(\b.*)$", re.MULTILINE)
    return pat.sub(rf"- [x] {problem_num}\1 — first clean: {date}", text, count=1)


# ---------- commands ----------

def _seed_set(rel, name):
    src = read(rel)
    if not src.strip():
        print(f"  (couldn't find {rel}; left tracker unchanged)")
        return False
    write(KIT["tracker"], src)
    print(f"  Seeded {KIT['tracker']} with {name} ({src.count('- [ ]')} problems).")
    return True


def _configure_set():
    """Pick a bundled set and seed the tracker. Returns the set name (or None).
    Guards against clobbering a tracker that already has clean solves."""
    print("\nProblem set:  [1] NeetCode 150 (default)   [2] Blind 75   [3] skip")
    choice = input("Choose [1]: ").strip() or "1"
    if choice not in SETS:
        return None
    name, rel = SETS[choice]
    has_solves = any(l.lstrip().startswith("- [x]")
                     for l in read(KIT["tracker"]).splitlines())
    if has_solves:
        if input(f"  {KIT['tracker']} has clean solves — overwrite with {name}? "
                 "[y/N]: ").strip().lower() != "y":
            print("  Kept your existing tracker.")
            return name
    _seed_set(rel, name)
    return name


def cmd_setup(args):
    print("LC Coach setup\n")
    name = input("Your name (optional): ").strip()
    lang = input("Primary language [C++]: ").strip() or "C++"
    lang2 = input("Diagnostic 2nd language (optional, e.g. Python): ").strip()
    set_name = _configure_set()
    lines = ["# LC Coach config\n\n", f"- name: {name}\n",
             f"- primary language: {lang}\n"]
    if lang2:
        lines.append(f"- diagnostic language: {lang2}\n")
    if set_name:
        lines.append(f"- problem set: {set_name}\n")
    write(KIT["config"], "".join(lines))
    extra = f" (+ {lang2} diagnostic)" if lang2 else ""
    tail = f"; set: {set_name}" if set_name else ""
    print(f"\nWrote {KIT['config']}. Language: {lang}{extra}{tail}")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\nYour API key is read from the environment (never stored here).")
        print("  export ANTHROPIC_API_KEY=sk-...      # add to ~/.zshrc to persist")


def _real_weak_tags():
    """(tag, fix-note) pairs from weak-areas.md, excluding example/header/empty
    rows. These are the user's actual tracked gaps — the curation source."""
    tags = []
    for line in read(KIT["weak"]).splitlines():
        if not line.lstrip().startswith("|") or "e.g." in line.lower():
            continue
        if set(line.strip()) <= set("|-: "):  # separator row
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        tag = cells[0] if cells else ""
        if not tag or tag in ("Tag", "Week"):  # header / wrong table
            continue
        tags.append((tag, cells[4] if len(cells) >= 5 else ""))
    return tags


def curated_warmup(mode, k=2):
    """Markdown for the curated warm-up: up to k random tracked gaps turned into
    recall prompts. Empty in INTERVIEW mode (warming up the answer contaminates
    the retention test) or when there's no user data yet."""
    if mode != "TEACH":
        return ("### Warm-up quiz\n(INTERVIEW mode — no warm-up; a primed answer "
                "contaminates the retention test.)\n")
    tags = _real_weak_tags()
    if not tags:
        return ("### Warm-up quiz\n(No tracked gaps yet — skip the curated warm-up; "
                "ask a couple of general complexity-recall questions instead.)\n")
    picks = random.sample(tags, min(k, len(tags)))
    lines = ["### Warm-up quiz — curated from my tracked gaps (TEACH only)",
             "Pose a fast recall question on each of these BEFORE I read the problem:"]
    for i, (tag, fix) in enumerate(picks, 1):
        lines.append(f"{i}. **{tag}**" + (f" — target: {fix}" if fix else ""))
    return "\n".join(lines) + "\n"


def cmd_arm(args):
    problem = args.problem
    mode = (args.mode or "TEACH").upper()
    key = problem.split()[0] if problem.split() else problem
    queue = read(KIT["queue"])
    history = "\n".join(l for l in queue.splitlines()
                        if l.lstrip().startswith("|") and key in l) or "(none logged)"
    if args.file:
        statement = read(args.file)
        src = f"from {args.file}"
    elif args.paste:
        print(f"Paste the problem statement ({EOF_HINT} to end):", file=sys.stderr)
        statement = sys.stdin.read()
        src = "pasted"
    else:
        statement = ("(No statement provided. Coach: recall or pose this problem "
                     "yourself, or ask the user to paste it.)")
        src = "coach-supplied"
    pack = (
        f"{read(KIT['brief'])}\n\n"
        f"---\n\n## THIS SESSION\n\n"
        f"- Problem: **{problem}**\n- Mode: **{mode}**\n- Problem source: {src}\n\n"
        f"### Problem statement\n{statement}\n\n"
        f"### Your prior attempts on this problem\n{history}\n\n"
        f"{curated_warmup(mode)}\n"
        f"### Watch these weak-spots\n{read(KIT['weak'])}\n"
    )
    write(KIT["pack"], pack)
    start_timer(problem)
    print(f"Session pack -> {KIT['pack']}  (mode {mode}; timer started)")
    print("Upload that file to your Claude voice session.")


def cmd_start(args):
    prob = args.problem or "(unspecified)"
    start_timer(prob)
    print(f"Timer started: {prob}")


def cmd_stop(args):
    r = stop_timer()
    print("No active timer." if not r else f"Stopped: {r[0]} — {r[1]} min")


def cmd_status(args):
    queue = read(KIT["queue"])
    weak = read(KIT["weak"])
    print(f"LC Coach — status ({lc_dir().name})\n")
    due = []
    for l in queue.splitlines():
        if "e.g." in l.lower():
            continue
        if l.lstrip().startswith("|") and re.search(r"\d{4}-\d{2}-\d{2}", l):
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            dates = re.findall(r"\d{4}-\d{2}-\d{2}", l)
            if len(cells) >= 3 and dates:
                duedate = dates[-1]
                if duedate <= today():
                    due.append(f"  • {cells[0]:<34} due {duedate}")
    print("Spaced-rep due/overdue:")
    print("\n".join(due) if due else "  (none)")
    print("\nFlagged weak areas:")
    flags = [l for l in weak.splitlines()
             if "FLAGGED" in l.upper() and l.lstrip().startswith("|")
             and "e.g." not in l.lower()]
    if flags:
        for l in flags:
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            print(f"  ⚑ {cells[0]}")
    else:
        print("  (none flagged)")


def cmd_review(args):
    code = read_input(args, "Paste your code")
    if not code.strip():
        raise SystemExit("No code provided.")
    cfg = get_config()
    system = (
        "You are a habit-aware code reviewer for LeetCode interview practice. "
        "Review the code for correctness, bugs, language standards (includes/"
        "imports, fixed-width types where relevant), and time/space complexity. "
        "Cross-reference the user's tracked weak-spots below and explicitly flag "
        "any that recur. Be concise and specific. Do NOT rewrite the code. "
        "End with a one-line verdict: clean-solo / with-assist / partial / failed."
    )
    user = (f"Language: {cfg.get('primary language', 'unspecified')}\n"
            f"Problem: {args.problem or 'unspecified'}\n\n"
            f"Tracked weak-spots:\n{read(KIT['weak'])}\n\n"
            f"Code:\n{code}")
    print("\n" + ask(system, user, max_tokens=900))


def _build_updates(d, date):
    prob = str(d.get("problem", "")).strip()
    outcome = str(d.get("outcome", "")).strip()
    updates = []
    qrow = (f"| {prob} | {date} | +14d | {outcome}"
            + (f" (~{d['time_min']}m)" if d.get("time_min") else "") + " |")
    updates.append(("queue", KIT["queue"], "First solved", qrow))
    eff = d.get("effort")
    note = d.get("habit_note") or f"{prob} {outcome}"
    hrow = f"| {date} | 1 | {note}" + (f" (effort {eff})" if eff else "") + " |"
    updates.append(("habits", KIT["habits"], "LC solved", hrow))
    for ws in d.get("weak_spots", []) or []:
        updates.append(("weak", KIT["weak"],
                         "| Tag", f"| {ws} | 1 | {date} | review | logged from session |"))
    if outcome == "clean-solo":
        num = prob.split()[0] if prob.split() else ""
        updates.append(("tracker-tick", KIT["tracker"], num, ""))
    return updates


def _diff(updates):
    print("\n── Proposed log updates ──────────────────────")
    for kind, path, _, row in updates:
        if kind == "tracker-tick":
            print(f"{path}:\n  ~ tick problem {row or _}  → [x] (clean solve)")
        else:
            print(f"{path}:\n  + {row}")


def cmd_log(args):
    report = read_input(args, "Paste your session report")
    if not report.strip():
        raise SystemExit("No report provided.")
    system = (
        "Extract structured logging data from this LeetCode session report. "
        "Return ONLY a JSON object with keys: problem (e.g. '11 Container'), "
        "outcome (one of clean-solo|with-assist|partial|failed), "
        "time_min (number or null), effort (1|2|3 or null), "
        "complexity_correct (true|false|null), weak_spots (array of short strings), "
        "date (YYYY-MM-DD or null), habit_note (short string)."
    )
    data = parse_json(ask(system, "Report:\n" + report, max_tokens=600))
    t = stop_timer()
    if t and not data.get("time_min"):
        data["time_min"] = t[1]
    date = data.get("date") or today()
    updates = _build_updates(data, date)
    _diff(updates)
    if input("\nApply these changes? [y/N]: ").strip().lower() != "y":
        print("Aborted — nothing written.")
        return
    for kind, path, anchor, row in updates:
        if kind == "tracker-tick":
            write(path, tick_tracker(read(path), row or anchor, date))
        else:
            write(path, insert_table_row(read(path), anchor, row))
    print("Logged.")


def cmd_gap(args):
    system = (
        "You are reviewing a learner's accumulated LeetCode logs to find TRENDS. "
        "Identify: weak areas repeating 3+ times, anything trending the wrong way, "
        "and the single highest-leverage focus for next week. Be concise and direct."
    )
    user = (f"weak-areas.md:\n{read(KIT['weak'])}\n\n"
            f"spaced-rep-queue.md:\n{read(KIT['queue'])}\n\n"
            f"habits.md:\n{read(KIT['habits'])}")
    out = ask(system, user, max_tokens=900)
    print("\n" + out)
    entry = f"\n## {today()} — gap analysis\n\n{out}\n"
    write(KIT["gaplog"], read(KIT["gaplog"]) + entry)
    print(f"\n(appended to {KIT['gaplog']})")


def main():
    p = argparse.ArgumentParser(prog="lc", description="LeetCode Coach companion CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup", help="name + language(s) -> config")
    a = sub.add_parser("arm", help="build a session pack for the voice coach")
    a.add_argument("problem")
    a.add_argument("--mode", choices=["TEACH", "INTERVIEW", "teach", "interview"])
    a.add_argument("--file", help="local file with the problem statement")
    a.add_argument("--paste", action="store_true", help="paste the problem statement")
    s = sub.add_parser("start", help="start the session timer")
    s.add_argument("problem", nargs="?")
    sub.add_parser("stop", help="stop the session timer")
    r = sub.add_parser("review", help="habit-aware code review")
    r.add_argument("--problem")
    r.add_argument("--file", help="read code from a file instead of pasting")
    lg = sub.add_parser("log", help="log a session report into logs/")
    lg.add_argument("--file", help="read the report from a file instead of pasting")
    sub.add_parser("status", help="what's due + flagged weak areas")
    sub.add_parser("gap", help="aggregate trend analysis across sessions")

    args = p.parse_args()
    {
        "setup": cmd_setup, "arm": cmd_arm, "start": cmd_start, "stop": cmd_stop,
        "review": cmd_review, "log": cmd_log, "status": cmd_status, "gap": cmd_gap,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
