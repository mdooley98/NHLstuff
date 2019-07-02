import praw, config, re, requests, json, pyperclip
import pandas as pd
from datetime import datetime, timedelta

class HockeyTopPosts():

    def __init__(self):
        self.teams = {'Anaheim Ducks': ['ANA', '/r/anaheimducks'],
                      'Arizona Coyotes': ['ARI', '/r/coyotes'],
                      'Boston Bruins': ['BOS', '/r/bostonbruins'],
                      'Buffalo Sabres': ['BUF', '/r/sabres'],
                      'Calgary Flames': ['CGY', '/r/calgaryflames'],
                      'Carolina Hurricanes': ['CAR', '/r/canes'],
                      'Chicago Blackhawks': ['CHI', '/r/hawks'],
                      'Colorado Avalanche': ['COL', '/r/coloradoavalanche'],
                      'Columbus Blue Jackets': ['CBJ', '/r/bluejackets'],
                      'Dallas Stars': ['DAL', '/r/dallasstars'],
                      'Detroit Red Wings': ['DET', '/r/detroitredwings'],
                      'Edmonton Oilers': ['EDM', '/r/edmontonoilers'],
                      'Florida Panthers': ['FLA', '/r/floridapanthers'],
                      'Los Angeles Kings': ['LAK', '/r/losangeleskings'],
                      'Minnesota Wild': ['MIN', '/r/wildhockey'],
                      'Montreal Canadiens': ['MTL', '/r/habs'],
                      'Nashville Predators': ['NSH', '/r/predators'],
                      'New Jersey Devils': ['NJD', '/r/devils'],
                      'New York Islanders': ['NYI', '/r/newyorkislanders'],
                      'New York Rangers': ['NYR', '/r/rangers'],
                      'Ottawa Senators': ['OTT', '/r/ottawasenators'],
                      'Philadelphia Flyers': ['PHI', '/r/flyers'],
                      'Pittsburgh Penguins': ['PIT', '/r/penguins'],
                      'San Jose Sharks': ['SJS', '/r/sanjosesharks'],
                      'St. Louis Blues': ['STL', '/r/stlouisblues'],
                      'Tampa Bay Lightning': ['TBL', '/r/tampabaylightning'],
                      'Toronto Maple Leafs': ['TOR', '/r/leafs'],
                      'Vancouver Canucks': ['VAN', '/r/canucks'],
                      'Vegas Golden Knights': ['VGK', '/r/goldenknights'],
                      'Washington Capitals': ['WSH', '/r/caps'],
                      'Winnipeg Jets': ['WPG', '/r/winnipegjets'],
                      # EXTRA,
                      # 'Hockey': ['HKY', '/r/hockey'],
                      # 'St Louis Blues': ['STL', '/r/stlouisblues'],
                      # 'Montréal Canadiens': ['MTL', '/r/habs']
                      }
        self.r = praw.Reddit(client_id=config.reddit_id,
                             client_secret=config.reddit_secret,
                             username=config.reddit_user,
                             password=config.reddit_pass,
                             user_agent=config.reddit_agent)
        self.subreddit = 'hockey'
        self.headers = {
            "User-Agent": "phenomenon praw testing"
        }
        self.MAGICSTART = '###Top Team Subreddit Posts'
        self.MAGICEND = '\[Click here for all 31\]\(/r/hockey/wiki/topposts\)'
        self.MAGICSTARTNEW = '###Top Team Subreddit Posts'
        self.MAGICENDNEW = '[Click here for all 31](/r/hockey/wiki/topposts)'

    def top_posts(self):
        post_stats = []
        post_subreddit = []
        short_table = "###Top Team Subreddit Posts\n\n"
        long_table = "###Top Team Subreddit Posts\n\n"

        for team, abr in self.teams.items():
            url = "https://www.reddit.com{}/about.json".format(abr[1])
            w = requests.get(url, headers=self.headers)
            content = w.json()
            w.close()
            abr[1] = re.sub(r'/r/', '', abr[1])
            subreddit = self.r.subreddit(abr[1])

            for submission in subreddit.top('day'):
                post_subreddit.append('/r/{}'.format(str(submission.subreddit).lower()))
                percent = float(submission.score / content['data']['subscribers'] * 100)
                post_info = {'title': submission.title, 'shortlink': submission.shortlink, 'score': submission.score, 'percent': percent}
                post_stats.append(post_info)
                break

        post_stats = pd.DataFrame(post_stats, index=post_subreddit)
        post_stats = post_stats.sort_values(by=['score'], ascending=[False])

        # Sidebar table
        for i in range(0, 5):
            if i < len(post_stats.index):
                post = post_stats.index[i]
                short_table += '{}) []({}) - [{}]({})\n\n'.format(str(i+1), post, post_stats['title'][post], post_stats['shortlink'][post])

        # Wiki page table
        for i in range(0, 31):
            if i < len(post_stats.index):
                post = post_stats.index[i]
                long_table += '{}) []({}) - [{}]({})\n\n'.format(str(i+1), post, post_stats['title'][post], post_stats['shortlink'][post])

        long_table += 'Last Updated: {} PST'.format(datetime.now().strftime('%d %b %Y - %I:%M %p'))

        settings = (self.r.subreddit(self.subreddit).wiki['config/sidebar'].content_md)
        sidebar = re.sub(self.MAGICSTART + ".*?" + self.MAGICEND, short_table + self.MAGICENDNEW, settings, flags=re.DOTALL)

        self.r.subreddit(self.subreddit).wiki['config/sidebar'].edit(sidebar)
        self.r.subreddit(self.subreddit).wiki['topposts'].edit(long_table)


x = HockeyTopPosts()
x.top_posts()