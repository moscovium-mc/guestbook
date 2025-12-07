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
    """Fetch all closed issues with rate limit handling and error handling"""
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
            
            # Check rate limits
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            if remaining < 10:
                print(f"Warning: Only {remaining} API calls remaining")
            
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
        
        # Check if there are more pages
        if len(issues) < 100:
            break
            
        page += 1
    
    # Sort by creation date ascending (oldest first) to match sequential number (newest at the bottom)
    # The default GitHub API sort is 'desc', but we want the list to show entry #1 as the oldest.
    all_issues.sort(key=lambda x: datetime.strptime(x['created_at'], '%Y-%m-%dT%H:%M:%SZ'), reverse=False)
    
    return all_issues

# Removed: filter_spam_issues function

def format_date(date_str):
    """Format ISO date to 'Dec 1, 2025'"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
        return date.strftime('%b %d, %Y')
    except ValueError:
        return date_str

def format_body(body):
    """Format issue body as blockquote"""
    if not body or body.strip() == '':
        return '> Leave your message here!'
    
    lines = body.strip().split('\n')
    formatted_lines = []
    
    for line in lines:
        if line.strip():
            formatted_lines.append(f'> {line}')
        else:
            formatted_lines.append('> ')
    
    return '\n'.join(formatted_lines)

def generate_stats_section(issues):
    """Generate stats section"""
    total = len(issues)
    
    if not issues:
        return "**Total Signatures:** 0\n\n---\n\n"
    
    # Latest is the last entry in the list, which is the newest since we sorted by ascending date
    latest = issues[-1] 
    latest_user = f"@{latest['user']['login']}" if latest.get('user') else "@[deleted]"
    latest_date = format_date(latest['created_at'])
    
    return f'''**Total Signatures:** {total} • **Latest:** {latest_user} on {latest_date}

---

'''

def generate_guestbook_table(issues):
    """Generate the guestbook table HTML with sequential numbering"""
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
        
        row = f'''<tr>
<td width="80px" align="center"><strong>#{idx}</strong><br><sub>Issue #{issue_number}</sub></td>
<td>

<strong><a href="{user_url}">@{username}</a></strong> • <em>{created_at}</em>

{body}
</td>
</tr>'''
        
        table_rows.append(row)
    
    separator = '<tr><td colspan="2"><hr></td></tr>'
    table_content = f'\n{separator}\n'.join(table_rows)
    
    return f'''<table>
{table_content}
</table>'''

def update_readme(guestbook_content):
    """Update README.md with new guestbook content"""
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: README.md not found")
        return
    
    pattern = r'.*?'
    replacement = f'\n{guestbook_content}\n'
    
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
    
    # Note: Spam filtering is removed, all closed issues are accepted.
    filtered_issues = issues 
    
    print(f"Generating guestbook content for {len(filtered_issues)} entries...")
    
    stats_section = generate_stats_section(filtered_issues)
    guestbook_table = generate_guestbook_table(filtered_issues)
    guestbook_content = stats_section + guestbook_table
    
    print("Updating README.md...")
    update_readme(guestbook_content)

if __name__ == '__main__':
    main()
