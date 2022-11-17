#pip install nest-asyncio
#pip install pantheon

from pantheon import pantheon 
import asyncio
import nest_asyncio

nest_asyncio.apply()

#Define constant variables 
server = "euw1"
api_key = 'RGAPI-59012253-68f3-41ab-b530-eff473a83a00' #Need to request a new one

def requestsLog(url, status, headers):
    print(url)
    print(status)
    print(headers)

panth = pantheon.Pantheon(server, api_key, errorHandling=True, requestsLoggingFunction=requestsLog, debug=True)

async def getSummonerId(name):
    try:
        data = await panth.getSummonerByName(name)
        return (data['id'],data['accountId'])
    except Exception as e:
        print(e)


async def getRecentMatchlist(accountId):
    try:
        data = await panth.getMatchlist(accountId, params={"endIndex":30})
        return data
    except Exception as e:
        print(e)

async def getMatchAndTimeline(gameId):
    match,timeline = await asyncio.gather(*[
        panth.getMatch(gameId),
        panth.getTimeline(gameId)
    ])
    match['timeline'] = timeline
    return match

async def getRecentMatches(accountId):
    try:
        matchlist = await getRecentMatchlist(accountId)
        tasks = [panth.getMatch(match['gameId']) for match in matchlist['matches']]
        return await asyncio.gather(*tasks)
    except Exception as e:
        print(e)

#Summoner Name
name = "Not Waldo"

loop = asyncio.get_event_loop()  

----------------------------------------------------------
----------------------------------------------------------

#Check Account info
(summonerId, accountId) = loop.run_until_complete(getSummonerId('Not Waldo'))
print('Summoner ID= ', summonerId)
print('Account ID= ',accountId)

#Create loop to retrieve data from matches depending on number of matches 
(summonerId, accountId) = loop.run_until_complete(getSummonerId(name))
gamesDataRaw = loop.run_until_complete(getRecentMatches(accountId))

----------------------------------------------------------
----------------------------------------------------------
#Organize variables that we will be analizyng from extracted data requested from API


#Participant variable
def getParticipantfromAccountId(game,accountId):
  for participant in game ['participantIdentities']:
    if participant['player']['currentAccountId'] == accountId:
      return participant['participantId']
  
def getTeamAndChampion(game, participantId):
  
  for participant in game['participants']:
    if participant['participantId'] == participantId:
      return participant['teamId'], participant['championId'], participant['stats']['win']
 
        
def getTeamSide(teamId):
    if teamId == 100:
      return "Blue Side"
    elif teamId== 200:
      return "Red Side"        

        
def getWin(result):
    if result == True:
      return "Yes"
    elif result== False:
      return "No"
  
def getTeamFirst(game):
  for teams in game['teams']:
    return teams['firstBlood'],teams['firstInhibitor']

def getTeamNumberof(game):
  for teams in game['teams']:
    return teams['dragonKills'],teams['baronKills'],teams['riftHeraldKills'],teams['towerKills'], teams['inhibitorKills']


def getTeamComposition(game):
  compositions = {100:[],200:[]}

  for participant in game['participants']:
    compositions[participant['teamId']].append(participant['championId'])
  return compositions


def getPatch(game):
  return ".".join(game['gameVersion'].split(".")[:2])

import datetime

def getDate(game):
  return datetime.datetime.fromtimestamp(int(game['gameCreation']/1000)).strftime('%d/%m/%Y')

def getGameDuration(game):
  conversion = datetime.timedelta(seconds= game['gameDuration'])
  return str(conversion)

def getKDA(game,participantId):
   for participant in game['participants']:
    if participant['participantId'] == participantId:
      return participant['stats']['kills'], participant['stats']['deaths'], participant['stats']['assists']
  
def getCalculatedKDA(kills,deaths,assists):
  return (kills + assists)/ deaths    
 

def getTotaldamage(game,participantId):
   for participant in game['participants']:
    if participant['participantId'] == participantId:
      return participant['stats']['totalDamageDealt']

def getCreeps(game,participantId):
   for participant in game['participants']:
    if participant['participantId'] == participantId:
      return participant['stats']['neutralMinionsKilledTeamJungle'],participant['stats']['neutralMinionsKilledEnemyJungle'],participant['stats']['totalMinionsKilled'] 
  
