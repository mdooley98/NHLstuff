import requests, os, urllib.request, re
from pathlib import Path
base_dir = Path(__file__).parent

class NHLVideoScraper:

    def __init__(self):
        self.path = base_dir/'Videos'
        pass

    def get_game_ids(self):
        # Team game log or player game log
        url = 'http://statsapi.web.nhl.com/api/v1/schedule?season=20172018&teamId=23&expand=schedule.broadcasts,schedule.linescore&site=en_nhlCA'
        response = requests.get(url).json()
        game_ids = []

        for game in response['dates']:
            if game['games'][0]['status']['statusCode'] == '7':  # Code 7 to exclude preseason games
                game_ids.append(game['games'][0]['gamePk'])

        return game_ids

    def get_event_ids(self):
        games = []
        for game_id in self.get_game_ids():
            url = 'https://statsapi.web.nhl.com/api/v1/game/{}/feed/live'.format(game_id)
            livedata = requests.get(url).json()
            event_list = []
            event_ids = {}

            for play in livedata['liveData']['plays']['allPlays']:
                # Conditions for which videos you want
                if play['result']['event'] == 'Goal' and play['result']['strength']['name'] == 'Short Handed' and not \
                play['team']['name'] == 'Vancouver Canucks':
                    event_list.append(play['about']['eventId'])


            if event_list:
                event_ids["gameId"] = game_id
                event_ids["eventId"] = event_list
                games.append(event_ids)

        return games

    def download_videos(self):
        if not os.path.exists(self.path):
            self.path.mkdir()

        for game in self.get_event_ids():
            url = 'https://statsapi.web.nhl.com/api/v1/game/{}/content'.format(game['gameId'])
            content = requests.get(url).json()
            for game_id in game['eventId']:
                for play in content['media']['milestones']['items']:
                    try:
                        if int(play['statsEventId']) == game_id:
                            if play['highlight']['playbacks'][-1]['name'] == 'FLASH_1800K_960X540':
                                description = re.sub(':', '', play['description'])
                                date = re.findall(r'\d{4}-\d{2}-\d{2}', play['timeAbsolute'])
                                title = '{} {}.mp4'.format(date[0], description)
                                print(title)
                                if os.path.exists(self.path / title):
                                    continue
                                urllib.request.urlretrieve(play['highlight']['playbacks'][-1]['url'], self.path/title)
                    except Exception as e:
                        pass


x = NHLVideoScraper()
x.download_videos()

