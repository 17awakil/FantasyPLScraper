import json
import urllib
import pymongo
from pymongo import MongoClient
import urllib.parse
import getters
import pprint
from config import mongo_user, mongo_password

password = urllib.parse.quote_plus(mongo_password) # TODO: hide password credentials
uri = "mongodb+srv://"+mongo_user+":"+password+"@cluster0.yc0gv.mongodb.net/fpl?retryWrites=true&w=majority"
client = pymongo.MongoClient(uri)
db = client['fpl']
seasons_collection = db['seasons']
players_history_collection = db['2020/2021-players-history']
fixtures_collection = db['fixtures-2020/2021']
players_history_merged_with_understat = db['2020/2021-merged-players-history']
understat_players_collection = db["understat-players-2020/2021"]
# Inserts

def insert_current_season():
    data = getters.get_data()
    data["_id"] = "2020/2021" # TODO : change season automatically
    # print(type(data))
    # print(data["_id"])
    seasons_collection.insert_one(data)

def insert_all_players_summary():
    data = getters.get_data()
    for player in data["elements"]:
        # print(player["first_name"] + " " + player["second_name"] + " " + str(player["id"]))
        id = player["id"]
        player_json = getters.get_player(id)
        player_json["_id"] = id 
        players_history_collection.insert_one(player_json)

def insert_fixtures():
    fixtures = getters.get_fixtures()
    for fixture in fixtures:
        fixture["_id"] = fixture["id"]
        fixtures_collection.insert_one(fixture)

def insert_merged_player_history(history):
    players_history_merged_with_understat.insert_one(history)
    # players_history_merged_with_understat.update_one(history, upsert=True,)

def insert_understat_player_data(player_data):
    understat_players_collection.insert_one(player_data)

# Getters

def get_all_players_summary():
    players = players_history_collection.find({}) # get all documents from collection
    count = 0
    players_list = []
    elements = seasons_collection.find_one()['elements']
    for player in players:
        id = player['_id']
        player_element = [element for element in elements if element["id"] == id][0]
        # print(player_element["web_name"])
        # print(player_element["first_name"], player_element["second_name"])
        # players_history_collection.update_one
        count += 1
        players_list.append(player_element)
    print(count)
    return players_list

def get_teams(season):
    season_document = seasons_collection.find_one({"_id" : season})
    return season_document["teams"]

def get_team_names(season):
    season_document = seasons_collection.find_one({"_id" : season})
    return [team["name"] for team in season_document["teams"]]

def get_player_history(id):
    player_history = players_history_collection.find_one({"_id": id})
    return player_history
