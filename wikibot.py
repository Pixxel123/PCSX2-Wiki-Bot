import requests
from bs4 import BeautifulSoup as bs
import re
from collections import namedtuple


wiki_url = 'https://wiki.pcsx2.net/index.php'

# Game has only NTSC-J info
game_search = 'Stepping Selection'
# Game has all 3 regions info
# game_search = 'Ratchet & Clank'
# game_search = 'God of War'

summon_phrase = 'WikiBot! '


def find_compatibility(game_page):
  html = game_page
  compatibility_table = []
  regions = html.find_all('th', string=re.compile(r'^(Region).*:$'))
  for region in regions:
    # Finds region and strips out 'Region' and ':', returning region only via regex group 2
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
    issues = html.find('span',{'id': 'Known_Issues'}).parent
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
  return active_issues, fixed_issues


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
  print(f"{game.title} || {game.page_url}")
  return game

game = get_game_info(game_search)
find_compatibility(game.page_html)
find_issues(game.page_html)

# TODO: Handle multiple search results (fuzzy match with first 3 results, show first in bot main message, then links to other two at the bottom?)

# Reddit table formatting
"""

| | **NTSC-U** | PAL | NTSC-J
|:-:|:-:|:-:|:-:|
| **Windows** |  Playable |  Playable | Playable
| **Mac**       | ? | ? | ?
| **Linux** | ? | ? | ?

"""
