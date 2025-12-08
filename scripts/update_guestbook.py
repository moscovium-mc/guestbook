import os
import re
import requests
from datetime import datetime

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["REPO"]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

def fetch_all_closed_issues():
    issues = []
    page = 1

    while True:
        url = f"https://api.github.com/repos/{REPO}/issues"
        params = {
            "state": "closed",
            "per_page": 100,
            "page": page,
            "sort": "created",
            "direction": "asc",
        }

        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        data = r.json()

        # remove PRs
        data = [i for i in data if "pull_request" not in i]

        if not data:
            break

        issues.extend(data)
        page += 1

    return issues


def format_date(dt):
    return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ").strftime("%b %d, %Y")


def format_body(text):
    if not text or not text.strip():
        return "> (no message)"

    return "\n".join(f"> {line}" if line.strip() else "> " for line in text.split("\n"))


def build_stats(issues):
    total = len(issues)
    if total == 0:
        return "**Total Signatures:** 0\n\n---\n\n"

    latest = issues[-1]
    user = latest.get("user", {}).get("login", "[deleted]")
    date = format_date(latest["created_at"])

    return f"**Total Signatures:** {total} • **Latest:** @{user} on {date}\n\n---\n\n"


def build_table(issues):
    rows = []

    for i, issue in enumerate(issues, start=1):
        user = issue.get("user", {}).get("login", "[deleted]")
        url = f"https://github.com/{user}" if user != "[deleted]" else "#"
        date = format_date(issue["created_at"])
        body = format_body(issue.get("body", ""))
        num = issue["number"]

        rows.append(
            f"""
<tr>
  <td width="80px" align="center"><strong>#{i}</strong><br><sub>Issue #{num}</sub></td>
  <td>
    <strong><a href="{url}">@{user}</a></strong> • <em>{date}</em><br>
    {body}
  </td>
</tr>
"""
        )

    sep = "<tr><td colspan='2'><hr></td></tr>"

    return "<table>\n" + f"{sep}\n".join(rows) + "\n</table>"


def update_readme(content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    pattern = r"<!--START_GUESTBOOK-->(.*?)<!--END_GUESTBOOK-->"
    replacement = f"<!--START_GUESTBOOK-->\n{content}\n<!--END_GUESTBOOK-->"

    new_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)


def main():
    print("Fetching closed issues...")
    issues = fetch_all_closed_issues()
    print(f"Found {len(issues)} entries")

    stats = build_stats(issues)
    table = build_table(issues)

    full = stats + table

    print("Updating README...")
    update_readme(full)
    print("Guestbook updated!")


if __name__ == "__main__":
    main()
