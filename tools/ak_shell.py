import os, json, sys, shlex, subprocess

BASE = os.path.expanduser("~/ak")
ALLOW_FILE = os.path.join(BASE, "allowed_cmds.json")

def load_allow():
    if not os.path.exists(ALLOW_FILE):
        return {"whitelist": ["ls","cat","echo","python3 --version"], "blocked": []}
    with open(ALLOW_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def is_allowed(cmd: str, allow) -> bool:
    # allow if command starts with any whitelist entry as a prefix
    for w in allow.get("whitelist", []):
        if cmd.strip().startswith(w):
            return True
    return False

def is_blocked(cmd: str, allow) -> bool:
    for b in allow.get("blocked", []):
        if b and b in cmd:
            return True
    return False

def run_cmd(cmd: str):
    # run in ~/ak only, short timeout
    p = subprocess.run(cmd, shell=True, cwd=BASE,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=15, text=True)
    return p.returncode, p.stdout.strip()

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/ak_shell.py \"<command>\""); return
    cmd = sys.argv[1]
    allow = load_allow()
    if is_blocked(cmd, allow):
        print("Blocked by policy."); return
    if not is_allowed(cmd, allow):
        print("Not allowed. Edit allowed_cmds.json to whitelist this command."); return
    code, out = run_cmd(cmd)
    print(out if out else f"(exit {code})")

if __name__ == "__main__":
    main()
