import pandas as pd

class Endpoints:


    def __init__(self, region):
        self.region = region
        self.ranks = ['IRON',
                    'BRONZE',
                    'SILVER',
                    'GOLD',
                    'PLATINUM',
                    'DIAMOND']
        self.tiers = ['I',
                    'II',
                    'III',
                    'IV']

        self.regions = {
            'BR1':'https://br1.api.riotgames.com',
            'EUN1':'https://eun1.api.riotgames.com',
            'EUW1':'https://euw1.api.riotgames.com',
            'JP1':'https://jp1.api.riotgames.com',
            'KR':'https://kr.api.riotgames.com',
            'LA1':'https://la1.api.riotgames.com',
            'LA2':'https://la2.api.riotgames.com',
            'NA1':'https://na1.api.riotgames.com',
            'OC1':'https://oc1.api.riotgames.com',
            'TR1':'https://tr1.api.riotgames.com',
            'RU':'https://ru.api.riotgames.com',
            }
        self.url = self.regions[self.region]
    
    def ranked_solo_gen(self):
        return [f"{self.url}/lol/league/v4/entries/RANKED_SOLO_5x5/{i}/{j}?page=1" for i in self.ranks for j in self.tiers]

    def playerId_gen(self, data):
        data = data['summonerId'].tolist()
        return [f"{self.url}/lol/summoner/v4/summoners/{i}" for i in data]

    def matchId_list_gen(self, data):
        data = data['accountId'].tolist()
        return [f"{self.url}/lol/match/v4/matchlists/by-account/{i}" for i in data]

    def matchId_gen(self, data):
        data = data['gameId'].tolist()
        return [f"{self.url}/lol/match/v4/matches/{i}" for i in data]







