import os
import re
import requests
from datetime import datetime

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
REPO = os.environ['REPO']
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def fetch_all_closed_issues():
    all_issues = []
    page = 1

    while True:
        url = f'https://api.github.com/repos/{REPO}/issues'
        params = {
            'state': 'closed',
            'per_page': 100,
            'page': page,
            'sort': 'created',
            'direction': 'desc'
        }

        try:
            response = requests.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
            issues = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break

        if not issues:
            break

        issues = [i for i in issues if 'pull_request' not in i]
        all_issues.extend(issues)

        if len(issues) < 100:
            break
        page += 1

    return all_issues

def format_date(date_str):
    try:
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
        return date.strftime('%b %d, %Y')
    except ValueError:
        return date_str

def format_body(body):
    if not body or body.strip() == '':
        return '> (no message)'

    lines = body.strip().split('\n')
    return '\n'.join(f'> {line}' if line else '> ' for line in lines)

def generate_stats_section(issues):
    total = len(issues)
    if not issues:
        return "**Total Signatures:** 0\n\n---\n\n"

    latest = issues[0]
    username = f"@{latest['user']['login']}" if latest.get('user') else "@[deleted]"
    created_at = format_date(latest['created_at'])

    return f"""**Total Signatures:** {total} • **Latest:** {username} on {created_at}

---

"""

def generate_guestbook_table(issues):
    rows = []

    for idx, issue in enumerate(issues, 1):
        username = issue['user']['login'] if issue.get('user') else '[deleted]'
        user_url = f"https://github.com/{username}" if issue.get('user') else "#"
        created_at = format_date(issue['created_at'])
        body = format_body(issue.get('body', ''))
        issue_number = issue['number']

        row = f"""<tr>
<td width="80px" align="center"><strong>#{idx}</strong><br><sub>Issue #{issue_number}</sub></td>
<td>
<strong><a href="{user_url}">@{username}</a></strong> • <em>{created_at}</em>

{body}
</td>
</tr>"""

        rows.append(row)

    separator = '<tr><td colspan="2"><hr></td></tr>'
    content = f"\n{separator}\n".join(rows)

    return f"<table>\n{content}\n</table>"

def update_readme(content):
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme = f.read()
    except FileNotFoundError:
        print("README.md not found.")
        return

    pattern = r'<!-- GUESTBOOK:START -->.*?<!-- GUESTBOOK:END -->'
    replacement = f"<!-- GUESTBOOK:START -->\n{content}\n<!-- GUESTBOOK:END -->"
    updated = re.sub(pattern, replacement, readme, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated)

    print("Guestbook updated.")

def main():
    issues = fetch_all_closed_issues()
    print(f"Found {len(issues)} closed issues")

    stats = generate_stats_section(issues)
    table = generate_guestbook_table(issues)
    full_content = stats + table

    update_readme(full_content)

if __name__ == "__main__":
    main()
