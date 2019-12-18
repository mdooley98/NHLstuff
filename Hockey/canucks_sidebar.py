import requests, json, re, config, praw, capfriendly, pytz, sqlite3
import pandas as pd
from datetime import *
from dateutil.parser import parse
from dateutil import tz
from dateutil.tz import tzlocal
import time as tm

class Sidebar:

    def __init__(self):
        self.teams = config.teams()
        self.SEASON = '20192020'
        self.MAGICSTART = '\[\]\(#startmagicalbotarea\)'
        self.MAGICEND = '\[\]\(#endmagicalbotarea\)'
        self.MAGICSTARTNEW = '[](#startmagicalbotarea)'
        self.MAGICENDNEW = '[](#endmagicalbotarea)'
        self.SUBREDDIT = 'canucks'
        self.pacific = pytz.timezone('US/Pacific')
        self.utc = pytz.timezone('UTC')
        self.headers = {'User-Agent': '/r/Canucks reddit'}

    r = praw.Reddit(client_id=config.reddit_id,
                    client_secret=config.reddit_secret,
                    username=config.reddit_user,
                    password=config.reddit_pass,
                    user_agent=config.reddit_agent)

    def standings(self):

        url = 'http://statsapi.web.nhl.com/api/v1/standings?season=' + self.SEASON
        w = requests.get(url, headers=self.headers)
        standings_data = json.loads(w.content.decode('utf-8'))
        w.close()

        pacific_standings = '\n##Pacific Standings\n|Team|GP|W|L|OTL|PTS|Streak\n|::|::|::|::|::|::|::|\n'

        for division in standings_data['records']:
            if division['division']['id'] == 15:
                for team in division['teamRecords']:
                    for name, abr in self.teams.items():
                        if team['team']['name'] in name:
                            try:
                                name_team = '[{}]({} "{}")'.format(name, abr[1], name)
                                gp_team = team['gamesPlayed']
                                wins_team = team['leagueRecord']['wins']
                                losses_team = team['leagueRecord']['losses']
                                otl_team = team['leagueRecord']['ot']
                                points_team = team['points']
                                streak_team = team['streak']['streakCode']
                                pacific_standings += '|' + str(name_team) + '|' + str(gp_team) + '|' + str(wins_team) + \
                                                     '|' + str(losses_team) + '|' + str(otl_team) + '|' + \
                                                     str(points_team) + '|' + str(streak_team) + '|\n'
                            except Exception as e:
                                pass

        return pacific_standings

    def wildcard(self):

        url = 'http://statsapi.web.nhl.com/api/v1/standings?season=' + self.SEASON
        w = requests.get(url, headers=self.headers)
        standings_data = json.loads(w.content.decode('utf-8'))
        w.close()

        wildcard = []
        central_leaders = []
        pacific_leaders = []

        for i in range(2, 4):
            for team in standings_data['records'][i]['teamRecords']:
                if not team['wildCardRank'] == '0':
                    wildcard.append(team)
                if team['wildCardRank'] == '0':
                    central_leaders.append(team) if standings_data['records'][i]['division']['name'] == 'Central' else pacific_leaders.append(team)
                # print(team['team']['name'])

        pacific_standings = '|PACIFIC|GP|W|L|OTL|PTS|Streak\n|::|::|::|::|::|::|::|\n'
        central_standings = '|CENTRAL|GP|W|L|OTL|PTS|Streak\n|::|::|::|::|::|::|::|\n'
        wildcard_standings = '|WC WEST|GP|W|L|OTL|PTS|Streak\n|::|::|::|::|::|::|::|\n'

        for team in central_leaders:
            for name, abr in self.teams.items():
                if team['team']['name'] in name:
                    name_team = '[{}]({} "{}")'.format(name, abr[1], name)
                    central_standings += f"| {name_team} | {team['gamesPlayed']} | {team['leagueRecord']['wins']} | " \
                                         f"{team['leagueRecord']['losses']} | {team['leagueRecord']['ot']} | {team['points']} | " \
                                         f"{team['streak']['streakCode']} |\n"

        for team in pacific_leaders:
            for name, abr in self.teams.items():
                if team['team']['name'] in name:
                    name_team = '[{}]({} "{}")'.format(name, abr[1], name)
                    pacific_standings += f"| {name_team} | {team['gamesPlayed']} | {team['leagueRecord']['wins']} | " \
                                         f"{team['leagueRecord']['losses']} | {team['leagueRecord']['ot']} | {team['points']} | " \
                                         f"{team['streak']['streakCode']} |\n"

        for i in range(0, (len(wildcard) + 1)):
            for team in wildcard:
                if team['wildCardRank'] == str(i):
                    if i == 3:
                        wildcard_standings += '|-|-|-|-|-|-|-|\n'
                    for name, abr in self.teams.items():
                        if team['team']['name'] in name:
                            name_team = '[{}]({} "{}")'.format(name, abr[1], name)
                            wildcard_standings += f"| {name_team} | {team['gamesPlayed']} | {team['leagueRecord']['wins']} | " \
                                                 f"{team['leagueRecord']['losses']} | {team['leagueRecord']['ot']} | {team['points']} | " \
                                                 f"{team['streak']['streakCode']} |\n"

        standings = f'---\n{central_standings}---\n{pacific_standings}---\n{wildcard_standings}---'

        return standings

    def player_stats(self, franchiseId):
        url = 'https://api.nhle.com/stats/rest/en/skater/summary'
        params = {
            'sort': '[{"property": "points", "direction": "DESC"}, {"property": "goals", "direction": "DESC"}, {"property": "assists", "direction": "DESC"}]',
            'start': '0',
            'limit': '50',
            'factCayennneExp': 'gamesPlayed>=1',
            'cayenneExp': f'franchiseId={franchiseId} and gameTypeId=2 and seasonId={self.SEASON}'
        }
        players = requests.get(url, params=params).json()['data']
        url = 'https://api.nhle.com/stats/rest/en/goalie/summary'
        params = {
            'sort': '[{"property": "wins", "direction": "DESC"}, {"property": "savePct", "direction": "DESC"}]',
            'start': '0',
            'limit': '50',
            'factCayenneExp': 'gamesPlayed>=1',
            'cayenneExp': f'franchiseId=20 and gameTypeId=2 and seasonId={self.SEASON}'
        }
        goalies = requests.get(url, params=params).json()['data']
        top_scorers = 'Player|GP|G|A|P|+/-|PIM|\n' + '|:|::|::|::|::|::|::|\n'
        top_goalies = '|Goalie|GP|W|L|SV%|GAA|SO|\n|:|::|::|::|::|::|::|\n'

        for i in range(0, 10):
            player = players[i]
            top_scorers += f"|{player['lastName']}|{player['gamesPlayed']}|{player['goals']}|{player['assists']}|**{player['points']}**|{player['plusMinus']}|{player['penaltyMinutes']}|\n"

        for i in range(0, len(goalies)):
            goalie = goalies[i]
            top_goalies += f"|{goalie['lastName']}|{goalie['gamesPlayed']}|{goalie['wins']}|{goalie['losses']}|{goalie['savePct']:.3f}|{goalie['goalsAgainstAverage']:.2f}|{goalie['shutouts']}|\n"

        comment = ('---\n' + top_scorers + '---\n' + top_goalies)

        return comment

    def schedule(self):
        # Few small modifications to Kurtenbot
        current_date = datetime.now().date()

        games_after = 0
        games_before = 0
        sched_start = 0
        sched_end = 6

        url = 'http://statsapi.web.nhl.com/api/v1/schedule?season={}&teamId=23&expand=schedule.broadcasts,schedule.linescore&site=en_nhlCA'.format(
            self.SEASON)
        w = requests.get(url, headers=self.headers)
        sched_data = json.loads(w.content.decode('utf-8'))
        reg_szn = []
        # Removes preseason games
        for game in sched_data['dates']:
            if game['games'][0]['gameType'] == 'R':
                reg_szn.append(game)
        w.close()

        bc_stations = ['SN', 'SN1', 'CBC', 'SNV', 'SNP', 'SN360', 'HNIC', 'CITY TV']

        schedule = '---\n|Date|Time|Opponent|TV/Score|\n|::|::|::|::|\n'

        for game in reg_szn:
            if parse(game['date']).date() < current_date:
                games_before += 1
            else:
                games_after += 1

        if games_before >= 3 and games_after >= 3:
            sched_start = games_before - 3
            sched_end = games_before + 3
        elif games_after < 3:
            sched_start = games_before - 3 - (3 - games_after)
            sched_end = len(reg_szn) - 1
        elif games_before < 3:
            sched_start = 0
            sched_end = 4

        for i, game in enumerate(reg_szn):
            if sched_start <= i <= sched_end:
                game_date = parse(game['date']).date()
                game_time = parse(game['games'][0]['gameDate'])
                game_time.replace(tzinfo=tz.gettz('UTC'))
                game_time = game_time.astimezone(tz=tz.gettz('America/Vancouver'))
                game_opponent = game['games'][0]['teams']['home']['team']['name'] if (
                        game['games'][0]['teams']['away']['team']['id'] == 23) else \
                    game['games'][0]['teams']['away']['team']['name']
                game_extra = ""

                if game_date == current_date:
                    check_time = game_time.strftime('%H:%M')
                    check_time = re.sub(':', '', check_time)
                    game_date = '**Today**' if int(check_time) < 1500 else '**Tonight**'
                elif game_date == current_date + timedelta(days=1):
                    game_date = 'Tomorrow'
                else:
                    game_date = game_date.strftime('%d %b')

                game_time = game_time.strftime('%H:%M')
                if game['games'][0]['teams']['home']['team']['id'] == 23:
                    game_opponent = 'vs [{}]({} "{}")'.format(game_opponent, self.teams[game_opponent][1],
                                                              game_opponent)
                else:
                    game_opponent = '@ [{}]({} "{}")'.format(game_opponent, self.teams[game_opponent][1], game_opponent)

                if game['games'][0]['status']['abstractGameState'] == 'Final':
                    if game['games'][0]['teams']['home']['team']['id'] == 23:
                        our_score = game['games'][0]['linescore']['teams']['home']['goals']
                        their_score = game['games'][0]['linescore']['teams']['away']['goals']
                    else:
                        our_score = game['games'][0]['linescore']['teams']['away']['goals']
                        their_score = game['games'][0]['linescore']['teams']['home']['goals']
                    if our_score > their_score:
                        game_extra = '**W {}-{}**'.format(our_score, their_score)
                    else:
                        if game['games'][0]['linescore']['currentPeriod'] > 3:
                            game_extra = 'OTL {}-{}'.format(their_score, our_score)
                        else:
                            game_extra = 'L {}-{}'.format(their_score, our_score)
                else:
                    if 'broadcasts' in game['games'][0]:
                        for broadcast in game['games'][0]['broadcasts']:
                            if broadcast['name'] in bc_stations:
                                game_extra = broadcast['name']
                                break

                schedule += '|{}|{}|{}|{}|\n'.format(game_date, game_time, game_opponent, game_extra)

        return schedule

    def update_sidebar(self):
        settings = self.r.subreddit(self.SUBREDDIT).wiki['config/sidebar'].content_md

        new_sidebar = (self.schedule() + self.wildcard() + self.player_stats(20) +
                       '\n*****\nUpdated at: ' + datetime.now().strftime("%d %b %Y, %I:%M %p") + ' PST\n*****')

        sidebar = re.sub(self.MAGICSTART + ".*?" + self.MAGICEND,
                         self.MAGICSTARTNEW + "\n\n" + new_sidebar + "\n\n" + self.MAGICENDNEW, settings,
                         flags=re.DOTALL)
        self.r.subreddit(self.SUBREDDIT).wiki['config/sidebar'].edit(sidebar)
        print('Sidebar updated @ {}'.format(datetime.now().strftime("%I:%M %p")))
        # print(sidebar)
        return sidebar

    def update_injuries(self):
        ir_start = '\[\]\(#startinjuredreserve\)'
        ir_end = '\[\]\(#endinjuredreserve\)'
        ir_start_new = '[](#startinjuredreserve)'
        ir_end_new = '[](#endinjuredreserve)'

        settings = self.r.subreddit(self.SUBREDDIT).wiki['config/sidebar'].content_md
        new_sidebar = capfriendly.injured_reserve()
        sidebar = re.sub(ir_start + ".*?" + ir_end,
                         ir_start_new + "\n\n" + new_sidebar + "\n" + ir_end_new, settings,
                         flags=re.DOTALL)
        self.r.subreddit(self.SUBREDDIT).wiki['config/sidebar'].edit(sidebar)
        print(sidebar)

    def update_times(self):
        prompt = input('Do an initial update? (y/n): ')
        if any(x == prompt for x in ['y', 'Y']):
            self.update_sidebar()
        else:
            pass
        conn = sqlite3.connect('sidebar_game_ids.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE if not exists game_ids (
                            id text
                            )""")
        conn.commit()

        while True:
            today = datetime.now(self.pacific).strftime('%Y-%m-%d')
            now = datetime.now(self.pacific).strftime('%Y-%m-%d, %I:%M')
            # today = '2019-10-17'
            url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate={}&endDate={}&expand=schedule.teams,schedule.linescore,schedule.broadcasts'.format(today, today)
            # print(url)
            games = requests.get(url, headers=self.headers).json()['dates'][0]['games']

            # Update if it hasn't been updated for today's date
            update_date = re.search('Updated at: (\d+ \w+ \d+)', self.r.subreddit(self.SUBREDDIT).wiki['config/sidebar'].content_md)
            if not update_date.group(1) == datetime.now().strftime('%d %b %Y'):
                print('New day. Updating sidebar...\n')
                self.update_sidebar()

            # Sleep until the first game of the day
            first_gametime = games[0]['gameDate']
            difference = (datetime.strptime(first_gametime, '%Y-%m-%dT%H:%M:%SZ') - datetime.utcnow()).total_seconds()
            if difference > 0:
                first_gametime = self.utc.localize(datetime.strptime(first_gametime, '%Y-%m-%dT%H:%M:%SZ')).astimezone(self.pacific).strftime('%I:%M %p')
                print(f'Games have not begun. Sleeping until {first_gametime}')
                tm.sleep(difference)
                continue

            print('\rScanning games for {}'.format(now), end='\n')
            for game in games:
                game_status = game['status']['abstractGameState']

                if 'vancouver canucks' in str(game).lower():
                    if not any(item in game_status for item in ['Final', 'Preview']):
                        print('Game in progress: {} @ {}'.format(game['teams']['away']['team']['name'],
                                                                 game['teams']['home']['team']['name']))

                if any(item == 'Western' for item in [game['teams']['away']['team']['conference']['name'],
                                                      game['teams']['home']['team']['conference']['name']]):
                    c.execute("SELECT id FROM game_ids WHERE id = '{}'".format(game['gamePk']))
                    if game_status == 'Final' and not c.fetchone():
                        print('Updating sidebar...  {}'.format(datetime.now().strftime("%I:%M %p")))
                        # Give NHL API 15 minutes to update after game ends
                        tm.sleep(60*15)
                        self.update_sidebar()
                        print('Game finished: {} @ {}'.format(game['teams']['away']['team']['name'],
                                                              game['teams']['home']['team']['name']))

                        c.execute("INSERT INTO game_ids VALUES ('{}')".format(game['gamePk']))
                        for i in range(0, len(games)):
                            c.execute("SELECT id FROM game_ids WHERE id = '{}'".format(games[i]['gamePk']))
                            if games[i]['status']['abstractGameState'] == 'Final' and not c.fetchone():
                                print('Adding game to database: {} @ {}, {}'.format(
                                    games[i]['teams']['away']['team']['name'],
                                    games[i]['teams']['home']['team']['name'], games[i]['gamePk']))
                                c.execute("INSERT INTO game_ids VALUES ('{}')".format(games[i]['gamePk']))
                        conn.commit()
                        break

            # If all games over sleep until next day
            if all(game['status']['abstractGameState'] == 'Final' for game in games):
                tomorrow = str(date.today() + timedelta(days=1)) + ' 08:00:00'
                difference = (datetime.strptime(tomorrow,
                                                '%Y-%m-%d %I:%M:%S') - datetime.utcnow()).total_seconds()
                print(f'All games for the day are over. Sleeping until {str(date.today() + timedelta(days=1))}')
                tm.sleep(difference)
                continue

            tm.sleep(60*5)

    def update_times2(self):
        """
        UNFINISHED
        Attempting to force an update when player stats change.
        """

        conn = sqlite3.connect('sidebar_game_ids.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE if not exists game_ids (
                                    id text
                                    )""")
        conn.commit()

        while True:
            today = datetime.now(self.pacific).strftime('%Y-%m-%d')
            now = datetime.now(self.pacific).strftime('%Y-%m-%d, %I:%M')
            url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate={}&endDate={}&expand=schedule.teams,schedule.linescore,schedule.broadcasts'.format(today, today)
            games = requests.get(url, headers=self.headers).json()['dates'][0]['games']

            # Update if it hasn't been updated for today's date
            # try:
            #     update_date = re.search('Updated at: (\d+ \w+ \d+)', self.r.subreddit(self.SUBREDDIT).wiki['config/sidebar'].content_md)
            #     if not update_date.group(1) == datetime.now().strftime('%d %b %Y'):
            #         print('New day. Updating sidebar...')
            #         self.update_sidebar()
            # except AttributeError:
            #     pass

            print('\rScanning games for {}'.format(now), end='\n')
            for game in games:
                game_status = game['status']['abstractGameState']

                c.execute("SELECT id FROM game_ids WHERE id = '{}'".format(game['gamePk']))
                if game_status == 'Final' and not c.fetchone():
                    if 'vancouver canucks' in str(game).lower():
                        old_stats = self.r.subreddit(self.SUBREDDIT).wiki['config/sidebar'].content_md
                        old_stats = re.search('(\n##Player Stats\n(.*?))\*\*\*\*\*', old_stats, flags=re.DOTALL)
                        print('Updating sidebar... {}'.format(datetime.now().strftime("%I:%M %p")))
                        tm.sleep(5)
                        self.update_sidebar()
                        print('Standings updated.\n')
                        while True:
                            new_stats = re.search('(\n##Player Stats\n(.*?))\*\*\*\*\*', self.update_sidebar(), flags=re.DOTALL)
                            if not old_stats.group(1).strip() == new_stats.group(1).strip():
                                print('New stats, updating now... {}'.format(datetime.now().strftime("%I:%M %p")))
                                self.update_sidebar()
                                print('Player stats updated.\n')
                                c.execute("INSERT INTO game_ids VALUES ('{}')".format(game['gamePk']))
                                break
                            elif old_stats.group(1).strip() == new_stats.group(1).strip():
                                print('Stats still match, waiting to check again... {}'.format(datetime.now().strftime("%I:%M %p")))
                                tm.sleep(15)
                        conn.commit()

                    elif not 'canucks' in str(game).lower() and any(item == 'Pacific' for item in
                                                                    [game['teams']['away']['team']['division']['name'],
                                                                     game['teams']['home']['team']['division']['name']]):
                        print('Updating sidebar...  {}'.format(datetime.now().strftime("%I:%M %p")))
                        # Give NHL API 15 minutes to update after game ends
                        tm.sleep(10)
                        self.update_sidebar()
                        print('Sidebar updated at {}\n'.format(datetime.now().strftime("%I:%M %p")))
                        print('Game finished: {} @ {}'.format(game['teams']['away']['team']['name'],
                                                              game['teams']['home']['team']['name']))

                        c.execute("INSERT INTO game_ids VALUES ('{}')".format(game['gamePk']))
                        for i in range(0, len(games)):
                            c.execute("SELECT id FROM game_ids WHERE id = '{}'".format(games[i]['gamePk']))
                            if games[i]['status']['abstractGameState'] == 'Final' and not c.fetchone() and not 'canucks'\
                                    in str(games[i]).lower():
                                print('Adding game to database: {} @ {}, {}'.format(
                                    games[i]['teams']['away']['team']['name'],
                                    games[i]['teams']['home']['team']['name'], games[i]['gamePk']))
                                c.execute("INSERT INTO game_ids VALUES ('{}')".format(games[i]['gamePk']))
                        # conn.commit()
                        pass


x = Sidebar()
x.update_times()
# x.update_injuries()
