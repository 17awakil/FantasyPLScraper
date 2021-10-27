from getters import get_player
from getters import get_fixtures
import pandas as pd
import requests
import numpy as np

def get_player_summary(player_id):
    player = get_player(player_id)
    player_history = pd.DataFrame(player["history"])
    player_history["influence"] = pd.to_numeric(player_history.influence)
    player_history["creativity"] = pd.to_numeric(player_history.creativity)
    player_history["threat"] = pd.to_numeric(player_history.threat)
    player_history["ict_index"] = pd.to_numeric(player_history.ict_index)

    home_game_pts = player_history.loc[player_history['was_home'] == True].total_points.sum()
    away_game_pts = player_history.loc[player_history['was_home'] == False].total_points.sum()
    print("home_game_pts : ", home_game_pts)
    print("away_game_pts : ", away_game_pts)

    # Goals
    home_game_goals = player_history.loc[player_history['was_home'] == True].goals_scored.sum()
    away_game_goals = player_history.loc[player_history['was_home'] == False].goals_scored.sum()
    print("home_game_goals : ", home_game_goals)
    print("away_game_goals : ", away_game_goals)

    # Assists
    home_game_assists = player_history.loc[player_history['was_home'] == True].assists.sum()
    away_game_assists = player_history.loc[player_history['was_home'] == False].assists.sum()
    print("home_game_assists : ", home_game_assists)
    print("away_game_assists : ", away_game_assists)

    #ICT index
    home_ict = player_history.loc[player_history['was_home'] == True].ict_index.sum()
    away_ict = player_history.loc[player_history['was_home'] == False].ict_index.sum()
    print("home_ict : ", home_ict)
    print("away_ict : ", away_ict)
    return home_game_pts, away_game_pts, home_game_goals, away_game_goals, home_game_assists, away_game_assists, home_ict, away_ict

# print(get_player_summary(233))

def get_player_points(player_id):
    player = get_player(player_id)
    player_history = pd.DataFrame(player["history"])
    pts = player_history.total_points.sum()
    return pts


def get_player_goals(player_id):
    player = get_player(player_id)
    player_history = pd.DataFrame(player["history"])
    goals = player_history.goals_scored.sum()
    return goals

def get_player_assists(player_id):
    player = get_player(player_id)
    player_history = pd.DataFrame(player["history"])
    assists = player_history.assists.sum()
    return assists

def get_player_influence(player_id):
    player = get_player(player_id)
    player_history = pd.DataFrame(player["history"])
    player_history["influence"] = pd.to_numeric(player_history.influence)
    player_history["creativity"] = pd.to_numeric(player_history.creativity)
    player_history["threat"] = pd.to_numeric(player_history.threat)
    player_history["ict_index"] = pd.to_numeric(player_history.ict_index)
    influence = player_history.influence.sum()
    return influence
def get_player_threat(player_id):
    player = get_player(player_id)
    player_history = pd.DataFrame(player["history"])
    player_history["influence"] = pd.to_numeric(player_history.influence)
    player_history["creativity"] = pd.to_numeric(player_history.creativity)
    player_history["threat"] = pd.to_numeric(player_history.threat)
    player_history["ict_index"] = pd.to_numeric(player_history.ict_index)
    threat = player_history.threat.sum()
    return threat
def get_player_creativity(player_id):
    player = get_player(player_id)
    player_history = pd.DataFrame(player["history"])
    player_history["influence"] = pd.to_numeric(player_history.influence)
    player_history["creativity"] = pd.to_numeric(player_history.creativity)
    player_history["threat"] = pd.to_numeric(player_history.threat)
    player_history["ict_index"] = pd.to_numeric(player_history.ict_index)
    creativity = player_history.creativity.sum()
    return creativity
def get_player_ict_index(player_id):
    player = get_player(player_id)
    player_history = pd.DataFrame(player["history"])
    player_history["influence"] = pd.to_numeric(player_history.influence)
    player_history["creativity"] = pd.to_numeric(player_history.creativity)
    player_history["threat"] = pd.to_numeric(player_history.threat)
    player_history["ict_index"] = pd.to_numeric(player_history.ict_index)
    ict_index = player_history.ict_index.sum()
    return ict_index

def get_player_clean_sheets(player_id):
    pass

print(get_player_goals(233))
# get_player_summary(254) # salah
# get_player_summary(390) # son
# get_player_summary(388) # kane
# get_player_summary(202) # bamford
# get_player_summary(302) # bruno fernandes

player_id = 233
player = get_player(player_id)
player_history = pd.DataFrame(player["history"])
player_history.head()
fixtures = get_fixtures()
difficulties = []
for index, row in player_history.iterrows():
    fixture_num = row['fixture']
    fixture = next((item for item in fixtures if item["id"] == fixture_num), None)
    if row['was_home'] == True:
        difficulties.append(fixture['team_h_difficulty'])
    else:
        difficulties.append(fixture['team_a_difficulty'])
player_history['difficulty'] = difficulties
player_history.head(10)
print(player_history.pivot_table(index='difficulty',values='total_points',aggfunc=len))
print(player_history.pivot_table(index='difficulty',values='total_points',aggfunc=np.mean))

