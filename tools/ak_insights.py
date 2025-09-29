#!/usr/bin/env python3
import os, json, time, re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path.home() / "ak"
MEMLOG = BASE / "memories" / "memories.jsonl"
OUTDIR = BASE / "logs"

def load_last_days(days=7):
    if not MEMLOG.exists():
        return []
    cutoff = datetime.now() - timedelta(days=days)
    out = []
    with open(MEMLOG, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                ts = rec.get("timestamp")
                dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S") if ts else None
                if dt and dt >= cutoff:
                    out.append(rec)
            except Exception:
                pass
    return out

def tokenize(text):
    # very light tokenizer for phrase freq
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-:]", " ", text)
    toks = [t for t in text.split() if len(t) >= 3 and t not in {"the","and","you","but","for","with","that","from","this","have"}]
    return toks

def summarize(records):
    from collections import Counter, defaultdict
    # buckets
    moods = [ (r.get("timestamp",""), (r.get("text") or "").strip().lower()) for r in records if r.get("type")=="mood" ]
    habits = [ (r.get("timestamp",""), (r.get("text") or "").strip()) for r in records if r.get("type")=="habit" ]
    tasks = [ (r.get("timestamp",""), (r.get("text") or "").strip()) for r in records if r.get("type")=="task" ]
    journals = [ (r.get("timestamp",""), (r.get("text") or "").strip()) for r in records if r.get("type")=="journal" ]

    mood_counts = Counter([m for _,m in moods if m])
    habit_counts = Counter([h for _,h in habits if h])
    # recent items
    recent_journals = journals[-7:]
    recent_tasks = tasks[-7:]
    recent_habits = habits[-5:]

    counts = {
        "journal": len(journals),
        "mood": len(moods),
        "habit": len(habits),
        "task": len(tasks),
    }

    bullets = []
    if mood_counts:
        top = ", ".join(f"{m} ({c})" for m,c in mood_counts.most_common(3))
        bullets.append("Top moods: " + top)
    if habit_counts:
        top = "; ".join(h for h,_ in habit_counts.most_common(3))
        bullets.append("Common habits: " + top)
    if recent_tasks:
        bullets.append(f"Open tasks captured this week: {len(recent_tasks)}")

    return counts, mood_counts, habit_counts, recent_journals, recent_tasks, recent_habits, bullets

def write_report(days, counts, mood_counts, habit_counts, journals, tasks, habits, bullets):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d")
    path = OUTDIR / f"insights-{ts}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# AK Weekly Insights (last {days} days)\n\n")
        f.write("## Totals\n")
        for k in sorted(counts):
            f.write(f"- {k}: {counts[k]}\n")

        f.write("\n## Top moods\n")
        if mood_counts:
            f.write(", ".join(f"{m} ({c})" for m,c in mood_counts.most_common(8)) + "\n")
        else:
            f.write("(none)\n")

        f.write("\n## Common habits\n")
        if habit_counts:
            f.write("; ".join(h for h,_ in habit_counts.most_common(8)) + "\n")
        else:
            f.write("(none)\n")

        f.write("\n## Recent journal snapshots\n")
        if journals:
            for tsn, snippet in journals:
                f.write(f"- {tsn} — {snippet[:140].replace('\n',' ')}\n")
        else:
            f.write("(none)\n")

        f.write("\n## Recent tasks\n")
        if tasks:
            for tsn, t in tasks:
                f.write(f"- {tsn} — {t}\n")
        else:
            f.write("(none)\n")

        f.write("\n## Summary\n")
        if bullets:
            for b in bullets:
                f.write(f"- {b}\n")
        else:
            f.write("- Not enough data yet. Journal daily to build signal.\n")
    return str(path)
days, counts, top_terms, journals, bullets):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d")
    path = OUTDIR / f"insights-{ts}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# AK Weekly Insights (last {days} days)\n\n")
        f.write("## Totals\n")
        for k in sorted(counts):
            f.write(f"- {k}: {counts[k]}\n")
        f.write("\n## Frequent terms\n")
        if top_terms:
            f.write(", ".join([f"{w} ({c})" for w,c in top_terms]) + "\n")
        else:
            f.write("(none)\n")
        f.write("\n## Recent journal snapshots\n")
        if journals:
            for ts, snippet in journals:
                f.write(f"- {ts} — {snippet}\n")
        else:
            f.write("(none)\n")
        f.write("\n## Summary\n")
        if bullets:
            for b in bullets:
                f.write(f"- {b}\n")
        else:
            f.write("- Not enough data yet. Journal daily to build signal.\n")
    return str(path)

def main():
    days = 7
    recs = load_last_days(days)
    print(f"Loaded {len(recs)} memories from last {days} days.")
    counts, top_terms, journals, bullets = summarize(recs)
    report = write_report(days, counts, top_terms, journals, bullets)
    print("Report written:", report)

if __name__ == "__main__":
    main()
