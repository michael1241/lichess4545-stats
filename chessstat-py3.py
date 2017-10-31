#! /usr/bin/env python

#stats: biggest upset, combined and individual low and high acpl, longest, shortest, fastest mate.
import urllib.request, urllib.parse, urllib.error
import requests
import lxml.html
import time
import json
import sys
from functools import reduce

LEAGUE = sys.argv[1] # team4545 or lonewolf
SEASON = sys.argv[2]
ROUNDNUMS = eval(sys.argv[3]) # tuple of round number(s) e.g (1,2) is round 1 and (1,9) is rounds 1 to 8
if len(sys.argv) == 5:
    EXCLUDE = sys.argv[4].split(",") # players to exclude from results in list format playerx,playery,playerz
else:
    EXCLUDE = []

GAMESFILENAME = "{0}GamesS{1}R{2}".format(LEAGUE, SEASON, ROUNDNUMS) 
LICHESSURL = "https://en.lichess.org/"

# setting the correct xpath to get game links from team4545 or lonewolf areas of lichess4545.com website
if LEAGUE == "team4545":
    XPATHCLASS = "cell-game-result"
elif LEAGUE == "lonewolf":
    XPATHCLASS = "text-center text-nowrap"

def gameList():
    # build list of gameIDs from the round(s) by scraping lichess4545.com website
    gameIDs = []
    print("Getting games for rounds {0} to {1}".format(ROUNDNUMS[0],ROUNDNUMS[1]))
    for roundnum in range(ROUNDNUMS[0], ROUNDNUMS[1]):
        connection = urllib.request.urlopen('https://www.lichess4545.com/{0}/season/{1}/round/{2}/pairings/'.format(LEAGUE, SEASON, roundnum))
        dom =  lxml.html.fromstring(connection.read())
        for link in dom.xpath('//td[@class="{0}"]/a/@href'.format(XPATHCLASS)):
            gameIDs.append(link[-8:])
    return gameIDs

def getGames(gameIDs):
    # get game data from games listed in gameIDs using lichess.org API
    games = {}
    for num,gameid in enumerate(gameIDs):
        response = requests.get("https://en.lichess.org/api/game/{0}?with_analysis=1&with_movetimes=1&with_opening=1&with_moves=1".format(gameid))
        games[gameid] = json.loads(response.text)
        time.sleep(1) # wait to prevent server overload
        print("got game", num)
    return games

# get games in dictionary format - from file if present in working directory or lichess.org if not
gameIDs = gameList()
try:
    infile = open(GAMESFILENAME,'r')
    games = json.load(infile)
    infile.close()
    newgames = set(gameIDs) - set(games.keys())
    if newgames:
        games.update(getGames(newgames))
        outfile = open(GAMESFILENAME, 'w')
        json.dump(games, outfile, indent=4)
        print("This data was updated with:", newgames)
    print("This data was read from file.")
except Exception as e:
    print(e)
    games = getGames(gameIDs)
    outfile = open(GAMESFILENAME,'w')
    json.dump(games, outfile, indent=4)
    print("This data was fetched from web.")
    outfile.close()

# exclude listed players' games from stats results e.g. for cheater games
gamevalues = []
for game in list(games.values()):
    if game["players"]["white"]["userId"] not in EXCLUDE and game["players"]["black"]["userId"] not in EXCLUDE:
        gamevalues.append(game)
    else:
        print("{0} removed".format(game["id"]))

# get stats for ACPL high low both individual and combined
def getACPL():
    maxi = 0
    mini = 1000
    combmaxi = 0
    combmini = 1000
    wbmaxigame = []
    wbminigame = []
    combmaxigame = []
    combminigame = []
    for game in gamevalues:
        try:
            whiteacpl = game.get('players').get('white').get('analysis').get('acpl')
            blackacpl = game.get('players').get('black').get('analysis').get('acpl')
        except AttributeError:
            print("No analysis for {0}{1}".format(LICHESSURL, game.get('id')))
            continue
        combacpl = whiteacpl + blackacpl
        wbmaxi = max(whiteacpl, blackacpl)
        wbmini = min(whiteacpl, blackacpl)
        
        if wbmaxi > maxi:                       #maximum individual ACPL
            maxi = wbmaxi
            wbmaxigame = [game.get('id')]
        elif wbmaxi == maxi:
            wbmaxigame.append(game.get('id'))
        if wbmini < mini:                       #minimum individual ACPL
            mini = wbmini
            wbminigame = [game.get('id')]
        elif wbmini == mini:
            wbminigame.append(game.get('id'))
        if combacpl > combmaxi:                 #maximum combined ACPL
            combmaxi = combacpl
            combmaxigame = [game.get('id')]
        elif combacpl == combmaxi:
            combmaxigame.append(game.get('id'))
        if combacpl < combmini:                 #minimum combined ACPL
            combmini = combacpl
            combminigame = [game.get('id')]
        elif combacpl == combmini:
            combminigame.append(game.get('id'))
    return maxi, wbmaxigame, mini, wbminigame, combmaxi, combmaxigame, combmini, combminigame

