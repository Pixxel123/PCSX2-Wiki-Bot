# PCSX2-Wiki-Bot

A Reddit bot that grabs game information from the PCSX2 wiki for users to get a quick view of any fixed or ongoing issues.

Similar to my [PCSX2-CPU-Bot](https://github.com/Pixxel123/PCSX2-CPU-Bot), this bot aims to help users of the PCSX2 subreddit to find information on the issues they may be facing when emulating games with PCSX2.

As the [PCSX2 Wiki](https://wiki.pcsx2.net/Main_Page) is the one place that users and testers report issues, subreddit contributors were constantly asking if users had checked the wiki, so this bot aims to both present the main information in an easily digestible format while linking back to the original wiki source for more detail.

## How it works

The bot is summoned with the command `WikiBot! <game name>`. The game name parameter is compared against a hashmap of all game names from the wiki and their respective page links.

Fuzzy matching is done with the [fuzzywuzzy module](https://github.com/seatgeek/fuzzywuzzy), but relies on closeness to the official game names. For instance, if a user searches for `Ratchet and Clank 2`, the bot will not find the matching `Ratchet & Clank: Going Commando` title, but searching for `GTA San Andreas` should match `Grand Theft Auto: San Andreas`.

To search for games, the bot creates a hashmap/dictionary on startup with game titles and the links to their respective pages. Matches are made between the user's input and the game name, which then pulls the corresponding game wiki link.

Once at the desired page, the bot uses [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) to scrape the following:

- The compatibility of each game region against the Windows, Mac and Linux operating systems. This is then made into a markdown table for easy viewing on Reddit.

- Any issues designated as Active or Fixed, along with their descriptions. These are placed under their respective headers. (There are other issues, such as `Note (not an issue)` but these are ignored as they have no real relevance for most end-users).

These details are then passed into a Reddit comment.

![Successful game reply](https://i.imgur.com/VlxxnhY.png)

## Why didn't the bot respond to me?

* Make sure that you are calling the bot correctly with `WikiBot! <game name>`

  The first part, `WikiBot!` **is NOT case-sensitive** and requires a space after the `!`.

* The bot currently does not support more than one game lookup at a time.

* The bot will only reply to a comment once. Edited comments after a reply is made will not be seen.

* The bot may be down for maintenance.

* I may have run out of free dynos for the month!

# Acknowledgements

1. https://github.com/kylelobo/Reddit-Bot - kylelobo
2. https://github.com/harshibar/friendly-redditbot - harshibar
3. The Reddit community, particularly [r/redditdev](https://old.reddit.com/r/redditdev/), [r/Python](https://old.reddit.com/r/python/), and of course, [r/PCSX2](https://old.reddit.com/r/pcsx2/)
