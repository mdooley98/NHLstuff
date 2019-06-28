import requests, json, pyperclip, re, config, praw
import pandas as pd
from datetime import *
from dateutil.parser import *
from dateutil import tz

class Sidebar():

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
                      'St Louis Blues': ['STL', '/r/stlouisblues'],
                      'Montréal Canadiens': ['MTL', '/r/habs']
                      }
        self.SEASON = '20182019'
        self.MAGICSTART = '\[\]\(#startmagicalbotarea\)'
        self.MAGICEND = '\[\]\(#endmagicalbotarea\)'
        self.MAGICSTARTNEW = '[](#startmagicalbotarea)'
        self.MAGICENDNEW = '[](#endmagicalbotarea)'
        self.SUBREDDIT = 'canucks'

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

        pacific_standings = '|Team|GP|W|L|OTL|PTS|Streak\n|::|::|::|::|::|::|::|\n'

        for division in standings_data['records']:
            if division['division']['id'] == 15:
                for team in division['teamRecords']:
                    for name, abr in self.teams.items():
                        if team['team']['name'] in name:
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

                return pacific_standings

    def player_stats(self, id):
        skater_stats = []
        skater_names = []
        goalie_stats = []
        goalie_names = []
        players = ['Motte', 'Leivo', 'Goldobin']

        url = 'https://statsapi.web.nhl.com/api/v1/teams/' + str(id) + '?expand=team.roster'
        w = requests.get(url)
        roster = json.loads(w.content.decode('utf-8'))
        w.close()

        for player in roster['teams'][0]['roster']['roster']:
            url = 'https://statsapi.web.nhl.com/api/v1/people/' + str(
                player['person']['id']) + '/stats?stats=yearByYear'
            w = requests.get(url)
            stats = json.loads(w.content.decode('utf-8'))
            w.close()

            for season in stats['stats'][0]['splits']:
                if season['season'] == self.SEASON:
                    if season['team']['name'] == roster['teams'][0]['name']:
                        name = re.sub(r'(\w+.+ )', '', player['person']['fullName'], flags=re.MULTILINE)

                        if player['position']['code'] == 'G':
                            try:
                                gstats = season['stat']
                                goalie_stats.append(gstats)
                                goalie_names.append(name)
                            except Exception as e:
                                pass
                        else:
                            try:
                                # if name in players:
                                pstats = season['stat']
                                skater_stats.append(pstats)
                                # skater_names.append('\#' + player['jerseyNumber'] + ' ' + name)
                                skater_names.append((name))
                            except Exception as e:
                                pass

        top_scorers = 'Player|GP|G|A|P|+/-|PIM|\n' + '|:|::|::|::|::|::|::|\n'
        goalies = '\n|Goalie|GP|W|L|SV%|GAA|SO|\n|:|::|::|::|::|::|::|\n'
        skater_stats = pd.DataFrame(skater_stats, index=skater_names)
        skater_stats = skater_stats.sort_values(by=['points', 'goals', 'games'], ascending=[False, False, True])
        list_length = 10
        goalie_stats = pd.DataFrame(goalie_stats, index=goalie_names)
        goalie_stats = goalie_stats.sort_values(by=['games'], ascending=[False])

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
                           str(goalie_stats['losses'][goalie]) + '|' + str(goalie_stats['savePercentage'][goalie]) + \
                           '|' + str(goalie_stats['goalAgainstAverage'][goalie]) + '|' + \
                           str(goalie_stats['shutouts'][goalie]) + '|\n'

        comment = ('##Player Stats\n' + top_scorers + '\n##Goalie Stats' + goalies)

        return comment

    def schedule(self):
        # Few small modifications to Kurtenbot
        current_date = datetime.now().date()

        games_after = 0
        games_before = 0
        sched_start = 0
        sched_end = 6

        url = 'http://statsapi.web.nhl.com/api/v1/schedule?season=20182019&teamId=23&expand=schedule.broadcasts,schedule.linescore&site=en_nhlCA'
        w = requests.get(url)
        sched_data = json.loads(w.content.decode('utf-8'))
        sched_data = sched_data['dates']
        w.close()

        bc_stations = ['SN', 'SN1', 'CBC', 'SNV', 'SNP', 'SN360', 'HNIC', 'CITY TV']

        schedule = '|Date|Time|Opponent|TV/Score|\n|::|::|::|::|\n'

        for game in sched_data:
            if parse(game['date']).date() < current_date:
                games_before += 1
            else:
                games_after += 1

        if games_before >= 3 and games_after >= 3:
            sched_start = games_before - 3
            sched_end = games_before + 3
        elif games_after < 3:
            sched_start = games_before - 3 - (3 - games_after)
            sched_end = len(sched_data) - 1
        elif games_before < 3:
            sched_start = 0
            sched_end = 7

        for i, game in enumerate(sched_data):
            if (i >= sched_start and i <= sched_end):
                game_date = parse(game['date']).date()
                game_time = parse(game['games'][0]['gameDate'])
                game_time.replace(tzinfo=tz.gettz('UTC'))
                game_time = game_time.astimezone(tz=tz.gettz('America/Vancouver'))
                game_opponent = game['games'][0]['teams']['home']['team']['name'] if (game['games'][0]['teams']['away']['team']['id'] == 23) else game['games'][0]['teams']['away']['team']['name']
                game_extra = ""

            # print(games_before, games_after)
            # print(sched_start, sched_end)
            # print(i)

                if game_date == current_date:
                    game_date = '**Tonight**'
                elif game_date == current_date + timedelta(days=1):
                    game_date = 'Tomorrow'
                else:
                    game_date = game_date.strftime('%d %b')

                game_time = game_time.strftime('%H:%M')
                if game['games'][0]['teams']['home']['team']['id'] == 23:
                    game_opponent = 'vs [{}]({} "{}")'.format(game_opponent, self.teams[game_opponent][1], game_opponent)
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

    def standings_stats(self):
        settings = (self.r.subreddit(self.SUBREDDIT).wiki['config/sidebar'].content_md)

        new_sidebar = ('##Schedule\n' + self.schedule() + '\n##Pacific Standings\n' + self.standings() + '\n' + \
                       self.player_stats(23) + '\n*****\nUpdated at: ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + \
                       ' PST\n*****')

        sidebar = re.sub(self.MAGICSTART + ".*?" + self.MAGICEND, self.MAGICSTARTNEW + "\n\n" + new_sidebar + "\n\n" + self.MAGICENDNEW, settings, flags=re.DOTALL)
        self.r.subreddit(self.SUBREDDIT).wiki['config/sidebar'].edit(sidebar)

    def sidebar_test(self):
        pass

class Draft():

    def __init__(self):

        self.url = 'https://statsapi.web.nhl.com/api/v1/draft/2019'
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
                      'St Louis Blues': ['STL', '/r/stlouisblues'],
                      'Montréal Canadiens': ['MTL', '/r/habs']
                      }

    def draft_table(self):
        table = "|Round|Overall|Player|Team|\n|:--|:--|:--|:-:|\n"

        w = requests.get(self.url)
        draft = json.loads(w.content.decode('utf-8'))
        w.close()

        for selection in draft['drafts'][0]['rounds'][0]['picks']:
            for team, abr in self.teams.items():
                if team in selection['team']['name']:
                    team = ('[]({})').format(abr[1])
                    table += '|' + str(selection['round']) + '|' + str(selection['pickOverall']) + '|' + \
                        str(selection['prospect']['fullName']) + '|' + str(team) + '|\n'

        print(table)
        pyperclip.copy(table)

    def wide_draft(self):
        prospect_info = []
        prospect_name = []
        table = "|Round|Overall|Player|Team|Round|Overall|Player|Team|\n|:-|:-|:-|:-|:-|:-|:-|:-|\n"

        w = requests.get(self.url)
        draft = json.loads(w.content.decode('utf-8'))
        w.close()

        # ['drafts'][0]['rounds'][draft round minus one]
        for selection in draft['drafts'][0]['rounds'][6]['picks']:
            for team, abr in self.teams.items():
                if selection['team']['name'] in team:
                    prospect_name.append(selection['prospect']['fullName'])
                    selection["abr"] = abr[0]
                    selection["sub"] = abr[1]
                    prospect_info.append(selection)

        prospect_info = pd.DataFrame(prospect_info, index=prospect_name)

        # number = int(len(prospect_info))
        # n = int(number / 2)
        i = 0
        while i < 15:
            pros = prospect_info.index[i]
            pros16 = prospect_info.index[i+16]

            table += ('|' + str(prospect_info['round'][pros]) + '|' + str(prospect_info['pickOverall'][pros]) + '|' + \
                pros + '|' + '[{}]({})' + '|' + str(prospect_info['round'][pros16]) + '|' + \
                str(prospect_info['pickOverall'][pros16]) + '|' + pros16 + '|' + '[{}]({})' + \
                '|\n').format(str(prospect_info['abr'][pros]), str(prospect_info['sub'][pros]), str(prospect_info['abr'][pros16]), str(prospect_info['sub'][pros16]))
            i = i+1

        pros = prospect_info.index[i+0]
        table += ('|' + str(prospect_info['round'][pros]) + '|' + str(prospect_info['pickOverall'][pros]) + '|' + \
                 pros + '|' + '[{}]({})' + '|\n').format(str(prospect_info['abr'][pros]), str(prospect_info['sub'][pros]))
        print(table)
        pyperclip.copy(table)

    def canucks_draft(self):
        table = "|Round|OA|Player|Pos|Amateur Team|NHL CS Rank|\n|:--:|:--:|:--:|:--:|:--:|:--:|\n"

        w = requests.get(self.url)
        draft = json.loads(w.content.decode('utf-8'))
        w.close()

        for i in range(0,7):
            for selection in draft['drafts'][0]['rounds'][i]['picks']:
                if selection['team']['name'] == 'Vancouver Canucks':

                    url = 'https://statsapi.web.nhl.com/api/v1/draft/prospects/' + str(selection['prospect']['id'])
                    w = requests.get(url)
                    player = json.loads(w.content.decode('utf-8'))
                    w.close()

                    for stat in player['prospects']:
                        if stat['ranks']:
                            table += '|' + str(selection['round']) + '|' + str(selection['pickOverall']) + '|' + \
                                str(selection['prospect']['fullName']) + '|' + str(stat['primaryPosition']['abbreviation']) + \
                                '|' + str(stat['amateurTeam']['name']) + '(' + str(stat['amateurLeague']['name']) + ')|' + \
                                str(stat['prospectCategory']['shortName']) + ' - ' + str(stat['ranks']['finalRank']) + '|\n'
                        else:
                            table += '|' + str(selection['round']) + '|' + str(selection['pickOverall']) + '|' + \
                                str(selection['prospect']['fullName']) + '|' + str(stat['primaryPosition']['abbreviation']) + \
                                '|' + str(stat['amateurTeam']['name']) + '(' + str(stat['amateurLeague']['name']) + ')|' + \
                                ' ' + '|\n'

        print(table)
        pyperclip.copy(table)

