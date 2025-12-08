import os
import re
import requests
from datetime import datetime

# Environment variables are passed from the GitHub workflow
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["REPO"] # Format: owner/repo

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

def fetch_all_closed_issues():
    """Fetches all closed, non-PR issues that are considered guestbook entries."""
    issues = []
    page = 1

    while True:
        # API endpoint for repository issues
        url = f"https://api.github.com/repos/{REPO}/issues"
        params = {
            "state": "closed",
            "per_page": 100,
            "page": page,
            "sort": "created", # Sort by creation date
            "direction": "asc", # Oldest first
        }

        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        data = r.json()

        # Filter out Pull Requests, which are issues with a 'pull_request' key
        data = [i for i in data if "pull_request" not in i]

        if not data:
            break

        issues.extend(data)
        page += 1

    return issues

def format_date(dt):
    """Formats the GitHub timestamp string into a readable date."""
    return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ").strftime("%b %d, %Y")

def sanitize(text):
    """
    Sanitizes text for safe inclusion within an HTML table cell.
    Crucially, it uses <pre> to preserve all internal GitHub markdown/formatting.
    """
    if not text:
        return "(no message)"

    # Escape characters that could break the HTML structure
    safe_text = (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )
    
    # Wrap in <pre> tags to preserve all whitespace, line breaks, and formatting
    # while still allowing the escaped HTML to render safely inside the <td>.
    return f"<pre>{safe_text}</pre>"

def build_stats(issues):
    """Generates the guestbook statistics header."""
    total = len(issues)
    if total == 0:
        return "**Total Signatures:** 0\n\n---\n\n"

    latest = issues[-1] # Last issue in the ASC-sorted list
    user = latest.get("user", {}).get("login", "[deleted]")
    date = format_date(latest["created_at"])

    return f"**Total Signatures:** {total} • **Latest:** @{user} on {date}\n\n---\n\n"

def build_table(issues):
    """Generates the HTML table content for all guestbook entries."""
    rows = []

    for i, issue in enumerate(issues, start=1):
        user = issue.get("user", {}).get("login", "[deleted]")
        url = f"https://github.com/{user}" if user != "[deleted]" else "#"
        date = format_date(issue["created_at"])
        num = issue["number"]
        raw_body = issue.get("body", "")
        # The sanitization function handles (no message) and wrapping in <pre>
        body = sanitize(raw_body)

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

    # Separator to put between rows for a clean, visually appealing look
    sep = "<tr><td colspan='2'><hr></td></tr>"

    return "<table>\n" + f"{sep}\n".join(rows) + "\n</table>"

def update_readme(content):
    """Inserts the new guestbook content between the markers in README.md."""
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme = f.read()
    except FileNotFoundError:
        print("Error: README.md not found. Ensure it exists in the root directory.")
        return

    # Regular expression to find the start and end markers
    pattern = r"(.*?)"
    replacement = f"\n{content}\n"

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
