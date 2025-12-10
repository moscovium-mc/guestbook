import os
import re
import requests
from datetime import datetime

# Configuration
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
REPO = os.environ['REPO']
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def fetch_all_closed_issues():
    """Fetch all closed issues with pagination"""
    all_issues = []
    page = 1
    
    while True:
        url = f'https://api.github.com/repos/{REPO}/issues'
        params = {
            'state': 'closed',
            'per_page': 100,
            'page': page,
            'sort': 'created',
            'direction': 'desc'  # Newest first
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
        
        # Filter out pull requests
        issues = [issue for issue in issues if 'pull_request' not in issue]
        all_issues.extend(issues)
        
        print(f"Fetched page {page}: {len(issues)} issues")
        
        if len(issues) < 100:
            break
            
        page += 1
    
    return all_issues

def format_date(date_str):
    """Format ISO date to 'Dec 1, 2025'"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
        return date.strftime('%b %d, %Y')
    except ValueError:
        return date_str

def format_body(body):
    """Format issue body - preserves all markdown/formatting"""
    if not body or body.strip() == '':
        return '*no message*'
    
    # Return raw body - let GitHub's markdown renderer handle it
    return body.strip()

def generate_stats_section(issues):
    """Generate stats section"""
    total = len(issues)
    
    if not issues:
        return "**total signatures:** 0\n\n---\n\n"
    
    latest = issues[0]  # First in DESC list
    latest_user = f"@{latest['user']['login']}" if latest.get('user') else "@[deleted]"
    latest_date = format_date(latest['created_at'])
    
    return f"**total signatures:** {total} • **latest:** {latest_user} on {latest_date}\n\n---\n\n"

def generate_guestbook_table(issues):
    """Generate the guestbook table"""
    table_rows = []
    
    for idx, issue in enumerate(issues, start=1):
        # Handle deleted/suspended accounts
        if issue.get('user'):
            username = issue['user']['login']
            user_url = f"https://github.com/{username}"
        else:
            username = '[deleted]'
            user_url = "#"
        
        created_at = format_date(issue['created_at'])
        body = format_body(issue.get('body', ''))
        issue_number = issue['number']
        
        # Build row with proper markdown support
        row = f"""<tr>
<td width="80px" align="center"><strong>#{idx}</strong><br><sub>issue #{issue_number}</sub></td>
<td>

**[@{username}]({user_url})** • *{created_at}*

{body}

</td>
</tr>"""
        
        table_rows.append(row)
    
    separator = '<tr><td colspan="2"><hr></td></tr>'
    table_content = f'\n{separator}\n'.join(table_rows)
    
    return f"<table>\n{table_content}\n</table>"

def update_readme(guestbook_content):
    """Update README.md with new guestbook content"""
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: README.md not found")
        return
    
    pattern = r'<!-- GUESTBOOK:START -->.*?<!-- GUESTBOOK:END -->'
    replacement = f'<!-- GUESTBOOK:START -->\n{guestbook_content}\n<!-- GUESTBOOK:END -->'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Guestbook updated successfully!")

def main():
    print("Fetching all closed issues...")
    issues = fetch_all_closed_issues()
    
    if not issues:
        print("No closed issues found")
        return
    
    print(f"Found {len(issues)} total closed issues")
    print("Generating guestbook content...")
    
    stats_section = generate_stats_section(issues)
    guestbook_table = generate_guestbook_table(issues)
    guestbook_content = stats_section + guestbook_table
    
    print("Updating README.md...")
    update_readme(guestbook_content)

if __name__ == '__main__':
    main()
