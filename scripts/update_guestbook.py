#!/usr/bin/env python3
"""
update_guestbook.py
Rebuilds the README guestbook section based on closed GitHub issues.
"""

import os
import sys
import requests

REPO = os.getenv("GH_REPO")
TOKEN = os.getenv("GH_TOKEN")

API_URL = f"https://api.github.com/repos/{REPO}/issues"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

README_PATH = "README.md"
START_MARK = "<!-- GUESTBOOK:START -->"
END_MARK = "<!-- GUESTBOOK:END -->"


def fetch_closed_issues():
    """Return all closed non-PR issues sorted oldest → newest."""
    issues = []
    page = 1

    while True:
        params = {"state": "closed", "per_page": 100, "page": page}
        r = requests.get(API_URL, headers=HEADERS, params=params)

        if r.status_code != 200:
            print(f"GitHub API error: {r.status_code}")
            sys.exit(1)

        data = r.json()
        if not data:
            break

        # Filter out PRs
        for issue in data:
            if "pull_request" not in issue:
                issues.append(issue)

        page += 1

    # Sort chronologically (oldest entries at top)
    issues.sort(key=lambda x: x["number"])
    return issues


def build_guestbook(issues):
    """Return plain text guestbook content."""
    lines = []

    for issue in issues:
        number = issue["number"]
        author = issue["user"]["login"]
        body = issue.get("body") or ""
        body = body.strip()

        entry = f"### Entry #{number} — {author}\n\n{body}\n\n---\n"
        lines.append(entry)

    return "\n".join(lines).rstrip()


def load_readme():
    if not os.path.exists(README_PATH):
        print("Error: README.md not found.")
        sys.exit(1)

    with open(README_PATH, "r", encoding="utf-8") as f:
        return f.read()


def save_readme(content):
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def update_readme(guestbook):
    readme = load_readme()

    if START_MARK not in readme or END_MARK not in readme:
        print("Error: Guestbook markers not found in README.md.")
        sys.exit(1)

    before = readme.split(START_MARK)[0]
    after = readme.split(END_MARK)[1]

    new_section = f"{START_MARK}\n{guestbook}\n{END_MARK}"
    updated = before + new_section + after

    save_readme(updated)
    print("Guestbook updated.")


def main():
    issues = fetch_closed_issues()
    guestbook = build_guestbook(issues)
    update_readme(guestbook)


if __name__ == "__main__":
    main()