# get longest games
def getTurns():
    maxturnIDs = []
    maxturns =  max([(game['turns']) for game in gamevalues])
    for game in gamevalues:
        if game['turns'] == maxturns:
            maxturnIDs.append(game['id'])
    return maxturns, maxturnIDs

# get biggest match upset by rating difference
def getUpset():
    maxiupset = 0
    upset = 0
    upsetIDs = []
    swapdict = {"white":"black","black":"white"}
    for game in gamevalues:
        if game['status'] == 'draw':
            continue
        currentupset = (game['players'][swapdict[game['winner']]]['rating'] - game['players'][game['winner']]['rating']) if 'winner' in game else -1
        if currentupset > maxiupset:
            maxiupset = currentupset
            upset = currentupset
            upsetIDs = [game['id']]
        elif currentupset == maxiupset:
            upsetIDs.append(game['id'])
    return upset, upsetIDs

# get shortest mate/resign/draw
def getQuickGame(finish):
    try:
        minfinIDs = []
        minfin =  min([(game['turns']) for game in gamevalues if game['status'] == finish])
        for game in gamevalues:
            if game['status'] == finish and game['turns'] == minfin:
                minfinIDs.append(game['id'])
        return minfin, minfinIDs
    except ValueError:
        return "not", ["N/A"]

# convert lichess 1/100ths of a second into easily readable format
def convert(time):
    minutes = time // 6000
    seconds = round(((((time / 6000.0) - minutes))*60),0)
    return  str(minutes) + " minutes " + str(seconds) + " seconds"

def timeStats():
    if LEAGUE == "team4545":
        start_time = 45*60*100
        increment = 45*100
    elif LEAGUE == "lonewolf":
        start_time = 30*60*100
        increment = 30*100

    maxi_remain = 0
    maxi_remainIDs = []

    maxi_think = 0
    maxi_thinkIDs = []
    maxi_move = []

    maxi_spent = 0
    maxi_spentIDs = []
    for game in gamevalues:
        try:
            whitetimes = game.get('players').get('white').get('moveCentis')
            blacktimes = game.get('players').get('black').get('moveCentis')
        except AttributeError:
            print("No movetimes for {0}{1}".format(LICHESSURL, game.get('id')))
            continue
        if len(whitetimes) == len(blacktimes):
            last_move = "black"
        else:
            last_move = "white"
        times = (whitetimes,blacktimes)
        for c, colour in enumerate(times):
            for move, time in enumerate(colour):
                if time > maxi_think:
                    maxi_think = time
                    maxi_thinkIDs = [game.get('id')]
                    maxi_move = [move+1]
                elif time == maxi_think:
                    maxi_thinkIDs.append(game.get('id'))
                    maxi_move.append(move+1)
            remain = (start_time) - reduce(lambda x, y: x+(y-(increment)), colour)
            if c == 0 and last_move == "white":
                remain -= increment
            if c == 1 and last_move == "black":
                remain -= increment
            if remain > maxi_remain:
                maxi_remain = remain
                maxi_remainIDs = [game.get('id')]
            elif remain == maxi_remain:
                maxi_remainIDs.append(game.get('id'))

            spent = reduce(lambda x, y: x+y, colour)
            if spent > maxi_spent:
                maxi_spent = spent
                maxi_spentIDs = [game.get('id')]
            elif spent == maxi_spent:
                maxi_spentIDs.append(game.get('id'))
    maxi_spent = convert(maxi_spent)
    maxi_remain = convert(maxi_remain) 
    maxi_think = convert(maxi_think)
    return maxi_think, maxi_thinkIDs, maxi_move, maxi_remain, maxi_remainIDs, maxi_spent, maxi_spentIDs

#eval based stats - in progress
def getBlunder():
    blunder = 0
    blunderIDs = []
    for game in gamevalues:
        evals = []
        for ev in game["analysis"]:
            if "eval" in ev:
                evals.append(ev.get("eval"))
            else:
                mate = ev.get("mate") * 100 #adjust weighting of mate to eval
                sign = mate//abs(mate)
                mate += 6000 * sign
                evals.append(mate)
        gameblunders = [abs(x - y) for (x, y) in zip(evals[1:], evals[:-1])]
        gameblundermove = max(range(len(gameblunders)), key=gameblunders.__getitem__)
        gameblunder = max(gameblunders)
        if gameblunder > blunder:
            blunder = gameblunder
            blunderIDs = [game.get('id'), gameblundermove]
        elif gameblunder == blunder:
            blunderIDs.append(game.get('id'), gameblundermove)
    return blunder, blunderIDs
#print(getBlunder())


# assigning variables for formatting
upset, upsetIDs = getUpset()
minmate, minmateIDs = getQuickGame("mate")
mindraw, mindrawIDs = getQuickGame("draw")
minresign, minresignIDs = getQuickGame("resign")
maxturns, maxturnIDs = getTurns()
maxi, wbmaxigame, mini, wbminigame, combmaxi, combmaxigame, combmini, combminigame = getACPL()
maxi_think, maxi_thinkIDs, maxi_move, maxi_remain, maxi_remainIDs, maxi_spent, maxi_spentIDs = timeStats()

