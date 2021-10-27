from bs4 import BeautifulSoup
import lxml
import requests
import re
import codecs
import pandas as pd
import os
import json
import pprint
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from mongo import get_all_players_summary, get_teams, get_player_history, insert_merged_player_history, insert_understat_player_data
import pprint
import unidecode
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Getters

def get_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Response was code " + str(response.status_code))
    html = response.text
    parsed_html = BeautifulSoup(html, 'html.parser')
    scripts = parsed_html.findAll('script')
    filtered_scripts = []
    for script in scripts:
        if len(script.contents) > 0:
            filtered_scripts += [script]
    return scripts

def get_epl_data(season):
    year = season.split("/")[0]
    scripts = get_data("https://understat.com/league/EPL/"+year)
    teamData = {}
    playerData = {}
    datesData = {}
    for script in scripts:
        for c in script.contents:
            split_data = c.split('=')
            data = split_data[0].strip()
            if data == 'var teamsData':
                content = re.findall(r'JSON\.parse\(\'(.*)\'\)',split_data[1])
                decoded_content = codecs.escape_decode(content[0], "hex")[0].decode('utf-8')
                teamData = json.loads(decoded_content)
            elif data == 'var playersData':
                content = re.findall(r'JSON\.parse\(\'(.*)\'\)',split_data[1])
                decoded_content = codecs.escape_decode(content[0], "hex")[0].decode('utf-8')
                playerData = json.loads(decoded_content)
            elif data == 'var datesData':
                content = re.findall(r'JSON\.parse\(\'(.*)\'\)',split_data[1])
                decoded_content = codecs.escape_decode(content[0], "hex")[0].decode('utf-8')
                datesData = json.loads(decoded_content)
    return teamData, playerData, datesData

def get_player_data(id):
    scripts = get_data("https://understat.com/player/" + str(id))
    groupsData = {}
    matchesData = {}
    shotsData = {}
    minMaxPlayerStats = {}
    for script in scripts:
        for c in script.contents:
            split_data = c.split('=')
            data = split_data[0].strip()
            if data == 'var groupsData':
                content = re.findall(r'JSON\.parse\(\'(.*)\'\)',split_data[1])
                decoded_content = codecs.escape_decode(content[0], "hex")[0].decode('utf-8')
                groupsData = json.loads(decoded_content)
            elif data == 'var matchesData':
                content = re.findall(r'JSON\.parse\(\'(.*)\'\)',split_data[1])
                decoded_content = codecs.escape_decode(content[0], "hex")[0].decode('utf-8')
                matchesData = json.loads(decoded_content)
            elif data == 'var shotsData':
                content = re.findall(r'JSON\.parse\(\'(.*)\'\)',split_data[1])
                decoded_content = codecs.escape_decode(content[0], "hex")[0].decode('utf-8')
                shotsData = json.loads(decoded_content)
            elif data == 'var minMaxPlayerStats':
                content = re.findall(r'JSON\.parse\(\'(.*)\'\)',split_data[1])
                decoded_content = codecs.escape_decode(content[0], "hex")[0].decode('utf-8')
                minMaxPlayerStats = json.loads(decoded_content)
    return groupsData, matchesData, shotsData, minMaxPlayerStats

