#! /usr/bin/env python

#stats: biggest upset, combined and individual low and high acpl, longest, shortest, fastest mate.
import urllib
import requests
import lxml.html
import time
import json

league = raw_input("Please enter 'team4545' or 'lonewolf'")
season = raw_input("Please enter season number as a digit:")
roundnum = raw_input("Please enter round number as a digit:")
gamesfilename = "{0}GamesS{1}R{2}".format(league, season, roundnum) 
#gamesfilename = 'lonewolfSeasonS6'
lichessurl = "https://en.lichess.org/"

if league == "team4545":
    xpathclass = "cell-game-result"
elif league == "lonewolf":
    xpathclass = "text-center text-nowrap"

def gameList():
    #build list of games from the round
    connection = urllib.urlopen('https://www.lichess4545.com/{0}/season/{1}/round/{2}/pairings/'.format(league, season, roundnum))
    dom =  lxml.html.fromstring(connection.read())
    gameIDs = []
    for link in dom.xpath('//td[@class="{0}"]/a/@href'.format(xpathclass)):
        gameIDs.append(link[-8:])
    return gameIDs

def getGames(gameIDs):
    #get games listed in gameIDs
    games = {}
    for num,gameid in enumerate(gameIDs):
        response = requests.get("https://en.lichess.org/api/game/{0}?with_analysis=1&with_movetimes=1".format(gameid))
        games[gameid] = json.loads(response.text)
        time.sleep(1)
        print "got game", num
    return games

#get games in dictionary format - from file if present or lichess.org if not
gameIDs = gameList()
try:
    infile = open(gamesfilename,'r')
    games = json.load(infile)
    infile.close()
    newgames = set(gameIDs) - set(games.keys())
    if newgames:
        games.update(getGames(newgames))
        outfile = open(gamesfilename, 'w')
        json.dump(games, outfile, indent=4)
        print "This data was updated with:", newgames
    print "This data was read from file."
except Exception,e:
    print e
    games = getGames(gameIDs)
    outfile = open(gamesfilename,'w')
    json.dump(games, outfile, indent=4)
    print "This data was fetched from web."
    outfile.close()
gamevalues = games.values()

#get stats for ACPL high low both individual and combined
def getACPL(games):
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
            print "No analysis for {0}{1}".format(lichessurl, game.get('id'))
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

#get longest (and shortest) games
def getTurns(games):
    maxturnIDs = []
    maxturns =  max([(game['turns']) for game in gamevalues])
    for game in gamevalues:
        if game['turns'] == maxturns:
            maxturnIDs.append(game['id'])
    return maxturns, maxturnIDs#, minturns, minturnIDs
"""    minturnIDs = []
    minturns =  min([(game['turns']) for game in gamevalues])
    for game in gamevalues:
        if game['turns'] == minturns:
            minturnIDs.append(game['id'])"""

#get biggest match upset by rating difference
def getUpset(games):
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

#get shortest mate
def getQuickGame(games, finish):
    try:
        minfinIDs = []
        minfin =  min([(game['turns']) for game in gamevalues if game['status'] == finish])
        for game in gamevalues:
            if game['status'] == finish and game['turns'] == minfin:
                minfinIDs.append(game['id'])
        return minfin, minfinIDs
    except ValueError:
        return "not", ["N/A"]

def convert(time):
    minutes = time / 6000
    seconds = round(((((time / 6000.0) - minutes))*60),0)
    return  str(minutes) + " minutes " + str(seconds) + " seconds"

def timeStats(games):
    if league == "team4545":
        start_time = 45*60*100
        increment = 45*100
    elif league == "lonewolf":
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
            print "No movetimes for {0}{1}".format(lichessurl, game.get('id'))
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
            elif time == maxi_think:
                maxi_spentIDs.append(game.get('id'))
    maxi_spent = convert(maxi_spent)
    maxi_remain = convert(maxi_remain) 
    maxi_think = convert(maxi_think)
    return maxi_think, maxi_thinkIDs, maxi_move, maxi_remain, maxi_remainIDs, maxi_spent, maxi_spentIDs

#assigning variables for formatting
upset, upsetIDs = getUpset(games)
minmate, minmateIDs = getQuickGame(games, "mate")
mindraw, mindrawIDs = getQuickGame(games, "draw")
minresign, minresignIDs = getQuickGame(games, "resign")
maxturns, maxturnIDs = getTurns(games)
maxi, wbmaxigame, mini, wbminigame, combmaxi, combmaxigame, combmini, combminigame = getACPL(games)
maxi_think, maxi_thinkIDs, maxi_move, maxi_remain, maxi_remainIDs, maxi_spent, maxi_spentIDs = timeStats(games)

for stat in [upsetIDs, minmateIDs, mindrawIDs, minresignIDs, maxturnIDs, wbmaxigame, wbminigame, combmaxigame, combminigame, maxi_thinkIDs, maxi_remainIDs, maxi_spentIDs]:
    for n, game in enumerate(stat):
        stat[n] = lichessurl + game

print "The fastest mate was {0} found in game ID {1}.".format(minmate, ", ".join(minmateIDs))
print "The fastest draw was {0} found in game ID {1}.".format(mindraw, ", ".join(mindrawIDs))
print "The fastest resign was {0} found in game ID {1}.".format(minresign, ", ".join(minresignIDs))
print "The biggest upset was {0} points in game ID {1}.".format(upset, ", ".join(upsetIDs))
print "{0} was the longest game with ID {1}.".format(maxturns, ", ".join(maxturnIDs))
#, {2} was the shortest game with ID {3}. minturns, ", ".join(minturnIDs)
print "{0} was the highest ACPL in game ID {1}. {2} was the lowest ACPL in game ID {3}. Combined maximum ACPL was {4} in game ID {5} and the combined minimum ACPL was {6} in game ID {7}.".format(maxi, ", ".join(wbmaxigame), mini, ", ".join(wbminigame), combmaxi, ", ".join(combmaxigame), combmini, ", ".join(combminigame))
print "The longest think was {0} in game {1} on move {2}".format(maxi_think, ", ".join(maxi_thinkIDs), maxi_move)
print "The most time left was {0} in game {1}".format(maxi_remain, ", ".join(maxi_remainIDs))
print "The most time spent was {0} in game {1}".format(maxi_spent, ", ".join(maxi_spentIDs))
