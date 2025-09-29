import csv, os, time, json, sys
LOG = os.path.expanduser("~/ak/logs/ak_eval.csv")
os.makedirs(os.path.dirname(LOG), exist_ok=True)

def log(row):
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ts","question","answer","sources","good"])
        if new: w.writeheader()
        w.writerow(row)

if __name__ == "__main__":
    # usage: python tools/ak_log.py "<q>" "<a>" "<sources>" "<good>"
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    q, a, s, g = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    log({"ts":ts,"question":q,"answer":a,"sources":s,"good":g})
    print("logged")
