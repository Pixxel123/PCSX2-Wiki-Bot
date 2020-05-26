import requests
from bs4 import BeautifulSoup as bs
import re
from collections import namedtuple
from pytablewriter import MarkdownTableWriter
import io

wiki_url = 'https://wiki.pcsx2.net'

# Game has only NTSC-J info
game_search = 'Stepping Selection'
# Game has all 3 regions info
# game_search = 'Ratchet Clank'
# game_search = 'Jak II'
# game_search = 'God of War'

summon_phrase = 'WikiBot! '


def get_game_info(game_search):
    session = requests.Session()
    params = {'search': game_search,
              'title': 'Special:Search',
              'go': 'Go'
              }
    res = session.get(url=wiki_url, params=params)
    # When on search page, h1 is "Search results":
    # <h1 id="firstHeading" class="firstHeading" lang="en">Search results</h1>
    game_page = requests.get(res.url)
    html = bs(game_page.content, 'lxml')
    # When on game page, h1 firstHeading is NOT Search results
    game_title = html.find('h1', {'id': 'firstHeading'}).text
    Game = namedtuple('Game', [
        'title',
        'page_url',
        'page_html',
    ])
    game = Game(game_title, game_page.url, html)
    return game


def parse_search(search_page):
    html = search_page
    found_games = []
    search_results = html.find('ul', class_='mw-search-results')
    for result in search_results.find_all('a', href=True):
        game_name = result.string
        game_link = f"{wiki_url}{result.get('href')}"
        found_games.append({'name': game_name, 'link': game_link})
    return found_games


def find_compatibility(game_lookup):
    html = get_game_info(game_search).page_html
    compatibility_table = []
    regions = html.find_all('th', string=re.compile(r'^(Region).*:$'))
    for region in regions:
        # Finds region and strips out 'Region' and ':', returning region code via regex group 2
        game_region = re.sub(r'(Region\s)(.*)(:)', r'\2', region.text)
        compatibility = {'region': game_region}
        compatibility_info = []
        table = region.findParent('tbody')
        os_string = table.find_all('td', string=re.compile(r'^.*(Status):'))
        for system in os_string:
            os_string = system.text.replace(' Status:', '')
            try:
                game_state = system.find_next('td').find('b').text
            except AttributeError:
                # If no text, shows '?' from page
                # game_state = system.find_next('td').string
                # N/A is clearer than a question mark
                game_state = 'N/A'
            compatibility_info.append({'os': os_string, 'state': game_state})
        compatibility['stats'] = compatibility_info
        compatibility_table.append(compatibility)
    return compatibility_table


def find_issues(game_page):
    html = get_game_info(game_search).page_html
    active_issues = []
    fixed_issues = []
    try:
        issues = html.find('span', {'id': 'Known_Issues'}).parent
        for element in issues.next_siblings:
            # Deals with BS4 finding newline as next_sibling
            if element.name == 'ul':
                try:
                    if element.contents[0].text == 'Status: Fixed':
                        # If issue is fixed, find issue text
                        fixed_issue = element.previous_sibling.previous_sibling.text
                        fixed_issues.append(fixed_issue)
                    elif element.contents[0].text == 'Status: Active':
                        active_issue = element.previous_sibling.previous_sibling.text
                        active_issues.append(active_issue)
                except AttributeError:
                    pass
    # Some pages may not have a Known Issues section
    except AttributeError:
        no_issues_found = 'No issues found'
        active_issues.append(no_issues_found)
        fixed_issues.append(no_issues_found)
    Game_Issues = namedtuple('Issues', [
        'active',
        'fixed',
    ])
    game_issues = Game_Issues(active_issues, fixed_issues)
    return game_issues


def generate_table(game_page):
    compatibility = find_compatibility(game_page)
    writer = MarkdownTableWriter()
    table_data = []
    for i in compatibility:
        table_row = []
        # bold region index with markdown
        table_row.append(f"**{i['region']}**")
        # Gets each playable state per OS
        for j in i['stats']:
            table_row.append(j['state'])
        table_data.append(table_row)
    # Uses first table value to make OS headers
    table_header = [i['os'] for i in compatibility[0]['stats']]
    # Blank space added to header to allow "index" column
    table_header.insert(0, '')
    writer.headers = table_header
    writer.value_matrix = table_data
    # Output stream changed to variable instead of default stdout
    writer.stream = io.StringIO()
    writer.write_table()
    return writer.stream.getvalue()


def bot_message(game_lookup):
    game = get_game_info(game_lookup)
    html = game.page_html
    """
    # TODO: Handle multiple search results
    # (fuzzy match with first 3 results, show first in bot main message, then links to other two at the bottom?)
    """
    if game.title == 'Search results':
        parse_search(html)
    else:
        try:
            reply_table = '### Compatibility table\n\n'
            reply_table += str(generate_table(html))
        except AttributeError:
            reply_table = 'No compatibility information found'
        try:
            issues = find_issues(html)
            # If active issues is not empty
            if len(issues[0]) != 0:
                issue_message = '\n\n**Active issues:**\n\n'
                for issue in issues.active:
                    issue_message += f"* {issue}\n"
        except AttributeError:
            print('No issue information found')
        else:
            # If fixed issues is not empty
            if len(issues[1]) != 0:
                issue_message += '\n\n**Fixed issues:**\n\n'
                for issue in issues.fixed:
                    issue_message += f"* {issue}\n"
        bot_reply = f"## [{game.title}]({game.page_url})\n\n{reply_table}{issue_message}"
        return bot_reply


bot_message(game_search)