class Game():

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
                      'St Louis Blues': ['STL', '/r/stlouisblues'],
                      'Montréal Canadiens': ['MTL', '/r/habs']
                      }

    def schedule(self):
        current_date = datetime.now().date()

        games_after = 0
        games_before = 0
        sched_start = 0
        sched_end = 6

        url = 'http://statsapi.web.nhl.com/api/v1/schedule?season=20182019&teamId=23&expand=schedule.broadcasts,schedule.linescore&site=en_nhlCA'
        w = requests.get(url)
        sched_data = json.loads(w.content.decode('utf-8'))
        sched_data = sched_data['dates']
        w.close()

        bc_stations = ['SN', 'SN1', 'CBC', 'SNV', 'SNP', 'SN360', 'HNIC', 'CITY TV']

        schedule = '|Date|Time|Opponent|TV/Score|\n|::|::|::|::|\n'

        for game in sched_data:
            if parse(game['date']).date() < current_date:
                games_before += 1
            else:
                games_after += 1

        if games_before >= 3 and games_after >= 3:
            sched_start = games_before - 3
            sched_end = games_before + 3
        elif games_after < 3:
            sched_start = games_before - 3 - (3 - games_after)
            sched_end = len(sched_data) - 1
        elif games_before < 3:
            sched_start = 0
            sched_end = 7

        for i, game in enumerate(sched_data):
            if (i >= sched_start and i <= sched_end):
                game_date = parse(game['date']).date()
                game_time = parse(game['games'][0]['gameDate'])
                game_time.replace(tzinfo=tz.gettz('UTC'))
                game_time = game_time.astimezone(tz=tz.gettz('America/Vancouver'))
                game_opponent = game['games'][0]['teams']['home']['team']['name'] if (game['games'][0]['teams']['away']['team']['id'] == 23) else game['games'][0]['teams']['away']['team']['name']
                game_extra = ""

            # print(games_before, games_after)
            # print(sched_start, sched_end)
            # print(i)

                if game_date == current_date:
                    game_date = '**Tonight**'
                elif game_date == current_date + timedelta(days=1):
                    game_date = 'Tomorrow'
                else:
                    game_date = game_date.strftime('%d %b')

                game_time = game_time.strftime('%H:%M')
                if game['games'][0]['teams']['home']['team']['id'] == 23:
                    game_opponent = 'vs [{}]({} "{}")'.format(game_opponent, self.teams[game_opponent][1], game_opponent)
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

        print(schedule)
        pyperclip.copy(schedule)
        return schedule

