import requests
from bs4 import BeautifulSoup as bs
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
from collections import namedtuple
from pytablewriter import MarkdownTableWriter
import io
import logging
import logging.config

# Logging allows replacing print statements to show more information
# This config outputs human-readable time, the log level, the log message and the line number this originated from
logging.basicConfig(
    format='%(asctime)s (%(levelname)s) %(message)s (Line %(lineno)d)', level=logging.DEBUG)

# PRAW seems to have its own logging which clutters up console output, so this disables everything but Python's logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True
})


wiki_url = 'https://wiki.pcsx2.net'
github_link = 'https://github.com/Pixxel123/PCSX2-Wiki-Bot'


summon_phrase = 'WikiBot! '


def get_game_info(game_search):
    session = requests.Session()
    params = {'search': game_search,
              'title': 'Special:Search',
              'go': 'Go'
              }
    res = session.get(url=wiki_url, params=params)
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


def parse_search_page(search_page):
    html = search_page
    found_games = []
    # Find games by "page title matches" section of page
    search_results = html.find('ul', class_='mw-search-results')
    for result in search_results.find_all('a', href=True):
        # Since search results can be finnicky, use the wiki's official game names for results
        game_name = result.string
        game_link = f"{wiki_url}{result.get('href')}"
        found_games.append({'name': game_name, 'link': game_link})
    return found_games


def find_compatibility(game_page):
    html = game_page
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
    html = game_page
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
        pass
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


def display_game_info(game_lookup):
    game = get_game_info(game_lookup)
    html = game.page_html
    try:
        reply_table = '### Compatibility table\n\n'
        reply_table += str(generate_table(html))
    except AttributeError:
        reply_table = 'No compatibility information found'
    issues = find_issues(html)
    issue_message = ''
    # If active issues is not empty
    if issues.active:
        issue_message += '\n\n**Active issues:**\n\n'
        for issue in issues.active:
            issue_message += f"* {issue}\n"
    # If fixed issues is not empty
    if issues.fixed:
        issue_message += '\n\n**Fixed issues:**\n\n'
        for issue in issues.fixed:
            issue_message += f"* {issue}\n"
    if not issues.active and not issues.fixed:
        issue_message = '\n\nNo active or fixed issues found.'
    bot_reply_info = f"## [{game.title}]({game.page_url})\n\n{reply_table}{issue_message}"
    return bot_reply_info


def bot_message(game_lookup):
    try:
        game = get_game_info(game_lookup)
        html = game.page_html
        if game.title == 'Search results':
            # Choices for fuzzy matching search results
            choices = []
            results = parse_search_page(html)
            for result in results:
                search_choice = result['name']
                # Handle user inputs with fuzzy matching
                # ! token_set_ratio ignores word order and duplicated words
                match_criteria = fuzz.token_set_ratio(
                    game_lookup.lower(), search_choice.lower())
                if match_criteria >= 50:
                    choices.append({'game_name': search_choice})
            try:
                closest_match = process.extractOne(
                    game_lookup, choices, scorer=fuzz.token_set_ratio, score_cutoff=95)
                game_search = closest_match[0]['game_name']
                bot_reply = display_game_info(game_search)
            except TypeError:
                # Limits results so that users are not overwhelmed with links
                limit_results = results[:5]
                bot_reply = f"No direct match found for **{game_lookup}**, displaying {len(limit_results)} wiki results:\n\n"
                search_results = ''
                for result in limit_results:
                    search_results += f"[{result['name']}]({result['link']})\n\n"
                bot_reply += search_results
                bot_reply += "Feel free to ask me again (`WikiBot! game name`) with these game names or visit the wiki directly!"
            # Pass allows footer to be appended
            pass
        else:
            # If game string does not trigger search page, show info directly
            bot_reply = display_game_info(game_lookup)
    # Handles no results being found in search
    except AttributeError:
        bot_reply = f"I'm sorry, I couldn't find any information on **{game_lookup}**.\n\nPlease feel free to try again; perhaps you had a spelling mistake, or your game does not exist in the [PCSX2 Wiki]({wiki_url})."
    # Append footer to bot message
    bot_reply += f"\n---\n^(I'm a bot, and should only be used for reference. All of my information comes from the contributors at the) [^PCSX2 ^Wiki]({wiki_url})^. ^(If there are any issues, please contact my) ^[Creator](https://www.reddit.com/message/compose/?to=theoriginal123123&subject=/u/PCSX2-Wiki-Bot)\n\n[^GitHub]({github_link})"
    return bot_reply


def run_bot():
    logging.info('Bot started!')
    game_search = 'fasfasfda'
    print(bot_message(game_search))


run_bot()
