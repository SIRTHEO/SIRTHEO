#!/usr/bin/env python3
"""Refresh the "ship's log" line in README.md with the latest commit on sailor.

Runs nightly from .github/workflows/refresh.yml. Replaces the text between the
log markers and nothing else.
"""
import json
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path

REPO = "SIRTHEO/sailor"
README = Path(__file__).resolve().parent.parent / "README.md"

req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/commits?per_page=1",
                             headers={"User-Agent": "profile-readme", "Accept": "application/vnd.github+json"})
if os.environ.get("GITHUB_TOKEN"):
    req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
commit = json.loads(urllib.request.urlopen(req, timeout=30).read())[0]
subject = commit["commit"]["message"].splitlines()[0].strip()
when = datetime.fromisoformat(commit["commit"]["committer"]["date"].replace("Z", "+00:00")).strftime("%b %-d, %Y")
url = commit["html_url"]

line = f'> **Latest log entry** · {when} · [{subject}]({url})'
text = README.read_text(encoding="utf-8")
new = re.sub(r"(<!-- log:start -->\n).*?(\n<!-- log:end -->)", lambda m: m.group(1) + line + m.group(2), text, flags=re.S)
if new != text:
    README.write_text(new, encoding="utf-8")
    print("log updated:", line)
else:
    print("log unchanged")