def get_players_understat():
    player_summaries = get_all_players_summary() # all players from FPL season to loop through
    team_list = get_teams('2020/2021') # list of teams in FPL for given season

    # Set up selenium webdriver
    PATH = "C:\Program Files (x86)\chromedriver.exe"
    driver = webdriver.Chrome(PATH)

    # Go to website
    driver.get("https://understat.com")
    pp = pprint.PrettyPrinter(indent=3)
    count = 0
    missing_players = []
    for player in player_summaries:
        player_id_fpl = player["id"]
        player_history_fpl = get_player_history(player_id_fpl)
        player_team_name = normalize_fpl_team_name_to_understat(team_list[player['team']-1]['name'])
        # Finds the corresponding player's understat ID
        player_id_understat = get_understat_player_id(driver, 
                                            unidecode.unidecode(player["web_name"]), 
                                            unidecode.unidecode(player["first_name"]), 
                                            unidecode.unidecode(player["second_name"]), 
                                            player_team_name,
                                            "2020/2021")
        print(player['web_name'], player_id_understat)
        if player_id_understat:
            count += 1
            print(count)
            player_understat_data = get_player_data(player_id_understat) 
            matches_data = player_understat_data[1]
            player['team_name'] = player_team_name # Set player's team name in fpl object
            player_history_fpl["understat_id"] = player_id_understat
            games_played_last_season_understat = [game for game in matches_data if game["season"] == '2020']
            for fixture in player_history_fpl['history']:
                # Find corresponding fixture in uderstat to link the data together by using the date of the fixture
                fixture_date = fixture['kickoff_time'].split("T")[0]
                fixture_understat = next((game for game in games_played_last_season_understat if game["date"] == fixture_date), None)
                if fixture_understat:
                    fixture['xG'] = fixture_understat['xG']
                    fixture['xA'] = fixture_understat['xA']
                    fixture['shots'] = fixture_understat['shots']
                    fixture['key_passes'] = fixture_understat['key_passes']
                    fixture['npg'] = fixture_understat['npg']
                    fixture['npxG'] = fixture_understat['npxG']
                    fixture['xGChain'] = fixture_understat['xGChain']
                    fixture['xGBuildup'] = fixture_understat['xGBuildup']
                else:
                    fixture['xG'] = 0
                    fixture['xA'] = 0
                    fixture['shots'] = 0
                    fixture['key_passes'] = 0
                    fixture['npg'] = 0
                    fixture['npxG'] = 0
                    fixture['xGChain'] = 0
                    fixture['xGBuildup'] = 0
                fixture['opponent_team_name'] = team_list[fixture['opponent_team']-1]['name']
            insert_merged_player_history(player_history_fpl)
        else:
            missing_players.append(player["web_name"])
            print("number of missing players: ", len(missing_players))

    print("total players retrieved ", count)        
    # Close webdriver
    driver.quit()

def get_understat_player_id(driver, web_name, first_name, last_name, team_name, season):
    # Identify search box element
    search = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, 'typeahead')))

    full_name = shorten_player_full_name(first_name + " " + last_name)
    # First, try searching for player with web name
    search.send_keys(web_name) # Search for most common name of player
    try:
        suggestions = WebDriverWait(driver,2).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'tt-suggestion  ')))
        for suggestion in suggestions:
            suggestion_player_text = suggestion.text.split("\n")[0]
            suggestion_team_text = suggestion.text.split("\n")[1]
            if (
                (suggestion_team_text == team_name 
                and
                (fuzz.ratio(suggestion_player_text, web_name) > 90 
                or fuzz.ratio(suggestion_player_text, full_name) > 90 
                )
                )
                or did_player_play_for_team_in_given_season(suggestion_player_text, suggestion_team_text, team_name, season)):
                suggestion.click()
                id = driver.current_url.split("/")[-1]
                return id
    except Exception:
        print("Could not retrieve player through web name : ", web_name)
    finally:        
        search = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, 'typeahead')))
        search.send_keys(Keys.CONTROL + "a")
        search.send_keys(Keys.DELETE)

    # Otherwise, search with first name first
    search.send_keys(shorten_player_first_name(first_name))
    try:
        suggestions = WebDriverWait(driver,2).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'player-name')))
        for suggestion in suggestions:
            suggestion_team = suggestion.find_element_by_xpath('//small[1]')
            if suggestion_team.text == team_name or fuzz.ratio(suggestion.text, web_name) > 90 or fuzz.ratio(suggestion.text, full_name) > 90:
                suggestion.click()
                id = driver.current_url.split("/")[-1]
                return id
        search.send_keys(" " + shorten_player_last_name(last_name))
        suggestions = WebDriverWait(driver,2).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'player-name')))
        for suggestion in suggestions:
            suggestion_team = suggestion.find_element_by_xpath('//small[1]')
            if suggestion_team.text == team_name or fuzz.ratio(suggestion.text, web_name) > 90 or fuzz.ratio(suggestion.text, full_name) > 90:
                suggestion.click()
                id = driver.current_url.split("/")[-1]
                return id
    except Exception:
        print("Could not retrieve player through first and last name : ", full_name)   
    finally:
        search = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, 'typeahead')))
        search.send_keys(Keys.CONTROL + "a")
        search.send_keys(Keys.DELETE)
    
    # Otherwise, search with last name (last resort)
    
    search.send_keys(shorten_player_last_name(last_name))
    try:
        suggestions = WebDriverWait(driver,2).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'player-name')))
        for suggestion in suggestions:
            suggestion_team = suggestion.find_element_by_xpath('//small[1]')
            if suggestion_team.text == team_name or fuzz.ratio(suggestion.text, full_name) > 90 or fuzz.ratio(suggestion.text, web_name) > 90 or fuzz.ratio(suggestion.text, last_name) > 90:
                suggestion.click()
                id = driver.current_url.split("/")[-1]
                return id
    except Exception:
        print("Could not retrieve player through last name : ", last_name)    
    finally:
        search = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, 'typeahead')))
        search.send_keys(Keys.CONTROL + "a")
        search.send_keys(Keys.DELETE)
    
    # TODO: if player leaves to a different team 
    # TODO: if player has long name (usually spanish or portuguese)
    # TODO: make sure you don't pick up the wrong player with same name (Neto (Barcelona) and Pedro Neto(Wolves))
    return None # No player ID found