for stat in [upsetIDs, minmateIDs, mindrawIDs, minresignIDs, maxturnIDs, wbmaxigame, wbminigame, combmaxigame, combminigame, maxi_thinkIDs, maxi_remainIDs, maxi_spentIDs]:
    for n, game in enumerate(stat):
        stat[n] = LICHESSURL + game

print("The fastest mate was {0} found in game ID {1}.".format(minmate, ", ".join(minmateIDs)))
print("The fastest draw was {0} found in game ID {1}.".format(mindraw, ", ".join(mindrawIDs)))
print("The fastest resign was {0} found in game ID {1}.".format(minresign, ", ".join(minresignIDs)))
print("The biggest upset was {0} points in game ID {1}.".format(upset, ", ".join(upsetIDs)))
print("{0} was the longest game with ID {1}.".format(maxturns, ", ".join(maxturnIDs)))
print("{0} was the highest ACPL in game ID {1}. {2} was the lowest ACPL in game ID {3}. Combined maximum ACPL was {4} in game ID {5} and the combined minimum ACPL was {6} in game ID {7}.".format(maxi, ", ".join(wbmaxigame), mini, ", ".join(wbminigame), combmaxi, ", ".join(combmaxigame), combmini, ", ".join(combminigame)))
print("The longest think was {0} in game {1} on move {2}".format(maxi_think, ", ".join(maxi_thinkIDs), maxi_move))
print("The most time left was {0} in game {1}".format(maxi_remain, ", ".join(maxi_remainIDs)))
print("The most time spent was {0} in game {1}".format(maxi_spent, ", ".join(maxi_spentIDs)))

def seasonStats(gamevalues):
    for game in gamevalues:
        try:
            _ = game['players']['white']['analysis']['acpl']
        except KeyError:
            print("no analysis for {0}".format(game['id']))

    removal = list([game for game in gamevalues if game['turns'] < 4 or game['status'] == 'started'])
    print(removal)
    for game in removal:
        gamevalues.remove(game)

    playergames = {}
    #dictionary of playername : [(game, colour), ...]
    for game in gamevalues:
        w = game['players']['white']['userId']
        b = game['players']['black']['userId']
        if w not in playergames:
            playergames[w] = [(game,'white')]
        else:
            playergames[w].append((game,'white'))
        if b not in playergames:
            playergames[b] = [(game,'black')]
        else:
            playergames[b].append((game,'black'))

    ################################################################

    #dictionary of playername : [ACPLs]
    playerACPLs = {}
    for player in playergames:
        playerACPLs[player] = []
        for gamedetails in playergames[player]:
            ACPL = gamedetails[0]['players'][gamedetails[1]]['analysis']['acpl']
            playerACPLs[player].append(ACPL)

    averageACPL = []
    for player in playerACPLs:
        average = sum(playerACPLs[player])/len(playerACPLs[player])
        if len(playerACPLs[player]) < 4:
            average = '< 4 games'
            continue
        averageACPL.append((player, average))
    averageACPL.sort(key=lambda x: x[1])
    print("acpl", averageACPL)

    #################################################################

    playerGameLen = {}
    for player in playergames:
        playerGameLen[player] = []
        for gamedetails in playergames[player]:
            GameLen = gamedetails[0]['turns']
            playerGameLen[player].append(GameLen)
    #print playerGameLen

    averageLen = []
    for player in playerGameLen:
        average = sum(playerGameLen[player])/len(playerGameLen[player])
        if len(playerGameLen[player]) < 4:
            average = '< 4 games'
            continue
        averageLen.append((player, average))
    averageLen.sort(key=lambda x: x[1])
    print("average length", averageLen)

    #################################################################
    playerDraws = []
    for player in playergames:
        draws = 0
        for gamedetails in playergames[player]:
            if gamedetails[0]['status'] in ['draw', 'stalemate']:
                draws += 1
        playerDraws.append((player,draws))
    playerDraws.sort(key=lambda x:x[1])
    print("draws", playerDraws)
    #################################################################
    sandbag = []
    for player in playergames:
        #order player's rating chronologically by 'createdAt'
        games = []
        for gamedetails in playergames[player]:
            rating = gamedetails[0]['players'][gamedetails[1]]['rating']
            time = gamedetails[0]['createdAt']
            games.append((time, rating))
        games.sort()
        diff = games[-1][1] - games[0][1]
        sandbag.append((player, diff))
    sandbag.sort(key=lambda x: x[1])
    sandbag.reverse()
    print("sandbag", sandbag)
    ################################################################
    openings = {}
    for game in gamevalues:
        try:
            a = game["opening"]["eco"]
        except KeyError:
            a = "unknown or from position"
        if a not in openings:
            openings[a] = 1
        else:
            openings[a] += 1
    opening_list = [[k,v] for k,v in list(openings.items())]
    opening_list.sort()
    print(opening_list)

if ROUNDNUMS[1] - ROUNDNUMS[0] > 1:
    seasonStats(gamevalues)
