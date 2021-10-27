import requests
import json
import pprint
import math

def get_data():
    """ Retrieve the fpl player data from the hard-coded url """
    response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
    if response.status_code != 200:
        raise Exception("Response was code " + str(response.status_code))
    return response.json()

def get_top_managers(league_id, num_managers):
    """ Get top managers """
    pp =pprint.PrettyPrinter(indent=4)
    url = "https://fantasy.premierleague.com/api/leagues-classic/"+str(league_id)+"/standings/"
    num_pages = math.ceil(num_managers / 50) + 1
    print(num_pages)
    result = []
    for i in range(1,num_pages):
        print("i", i)
        url_with_page = url + "?page_standings="+str(i)
        response = requests.get(url_with_page)
        pp.pprint(response.text)
        result.append(response.json())
    return result
    
def get_user(user_id):
    """ Get user """
    url = "https://fantasy.premierleague.com/api/entry/"+str(user_id)+"/"
    response = requests.get(url)
    return response.json()
    
def get_picks(user_id, gameweek):
    """ Get team picks for a specified gameweek """
    url = "https://fantasy.premierleague.com/api/entry/"+str(user_id)+"/event/"+str(gameweek)+"/picks/"
    response = requests.get(url)
    return response.json()

def get_player(player_id):
    """ Get player's summary """
    url = "https://fantasy.premierleague.com/api/element-summary/"+str(player_id)+"/"
    response = requests.get(url)
    return response.json()

def get_fixtures():
    """ Get player's summary """
    url = "https://fantasy.premierleague.com/api/fixtures/"
    response = requests.get(url)
    return response.json()




