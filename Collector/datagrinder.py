#!/usr/bin/python3
import pandas as pd 
import requests
import json
from tqdm import tqdm 
from time import sleep
import database.ldb_connector as ldb_connector
from collector.tools import flattenList
from collector.endpoints import Endpoints
from ratelimit import limits, sleep_and_retry


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
        self.mongo = ldb_connector.MongoCollection()

    @sleep_and_retry
    @limits(calls=0.05, period=1)
    def api_call(self, url):
        try:
            r = requests.get(
                url,
                headers={'X-Riot-Token': self.api_key}
                )
            if (r.status_code != 200):
                raise Exception
        except:
            if (r.status_code == 429):
                print('\nCatched exception API Response: {} Sleeping...'.format(r.status_code))
                sleep(5)
                self.api_call(url)
            elif (r.status_code == 403):
                self.api_key = input('\nPlease update API key:')
                self.api_call(url)
        return r

    def ranked_5x5_data(self):
        rank_nb = len(self._Endpoints.ranked_solo_gen())
        for i in tqdm(range(rank_nb)):
            api_name = self._Endpoints.ranked_solo_gen()[i]
            r = self.api_call(api_name)
            summoners = r.json()
            self.data_list.append(summoners)
        df = pd.DataFrame.from_records(flattenList(self.data_list))
        df.drop(['queueType', 
        'summonerName', 
        'leagueId', 
        'hotStreak',
        'miniSeries',
        'freshBlood',
        'inactive'], axis=1, inplace=True, errors='ignore')
        df['winRatio'] = (df['wins'] / (df['wins'] + df['losses']))
        post_data_s = df.to_dict("records")
        with self.mongo:
            collection = self.mongo.connection.leagueai.ranked_5x5_tiers
            collection.insert_many(post_data_s)
        summonerId_list = self._Endpoints.playerId_gen(df)
        summ_nb = len(summonerId_list)
        self.data_list = []
        for summs in tqdm(range(summ_nb)):
            api_name = summonerId_list[summs]
            r = self.api_call(api_name)
            accounts = r.json()
            print(accounts)
            self.data_list.append(accounts)
            temp_df = pd.DataFrame.from_records(self.data_list)
            df[['accountId', 'summonerLevel']] = temp_df[['accountId', 'summonerLevel']]
            del temp_df
            post_data = json.dumps(accounts)
            post_data = json.loads(post_data)
            with self.mongo:
                collection = self.mongo.connection.leagueai.ranked_5x5
                collection.insert_one(post_data)
        return df

    def match_data_players(self, data:object):
        accountId_list = self._Endpoints.matchId_list_gen(data)
        player_nb = len(accountId_list)
        self.data_list = []
        for accs in tqdm(range(player_nb)):
            api_name = accountId_list[accs]
            r = self.api_call(api_name)
            matches = r.json()
            self.data_list.append(matches)
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
        'profileIconId',
        'revisionDate', 
        'summonerLevel'], axis=1, inplace=True, errors='ignore')
        return match_df

    def match_data(self, data:object):
        matchId_list = self._Endpoints.matchId_gen(data)
        match_nb = len(matchId_list)
        df = pd.DataFrame()
        for games in tqdm(range(match_nb - 1000, match_nb)):
            api_name = matchId_list[games]
            r = self.api_call(api_name)
            matches = r.json()
            games_df = pd.json_normalize(matches)
            df = df.append(games_df, ignore_index=True)
        df = df.explode('teams')
        df.drop(['platformId', 
        'gameCreation', 
        'gameDuration', 
        'queueId', 
        'mapId', 
        'seasonId', 
        'gameVersion', 
        'gameMode', 
        'gameType', 
        'status.status_code', 
        'status.message'], inplace=True, axis=1, errors='ignore')
        df = pd.concat([df.drop(['teams'], axis=1), df['teams'].apply(pd.Series)], axis=1)
        df.drop(['dominionVictoryScore',
        'vilemawKills'
        ], inplace=True, axis=1, errors='ignore')
        data_win = df[df['win'] == 'Win']
        data_fail = df[df['win'] == 'Fail']
        data_part_w = data_win[['gameId', 'participants']]
        data_part_f = data_fail[['gameId', 'participants']]
        data_part_w = data_part_w.explode('participants')
        data_part_f = data_part_f.explode('participants')
        data_part_w = pd.concat([data_part_w.drop(['participants'], axis=1), data_part_w['participants'].apply(pd.Series)], axis=1)
        data_part_f = pd.concat([data_part_f.drop(['participants'], axis=1), data_part_f['participants'].apply(pd.Series)], axis=1)
        return data_win, data_fail, data_part_w, data_part_f