# def get_team_data():

# Helper functions

def find_player_id_by_name(driver, name, full_name, team_name, season):
    # Identify search box element
    search = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, 'typeahead')))

    # First, try searching for player with web name
    search.send_keys(name) # Search for most common name of player
    try:
        suggestions = WebDriverWait(driver,2).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'tt-suggestion  ')))
        for suggestion in suggestions:
            suggestion_player_text = suggestion.text.split("\n")[0]
            suggestion_team_text = suggestion.text.split("\n")[1]
            if (
                (suggestion_team_text == team_name 
                and
                (fuzz.ratio(suggestion_player_text, name) > 90 
                or fuzz.ratio(suggestion_player_text, full_name) > 90 
                )
                )
                or did_player_play_for_team_in_given_season(suggestion_player_text, suggestion_team_text, team_name, season)):
                suggestion.click()
                id = driver.current_url.split("/")[-1]
                return id
    except Exception:
        print("Could not retrieve player through name : ", name)
    finally:        
        search = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, 'typeahead')))
        search.send_keys(Keys.CONTROL + "a")
        search.send_keys(Keys.DELETE)
    return None

def find_player_id_by_full_name(driver, web_name, first_name, last_name, team_name, season):
    # Otherwise, search with first name first
    full_name = shorten_player_full_name(first_name + " " + last_name)
    search = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, 'typeahead')))
    search.send_keys(shorten_player_first_name(first_name))
    try:
        suggestions = WebDriverWait(driver,2).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'tt-suggestion')))
        for suggestion in suggestions:
            suggestion_player_text = suggestion.text.split("\n")[0]
            suggestion_team_text = suggestion.text.split("\n")[1]
            if (
                (suggestion_team_text == team_name 
                and
                (fuzz.ratio(suggestion_player_text, web_name) > 90 
                or fuzz.ratio(suggestion_player_text, full_name) > 90 
                )
                )
                or did_player_play_for_team_in_given_season(suggestion_player_text, suggestion_team_text, team_name, season)):
                suggestion.click()
                id = driver.current_url.split("/")[-1]
                return id
        search.send_keys(" " + shorten_player_last_name(last_name))
        suggestions = WebDriverWait(driver,2).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'tt-suggestion')))
        for suggestion in suggestions:
            suggestion_player_text = suggestion.text.split("\n")[0]
            suggestion_team_text = suggestion.text.split("\n")[1]
            if (
                (suggestion_team_text == team_name 
                and
                (fuzz.ratio(suggestion_player_text, web_name) > 90 
                or fuzz.ratio(suggestion_player_text, full_name) > 90 
                )
                )
                or did_player_play_for_team_in_given_season(suggestion_player_text, suggestion_team_text, team_name, season)):
                suggestion.click()
                id = driver.current_url.split("/")[-1]
                return id
    except Exception:
        print("Could not retrieve player through first and last name : ", full_name)   
    finally:
        search = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, 'typeahead')))
        search.send_keys(Keys.CONTROL + "a")
        search.send_keys(Keys.DELETE)
    return None

def normalize_fpl_team_name_to_understat(team_name):
    if team_name == "Man City":
        return "Manchester City"
    elif team_name == "Man Utd":
        return "Manchester United"
    elif team_name == "Newcastle":
        return "Newcastle United"
    elif team_name == "Sheffield Utd":
        return "Sheffield United"
    elif team_name == "Spurs":
        return "Tottenham"
    elif team_name == "West Brom":
        return "West Bromwich Albion"
    elif team_name == "Wolves":
        return "Wolverhampton Wanderers"
    else:
        return team_name
# For long full names, take first name and last name in list of names
def shorten_player_full_name(full_name):
    names = full_name.split()
    if len(names) > 2:
        return names[0] + " " + names[-1]
    else:
        return full_name

def shorten_player_first_name(first_name):
    names = first_name.split()
    return names[0]

def shorten_player_last_name(last_name):
    names = last_name.split()
    return names[-1]


