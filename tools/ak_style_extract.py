#!/usr/bin/env python3
import os, glob, json, re
from pathlib import Path

BASE = Path.home()/ "ak"
SAMPLES = BASE/ "data/identity/style_samples"
OUT = BASE/ "data/identity/style_profile.json"

def lines(p):
    try:
        return [l.strip() for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]
    except:
        return []

def main():
    texts=[]
    for p in glob.glob(str(SAMPLES/"*.md")):
        texts += lines(p)
    # crude feature extraction
    avg_len = sum(len(t) for t in texts)/max(1,len(texts))
    bullets = sum(1 for t in texts if t.startswith(("-", "*")))
    imper = sum(1 for t in texts if re.match(r"^(do|pick|choose|ship|use|avoid|stop|start|recommend)\b", t.lower()))
    profile = {
        "avg_line_len": round(avg_len,1),
        "prefers_bullets": bullets > len(texts)*0.2,
        "imperative_ratio": round(imper/max(1,len(texts)),2),
        "signature": [
            "Lead with options + recommendation.",
            "Convert asks into checklists.",
            "Name trade-offs plainly.",
            "Skip filler; keep lines short."
        ]
    }
    OUT.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print("Wrote", OUT)

if __name__ == "__main__":
    main()
