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

def fetch_closed_issues():
    """Fetch all closed issues from the repository"""
    url = f'https://api.github.com/repos/{REPO}/issues'
    params = {
        'state': 'closed',
        'per_page': 100,
        'sort': 'created',
        'direction': 'desc'
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def format_date(date_str):
    """Format ISO date to 'Dec 1, 2025'"""
    date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
    return date.strftime('%b %d, %Y')

def format_body(body):
    """Format issue body as blockquote"""
    if not body or body.strip() == '':
        return '> Leave your message here!'
    
    # Split by lines and add > prefix
    lines = body.strip().split('\n')
    formatted_lines = []
    
    for line in lines:
        if line.strip():
            formatted_lines.append(f'> {line}')
        else:
            formatted_lines.append('> ')
    
    return '\n'.join(formatted_lines)

def generate_guestbook_table(issues):
    """Generate the guestbook table HTML"""
    # Show ALL entries (not just 6)
    table_rows = []
    
    for idx, issue in enumerate(issues, 1):
        username = issue['user']['login']
        created_at = format_date(issue['created_at'])
        body = format_body(issue['body'])
        issue_number = issue['number']
        
        row = f'''<tr>
<td width="80px" align="center"><strong>#{issue_number}</strong></td>
<td>

**[{username}](https://github.com/{username})** • *{created_at}*

{body}

</td>
</tr>'''
        
        table_rows.append(row)
    
    # Join rows with separators
    separator = '<tr><td colspan="2"><hr></td></tr>'
    table_content = f'\n{separator}\n'.join(table_rows)
    
    return f'''<table>
{table_content}
</table>'''

def update_readme(guestbook_content):
    """Update README.md with new guestbook content"""
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace content between markers
    pattern = r'<!-- GUESTBOOK:START -->.*?<!-- GUESTBOOK:END -->'
    replacement = f'<!-- GUESTBOOK:START -->\n{guestbook_content}\n<!-- GUESTBOOK:END -->'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Guestbook updated successfully!")

def main():
    print("Fetching closed issues...")
    issues = fetch_closed_issues()
    
    if not issues:
        print("No closed issues found")
        return
    
    print(f"Found {len(issues)} closed issues")
    print("Generating guestbook table...")
    
    guestbook_content = generate_guestbook_table(issues)
    
    print("Updating README.md...")
    update_readme(guestbook_content)

if __name__ == '__main__':
    main()
