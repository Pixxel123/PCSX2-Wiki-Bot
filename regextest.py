import re

summon_phrase = 'Wikibot! '

game_lookup = 'Wikibot! Game 1| Game 2|Game 3'

game_search = re.search(
    f"({summon_phrase})([^!,?\n\r]*)", game_lookup, re.IGNORECASE)

if game_search:
    game_search = game_search.group(2)
    game_search = [item.strip() for item in game_search.split('|')]

print(game_search)
