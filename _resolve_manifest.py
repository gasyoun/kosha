"""Resolve datasets.json v2: master's side wholesale + the PR's les-1990 row lines verbatim."""
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

p = "data/manifest/datasets.json"
lines = io.open(p, encoding="utf-8").read().splitlines()

i_start = next(i for i, l in enumerate(lines) if l.startswith("<<<<<<<"))
i_mid = next(i for i, l in enumerate(lines) if l.strip() == "=======")
i_end = next(i for i, l in enumerate(lines) if l.startswith(">>>>>>>"))

master_side = lines[i_mid + 1 : i_end]
pr_side = lines[i_start + 1 : i_mid]

row_start = next(i for i, l in enumerate(pr_side) if '"id": "les-1990-static-dump"' in l)
obj_open = max(i for i in range(row_start) if pr_side[i].strip() == "{")
obj_close = max(i for i in range(row_start, len(pr_side)) if pr_side[i].strip() == "}")
row_lines = pr_side[obj_open : obj_close + 1]
json.loads("\n".join(row_lines))  # the row itself must parse
print("row ok:", row_lines[1].strip()[:60])

close_idx = max(i for i, l in enumerate(master_side) if l.strip() == "]")
prev = close_idx - 1
while master_side[prev].strip() == "":
    prev -= 1
assert master_side[prev].strip() == "}", f"unexpected tail: {master_side[prev]!r}"

master_side = master_side[:prev] + [master_side[prev] + ","] + row_lines + master_side[close_idx:]

doc = "\n".join(lines[:i_start] + master_side + lines[i_end + 1 :]) + "\n"
obj = json.loads(doc)
rows = obj.get("datasets", [])
print("valid JSON; datasets:", len(rows), "; les-1990 present:",
      any(r.get("id") == "les-1990-static-dump" for r in rows))

io.open(p, "w", encoding="utf-8", newline="").write(doc)
print("written")