# Checks if the suggested player was part of the team in the season in question
# suggested_player_name
# suggested_team_name
# team_name should be in understat format (i.e. Tottenham instead of Spurs)
# season should be of the form "2020/2021"
def did_player_play_for_team_in_given_season(suggested_player_name, suggested_team_name, team_name, season):
    PATH = "C:\Program Files (x86)\chromedriver.exe"
    try:
        driver = webdriver.Chrome(PATH)
        # Go to website
        driver.get("https://understat.com")
        # Identify search box element
        search = WebDriverWait(driver,1.5).until(EC.presence_of_element_located((By.CLASS_NAME, 'typeahead')))

        search.send_keys(suggested_player_name) # Search for most common name of player
        suggestions = WebDriverWait(driver,2).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'tt-suggestion')))
        id = -1
        for suggestion in suggestions:
            suggestion_player_text = suggestion.text.split("\n")[0]
            suggestion_team_text = suggestion.text.split("\n")[1]
            if suggestion_player_text == suggested_player_name and suggestion_team_text == suggested_team_name:
                suggestion.click()
                id = driver.current_url.split("/")[-1]
                break
        
        if id != -1:
            groups_data = get_player_data(id)[0]
            seasons = groups_data['season']
            year = season.split("/")[0]
            return next((season for season in seasons if season["team"] == team_name and season["season"] == year), None) != None
        else:
            return False
    except Exception as e:
        print("Error encountered: ", e)
        return False
    finally:
        driver.quit()

# print(did_player_play_for_team_in_given_season("Neto", "Barcelona", "Wolves", "2020/2021"))
# print(did_player_play_for_team_in_given_season("Pedro Neto", "Wolverhampton Wanderers", "Wolverhampton Wanderers", "2020/2021"))
# print(did_player_play_for_team_in_given_season("Mohamed Salah", "Liverpool", "Liverpool", "2020/2021"))
# print(did_player_play_for_team_in_given_season("Mohamed Salah", "Liverpool", "Chelsea", "2014/2015"))
# print(did_player_play_for_team_in_given_season("Shkodran Mustafi", "Schalke 04", "Arsenal", "2020/2021"))
# print(did_player_play_for_team_in_given_season("Shkodran Mustafi", "Schalke 04", "Arsenal", "2021/2022"))

# get_players_understat()

# get_player_data(1699)
PATH = "C:\Program Files (x86)\chromedriver.exe"
# driver = webdriver.Chrome(PATH)

# Go to website
# driver.get("https://understat.com")
# print(fuzz.ratio("Ahmed Hegazy", "Ahmed Hegazi"))
# print(get_understat_player_id(driver, "Hegazi", "Ahmed", "Hegazi", "West Bromwich Albion", "2020/2021"))
# print(get_understat_player_id(driver, "Smith Rowe", "Emile", "Smith Rowe", "Arsenal", "2020/2021")) # 7230
# print(get_understat_player_id(driver, "Mustafi", "Shkodran", "Mustafi", "Arsenal", "2020/2021")) # 1699
# print(get_understat_player_id(driver, "Son", "Heung-Min", "Son", "Tottenham", "2020/2021"))
# print(get_understat_player_id(driver, "Kante", "N'Golo", "Kante", "Chelsea", "2020/2021")) # 751
# print(get_understat_player_id(driver, "Patricio", "Rui Pedro", "dos Santos Patricio", "Wolverhampton Wanderers", "2020/2021"))
# print(get_understat_player_id(driver, "Semedo", "Nelson", "Cabral Semedo", "Wolverhampton Wanderers", "2020/2021")) # 6163
# print(get_understat_player_id(driver, "Aubameyang", "Pierre-Emerick", "Aubameyang", "Arsenal", "2020/2021")) # 318
# print(get_understat_player_id(driver, "Salah", "Mohamed", "Salah", "Liverpool", "2020/2021")) # 1250

#Rui Pedro dos Santos Patricio (Rui Patricio) not found, Nelson Cabral Semedo, Wrong Neto selected, Neto instead of Pedro Neto,Ruben Diogo da Silva Neves not found
# print(shorten_player_first_name("Rui Pedro"))
# print(shorten_player_last_name("dos Santos Patricio"))
# print(find_player_id_by_full_name(driver,"Salah", "Mohamed", "Salah", "Liverpool", "2020/2021"))
# print(find_player_id_by_name(driver,"Salah", "Mohamed Salah", "Liverpool", "2020/2021"))
def get_players_data_understat():
    players = get_epl_data("2020/2021")[1]
    for player in players:
        player["_id"] = player["id"]
        del player["id"]
        insert_understat_player_data(player)


# get_players_data_understat()