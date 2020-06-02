from wikibot import Wikibot

# summon_phrase = {'wiki': 'Wikibot! ', 'cpu': 'CPUBot! '}

# body = 'cpubot! This is a thing'

# if summon_phrase['wiki'].lower() in body.lower():
#     print('Wiki mode')
# if summon_phrase['cpu'].lower() in body.lower():
#     print('CPU mode!')
# wikibot = Wikibot()
# reddit = wikibot.get_games_list()


if __name__ == '__main__':
    wikibot = Wikibot()
    print('Ready!')
    while True:
        print(wikibot.bot_message(''))
