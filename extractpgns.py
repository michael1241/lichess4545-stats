#! /usr/bin/env python

import sys
import json

datafile = sys.argv[1]

infile = open(datafile,'r')
games = json.load(infile)
infile.close()

newfile = datafile + "pgns.pgn"
outfile = open(newfile, 'w')

convert = {"white":"1-0","black":"0-1"}

for game in games.values():
    try:
        if game['status'] in ["draw", "stalemate"]:
            result = "1/2-1/2"
        else:
            result = convert[game['winner']]
        outfile.write('[Event "{0}"]\n[Result "{1}"]\n[WhiteElo "{3}"]\n[BlackElo "{4}"]\n{2}\n{1}\n\n'.format(game['id'], result, game['moves'], game['players']['white']['rating'], game['players']['black']['rating']))
    except KeyError:
        print "No moves for this game"

outfile.close()
