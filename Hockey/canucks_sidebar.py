import requests, json, pyperclip, re, config, praw, capfriendly, pytz
import pandas as pd
from datetime import *
from dateutil.parser import *
from dateutil import tz
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

    r = praw.Reddit(client_id=config.reddit_id,
                    client_secret=config.reddit_secret,
                    username=config.reddit_user,
                    password=config.reddit_pass,
                    user_agent=config.reddit_agent)

    def standings(self):

        url = 'http://statsapi.web.nhl.com/api/v1/standings?season=' + self.SEASON
        w = requests.get(url)
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

    def player_stats(self, team_id):
        skater_stats = []
        skater_names = []
        goalie_stats = []
        goalie_names = []

        url = 'https://statsapi.web.nhl.com/api/v1/teams/{}?expand=team.roster'.format(str(team_id))
        w = requests.get(url)
        roster = json.loads(w.content.decode('utf-8'))
        w.close()

        for player in roster['teams'][0]['roster']['roster']:
            url = 'https://statsapi.web.nhl.com/api/v1/people/{}/stats?stats=yearByYear'.format(str(player['person']['id']))
            w = requests.get(url)
            stats = json.loads(w.content.decode('utf-8'))
            w.close()

            for season in stats['stats'][0]['splits']:
                if season['season'] == self.SEASON:
                    if season['team']['name'] == roster['teams'][0]['name']:
                        name = re.sub(r'(\w+\S+\s)', '', player['person']['fullName'], flags=re.MULTILINE)
                        if player['position']['code'] == 'G':
                            try:
                                gstats = season['stat']
                                goalie_stats.append(gstats)
                                goalie_names.append(name)
                            except Exception as e:
                                pass
                        else:
                            try:
                                pstats = season['stat']
                                skater_stats.append(pstats)
                                skater_names.append(name)
                            except Exception as e:
                                pass

        top_scorers = 'Player|GP|G|A|P|+/-|PIM|\n' + '|:|::|::|::|::|::|::|\n'
        goalies = '\n|Goalie|GP|W|L|SV%|GAA|SO|\n|:|::|::|::|::|::|::|\n'
        if skater_stats and goalie_stats:
            skater_stats = pd.DataFrame(skater_stats, index=skater_names)
            skater_stats = skater_stats.sort_values(by=['points', 'goals', 'games'], ascending=[False, False, True])
            goalie_stats = pd.DataFrame(goalie_stats, index=goalie_names)
            goalie_stats = goalie_stats.sort_values(by=['games'], ascending=[False])

            list_length = 10


            for i in range(0, list_length):
                if i < len(skater_stats.index):
                    player = skater_stats.index[i]
                    top_scorers += '|' + player + '|' + \
                                   str(skater_stats['games'][player]) + '|' + str(skater_stats['goals'][player]) + '|' + \
                                   str(skater_stats['assists'][player]) + '|**' + str(skater_stats['points'][player]) + \
                                   '**|' + str(skater_stats['plusMinus'][player]) + '|' + \
                                   str(skater_stats['penaltyMinutes'][player]) + '|\n'
            for i in range(0, 2):
                if i < len(goalie_stats.index):
                    goalie = goalie_stats.index[i]
                    goalies += '|' + goalie + '|' + \
                               str(goalie_stats['games'][goalie]) + '|' + str(goalie_stats['wins'][goalie]) + '|' + \
                               str(goalie_stats['losses'][goalie]) + '|{0:.3f}|'.format(goalie_stats['savePercentage'][goalie]) + \
                               '|{0:.2f}|'.format(goalie_stats['goalAgainstAverage'][goalie]) + \
                               str(goalie_stats['shutouts'][goalie]) + '|\n'

        comment = ('\n##Player Stats\n' + top_scorers + '\n##Goalie Stats' + goalies)

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
        w = requests.get(url)
        sched_data = json.loads(w.content.decode('utf-8'))
        reg_szn = []
        # Removes preseason games
        for game in sched_data['dates']:
            if game['games'][0]['gameType'] == 'R':
                reg_szn.append(game)
        w.close()

        bc_stations = ['SN', 'SN1', 'CBC', 'SNV', 'SNP', 'SN360', 'HNIC', 'CITY TV']

        schedule = '\n##Schedule\n|Date|Time|Opponent|TV/Score|\n|::|::|::|::|\n'

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
                    game_date = '**Tonight**'
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

        new_sidebar = (self.schedule() + self.standings() + self.player_stats(23) +
                       '\n*****\nUpdated at: ' + datetime.now().strftime("%d %b %Y, %I:%M %p") + ' PST\n*****')

        sidebar = re.sub(self.MAGICSTART + ".*?" + self.MAGICEND,
                         self.MAGICSTARTNEW + "\n\n" + new_sidebar + "\n\n" + self.MAGICENDNEW, settings,
                         flags=re.DOTALL)
        self.r.subreddit(self.SUBREDDIT).wiki['config/sidebar'].edit(sidebar)

        print(sidebar)
        # pyperclip.copy(sidebar)

    def update_injuries(self):
        ir_start = '\[\]\(#startinjuredreserve\)'
        ir_end = '\[\]\(#endinjuredreserve\)'
        ir_start_new = '[](#startinjuredreserve)'
        ir_end_new = '[](#endinjuredreserve)'

        settings = self.r.subreddit(self.SUBREDDIT).wiki['config/sidebar'].content_md
        new_sidebar = capfriendly.injured_reserve()
        sidebar = re.sub(ir_start + ".*?" + ir_end,
                         ir_start_new + "\n\n" + new_sidebar + "\n\n" + ir_end_new, settings,
                         flags=re.DOTALL)
        self.r.subreddit(self.SUBREDDIT).wiki['config/sidebar'].edit(sidebar)
        print(sidebar)

    def update_times(self):
        """
        Testing
        Set update intervals based on necessity. If Canucks have a game that day, higher frequency updates.
        Check if game is in progress and update quicker. Every 5 minutes? ['abstractGameState']
        If all games are final, stop updates for the night

        :return:
        """
        today = datetime.now(self.pacific).strftime('%Y-%m-%d')
        base_json = ""

        while True:
            # url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=' + today + '&endDate=' + today + '&expand=schedule.teams,schedule.linescore,schedule.broadcasts'
            # url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=2019-09-29&endDate=2019-09-29&expand=schedule.teams,schedule.linescore,schedule.broadcasts'
            url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate=2019-09-26&endDate=2019-09-26&expand=schedule.teams,schedule.linescore,schedule.broadcasts'
            games = requests.get(url).json()['dates'][0]['games']
            sleep_time = 0

            if base_json:
                for i, game in enumerate(games):
                    if 'vancouver canucks' in str(game).lower():
                        if not any(item in game['status']['abstractGameState'] for item in ['Abc', 'Preview']):
                            print('Game in progress: {} @ {}'.format(game['teams']['away']['team']['name'], game['teams']['home']['team']['name']))
                            # Update every 5 minutes


                    for team in game['teams']:

                        # Divisional standings
                        try:
                            team_division = game['teams'][team]['team']['division']['name']
                            new_status = game['status']['abstractGameState']
                            old_status = base_json[i]['status']['abstractGameState']
                            if team_division == 'Pacific':
                                if new_status == 'Final' and not new_status == old_status:
                                    print('Updating divisionial standings...')
                                    # Update divisionial standings
                                    print('Divisional standings updated!')
                        except KeyError as e:
                            pass

            base_json = games

            tm.sleep(sleep_time)

x = Sidebar()
x.update_sidebar()
# x.update_times()
# while True:
#     try:
#         x.update_sidebar()
#         tm.sleep(900)
#     except Exception as e:
#         print(e)
#         pass
# x.update_injuries()
