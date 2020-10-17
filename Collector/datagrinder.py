import pandas as pd 
from endpoints import Endpoints
import requests
import json
from tools import flattenList
from tqdm import tqdm 
import time
import pymongo
from pymongo import MongoClient


def replace_nans_with_dict(series):
    for idx in series[series.isnull()].index:
        series.at[idx] = {}
    return series

def df_explosion(df, col_name:str):
    if df[col_name].isna().any():
        df[col_name] = replace_nans_with_dict(df[col_name])
    df.reset_index(drop=True, inplace=True)
    df1 = pd.DataFrame(df.loc[:,col_name].values.tolist())
    df = pd.concat([df,df1], axis=1)
    df.drop([col_name], axis=1, inplace=True)
    return df

class MeatGrinder:

    def __init__(self, api_key:str):
        self.api_key = api_key
        self.data_list = []
        self._Endpoints = Endpoints('JP1')
    
    def ranked_5x5_data(self):
        rank_nb = len(self._Endpoints.ranked_solo_gen())
        for i in tqdm(range(rank_nb)):
            api_name = self._Endpoints.ranked_solo_gen()[i]
            r = requests.get(
                api_name,
                headers={'X-Riot-Token': self.api_key}
            )
            if str(r) == '<Response [403]>':
                raise Exception('403 Forbidden, renew API key')
            else:
                summoners = r.json()
                self.data_list.append(summoners)
                time.sleep(1)
        df = pd.DataFrame.from_records(flattenList(self.data_list))
        df.drop(['queueType', 
        'summonerName', 
        'leagueId', 
        'hotStreak',
        'miniSeries', 
        'freshBlood',
        'inactive'], axis=1, inplace=True)
        df['winRatio'] = (df['wins'] / (df['wins'] + df['losses']))
        summonerId_list = self._Endpoints.playerId_gen(df)
        summ_nb = len(summonerId_list)
        self.data_list = []
        for summs in tqdm(range(summ_nb)):
            api_name = summonerId_list[summs]
            r = requests.get(
                api_name,
                headers={'X-Riot-Token': self.api_key}
            )
            if str(r) == '<Response [403]':
                raise Exception('403 Forbidden, renew API key')
            else:
                accounts = r.json()
                self.data_list.append(accounts)
                temp_df = pd.DataFrame.from_records(self.data_list)
                time.sleep(1)
                df[['accountId', 'summonerLevel']] = temp_df[['accountId', 'summonerLevel']]
                del temp_df
        return df

    def match_data_players(self, data:object):
        accountId_list = self._Endpoints.matchId_list_gen(data)
        player_nb = len(accountId_list)
        self.data_list = []
        for accs in tqdm(range(player_nb)):
            api_name = accountId_list[accs]
            r = requests.get(
                api_name,
                headers={'X-Riot-Token': self.api_key}
            )
            if str(r) == '<Response [403]>':
                raise Exception('403 Forbidden, renew API key')
            else:
                matches = r.json()
                self.data_list.append(matches)
                time.sleep(1)
        match_df = pd.DataFrame.from_records(self.data_list)
        rmv_mask = match_df['matches'].apply(lambda x: isinstance(x, (float, str)))
        match_df.reset_index(drop=True, inplace=True)
        match_df = match_df[~rmv_mask]
        match_df = match_df.explode('matches')
        match_df = df_explosion(match_df, 'matches')
        match_df.drop(['startIndex', 
        'endIndex',
        'totalGames',
        'platformId',
        'champion',
        'puuid', 
        'name', 
        'profileIconId', w
        'revisionDate', 
        'summonerLevel'], axis=1, inplace=True, errors='ignore')
        return match_df

    def match_data(self, data:object):
        matchId_list = self._Endpoints.matchId_gen(data)
        match_nb = len(matchId_list)
        self.data_list = []
        for games in tqdm(range(match_nb - 1000, match_nb)):
            api_name = matchId_list[games]
            r = requests.get(
                api_name,
                headers={'X-Riot-Token': self.api_key}
            )
            if str(r) == '<Response [403]>':
                raise Exception('403 Forbidden, renew API key')
            else:
                matches = r.json()
                self.data_list.append(matches)
                time.sleep(1)
                games_df = pd.DataFrame.from_records(self.data_list)
                games_df.drop(['participantIdentities'], axis=1, inplace=True)
                games_df = games_df.explode('teams')
                games_df = df_explosion(games_df, 'teams')
                games_df.drop(['queueId', 
                'mapId', 
                'seasonId', 
                'gameVersion', 
                'gameMode', 
                'gameType', 
                'status', 
                'vilemawKills', 
                'dominionVictoryScore'
                ], inplace=True, axis=1, errors='ignore')
                data_win = games_df[games_df['win'] == 'Win']
                data_fail = games_df[games_df['win'] == 'Fail']
        return games_df