class Stats2():

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
                      'St Louis Blues': ['STL', '/r/stlouisblues'],
                      'Montréal Canadiens': ['MTL', '/r/habs']
                      }

    # Not adjusted for traded players
    def player_stats(self, id):
        skater_stats = []
        skater_names = []
        goalie_stats = []
        goalie_names = []

        url = 'https://statsapi.web.nhl.com/api/v1/teams/' + str(id) + '?expand=team.roster'
        w = requests.get(url)
        roster = json.loads(w.content.decode('utf-8'))
        w.close()

        for player in roster['teams'][0]['roster']['roster']:
            url = 'https://statsapi.web.nhl.com/api/v1/people/' + str(
                player['person']['id']) + '/stats?stats=statsSingleSeason'
            w = requests.get(url)
            stats = json.loads(w.content.decode('utf-8'))
            w.close()

            name = re.sub(r'(\w+.+ )', '', player['person']['fullName'], flags=re.MULTILINE)

            if player['position']['code'] == 'G':
                try:
                    gstats = stats['stats'][0]['splits'][0]['stat']
                    goalie_stats.append(gstats)
                    # goalie_names.append('\#' + player['jerseyNumber'] + ' ' + name)
                    goalie_names.append(name)
                except Exception as e:
                    pass
            else:
                try:
                    pstats = stats['stats'][0]['splits'][0]['stat']
                    skater_stats.append(pstats)
                    # skater_names.append('\#' + player['jerseyNumber'] + ' ' + name)
                    skater_names.append((name))
                except Exception as e:
                    pass

        top_scorers = 'Player|GP|G|A|P|+/-|PIM|\n' + '|:|::|::|::|::|::|::|\n'
        goalies = '\n|Goalie|GP|W|L|SV%|GAA|SO|\n|:|::|::|::|::|::|::|\n'
        skater_stats = pd.DataFrame(skater_stats, index=skater_names)
        skater_stats = skater_stats.sort_values(by=['points', 'goals', 'games'], ascending=[False, False, True])
        list_length = 10
        goalie_stats = pd.DataFrame(goalie_stats, index=goalie_names)
        goalie_stats = goalie_stats.sort_values(by=['games'], ascending=[False])

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
                           str(goalie_stats['losses'][goalie]) + '|' + str(goalie_stats['savePercentage'][goalie]) + \
                           '|' + str(goalie_stats['goalAgainstAverage'][goalie]) + '|' + \
                           str(goalie_stats['shutouts'][goalie]) + '|\n'

        comment = (top_scorers + '\n##Goalie Stats' + goalies)
        top_scorers = 'Name|GP|G|A|P|+/-|PIM|\n' + '|:--|:--:|:--:|:--:|:--:|:--:|:--:|\n'
        skater_stats = []
        skater_names = []

        return comment

    def goalie_stats(self, id):

        url = 'https://statsapi.web.nhl.com/api/v1/teams'
        w = requests.get(url)
        teamdata = json.loads(w.content.decode('utf-8'))
        w.close()

        for team in teamdata['teams']:
            if team['active'] == True:
                print('###' + team['name'])



            goalie_stats = []
            goalie_names = []

            url = 'https://statsapi.web.nhl.com/api/v1/teams/' + str(team['id']) + '?expand=team.roster'
            w = requests.get(url)
            roster = json.loads(w.content.decode('utf-8'))
            w.close()

            for player in roster['teams'][0]['roster']['roster']:

                url = 'https://statsapi.web.nhl.com/api/v1/people/' + str(player['person']['id']) + '/stats?stats=statsSingleSeason'
                w = requests.get(url)
                stats = json.loads(w.content.decode('utf-8'))
                w.close()

                name = re.sub(r'(\w+.+ )', '', player['person']['fullName'], flags=re.MULTILINE)

                if player['position']['code'] == 'G':
                    try:
                        gstats = stats['stats'][0]['splits'][0]['stat']
                        goalie_stats.append(gstats)
                        goalie_names.append(name)
                    except Exception as e:
                        pass

            goalies = '\n|Goalie|GP|W|L|SV%|GAA|SO|\n|:|::|::|::|::|::|::|\n'
            goalie_stats = pd.DataFrame(goalie_stats, index=goalie_names)
            goalie_stats = goalie_stats.sort_values(by=['games'], ascending=[False])

            for i in range(0, 2):
                if i < len(goalie_stats.index):
                    goalie = goalie_stats.index[i]
                    goalies += '|' + goalie + '|' + \
                               str(goalie_stats['games'][goalie]) + '|' + str(goalie_stats['wins'][goalie]) + '|' + \
                               str(goalie_stats['losses'][goalie]) + '|' + str(goalie_stats['savePercentage'][goalie]) + \
                               '|' + str(goalie_stats['goalAgainstAverage'][goalie]) + '|' + \
                               str(goalie_stats['shutouts'][goalie]) + '|\n'

            print(goalies)
            pyperclip.copy(goalies)

x = Sidebar()
x.standings_stats()

# x.player_stats(23)
# x.test2(23)
# x.sidebar_test()
# y = Draft()
# y.draft_table()
# y.wide_draft()
# y.canucks_draft()
# z = Game()
# z.schedule()
# z.test()
# a = Stats2()
# a.goalie_stats(23)