def getTotalminions(game,participantId):
  jungle,enemyjungle,minions = getCreeps(game,participantId)
  return jungle+enemyjungle+minions

  
def getGoldPerMinute(game,participantId):
  for participant in game['participants']:
    if participant['participantId'] == participantId:
      if ("20-30" in  participant["timeline"]["goldPerMinDeltas"].keys()):
        return participant['timeline']['goldPerMinDeltas']['0-10'],participant['timeline']['goldPerMinDeltas']['10-20'],participant['timeline']['goldPerMinDeltas']['20-30']
      else:
        return participant['timeline']['goldPerMinDeltas']['0-10'],participant['timeline']['goldPerMinDeltas']['10-20'],"N/a"    
  
    
--------------------------------------------------------  
--------------------------------------------------------
#Putting all together

import requests, json

response = requests.get('https://ddragon.leagueoflegends.com/cdn/11.10.1/data/en_US/champion.json')
championRawData = json.loads(response.text)

championIdtoName = {}
for key,champion in championRawData['data'].items():
  championIdtoName[int(champion['key'])] = champion['name']

playerChampion = championIdtoName[championId]

teamComposition = [championIdtoName[chId] for chId in compositions[teamId]]
enemyteamComposition = [championIdtoName[chId] for chId in compositions[100 if teamId==200 else 200]]


gameInformationList = []
for game in gamesDataRaw:
  participantId = getParticipantfromAccountId(game, accountId)
  teamId, championId, win = getTeamAndChampion(game, participantId)
  compositions = getTeamComposition(game)
  kills, deaths,assists= getKDA(game,participantId)
  kda = getCalculatedKDA(kills,deaths,assists)
  jungle,enemyjungle,minions = getCreeps(game,participantId)
  firstBlood,firstInhibitor = getTeamFirst(game) 
  dragonKills,baronKills,heraldKills,towerKills,inhibitorKills=  getTeamNumberof(game)
  goldpermin0,goldpermin10,goldpermin20= getGoldPerMinute(game,participantId)
  
  #Select Info you want to show
  gameInformation={}
  gameInformation['Patch'] = getPatch(game)
  gameInformation['Date'] = getDate(game)
  gameInformation['Team Side'] = getTeamSide(teamId)
  gameInformation['Game Duration'] = getGameDuration(game)
  gameInformation['Champion'] = championIdtoName[championId]
  gameInformation['Win'] = getWin(win)
  gameInformation['Kills'] = kills
  gameInformation['Deaths'] = deaths
  gameInformation['Assists'] = assists
  gameInformation['KDA'] = kda
  gameInformation['Total Minions '] = getTotalminions(game,participantId) 
  gameInformation['Total Damage Dealt']= getTotaldamage(game,participantId)
  gameInformation['Team Composition'] = "/".join([championIdtoName[chId] for chId in compositions[teamId]])
  gameInformation['Enemy Team Composition'] = "/".join([championIdtoName[chId] for chId in compositions[100 if teamId==200 else 200]])
  gameInformation['First Blood'] = firstBlood
  gameInformation['First Inhibitor'] = firstInhibitor
  gameInformation['Dragons Killed'] = dragonKills
  gameInformation['Rift Herald Killed'] = heraldKills
  gameInformation['Barons Killed'] = baronKills
  gameInformation['Towers Killed'] = towerKills
  gameInformation['Inhibitors Killed'] = inhibitorKills
  gameInformation['Enemy Jungle Creeps']= enemyjungle
  gameInformation['Team Jungle Creeps'] = jungle
  gameInformation['Gold Per Minute 0-10']= goldpermin0
  gameInformation['Gold Per Minute 10-20']= goldpermin10
  gameInformation['Gold Per Minute 20-30']= goldpermin20
  #Add the rows to the list
  gameInformationList.append(gameInformation)


import pandas as pd

Fiddlesticks= pd.DataFrame(gameInformationList)
Fiddlesticks.to_csv('Fiddlesticks.csv')

Fiddlesticks.head(5)





















