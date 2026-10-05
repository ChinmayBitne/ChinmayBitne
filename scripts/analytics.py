"""Generate repository-hosted SVG cards from public GitHub repository metadata."""
import json
import os
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

OWNER = 'ChinmayBitne'
OUTPUT = Path(__file__).resolve().parents[1] / 'assets' / 'analytics'

def fetch_repositories():
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-analytics', 'X-GitHub-Api-Version': '2022-11-28'}
    if os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    repositories = []
    for page in range(1, 101):
        request = Request(f'https://api.github.com/users/{OWNER}/repos?type=owner&per_page=100&page={page}', headers=headers)
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError('GitHub returned an invalid repository response')
        repositories.extend(repo for repo in batch if not repo.get('private', True) and repo['owner']['login'].lower() == OWNER.lower())
        if len(batch) < 100:
            return repositories
    raise ValueError('Repository pagination limit exceeded')

def summarize(repositories):
    originals = [repo for repo in repositories if not repo['fork']]
    return {
        'repositories': len(originals),
        'stars': sum(repo['stargazers_count'] for repo in originals),
        'forks': sum(repo['forks_count'] for repo in originals),
        'languages': Counter(repo['language'] for repo in originals if repo['language']),
    }

def frame(title, content, date):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="500" height="250" viewBox="0 0 500 250" role="img" aria-label="{escape(title, quote=True)}">
<rect x="1" y="1" width="498" height="248" rx="12" fill="#0d1117" stroke="#30363d"/>
<g font-family="Arial, sans-serif" fill="#e6edf3"><text x="24" y="36" font-size="19" font-weight="bold">{escape(title)}</text>
{content}
<text x="24" y="230" font-size="12" fill="#8b949e">Public, non-fork repositories · updated {escape(date)}</text></g></svg>\n'''

def render_cards(summary, date):
    rows = [('Repositories', summary['repositories']), ('Stars received', summary['stars']), ('Forks received', summary['forks'])]
    stats = ''.join(f'<text x="24" y="{80 + i * 48}" font-size="16">{label}</text><text x="450" y="{80 + i * 48}" text-anchor="end" font-size="24" fill="#a78bfa">{value}</text>' for i, (label, value) in enumerate(rows))
    languages = summary['languages'].most_common(5)
    total = sum(summary['languages'].values())
    language_rows = []
    for index, (language, count) in enumerate(languages):
        y = 65 + index * 29
        language_rows.append(f'<text x="24" y="{y}" font-size="14">{escape(language)}</text><rect x="195" y="{y - 11}" width="{round(count / total * 210, 1)}" height="12" rx="3" fill="#a78bfa"/><text x="456" y="{y}" text-anchor="end" font-size="13">{count}</text>')
    if not languages:
        language_rows.append('<text x="24" y="90" font-size="14">No primary-language data available</text>')
    language_rows.append('<text x="24" y="210" font-size="12" fill="#8b949e">Repository count by primary language</text>')
    return {'stats.svg': frame('GitHub repository overview', stats, date), 'languages.svg': frame('Languages across repositories', ''.join(language_rows), date)}

def main():
    # Complete all requests and rendering before replacing the last good snapshot.
    cards = render_cards(summarize(fetch_repositories()), datetime.now(timezone.utc).date().isoformat())
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, content in cards.items():
        temporary = OUTPUT / (name + '.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(OUTPUT / name)
    print('Generated two SVG cards from public GitHub repository metadata.')

if __name__ == '__main__':
    main()
