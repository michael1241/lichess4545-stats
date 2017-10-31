# lichess4545-stats
Download games from lichess.org based on lichess4545.com league game list and generate statistics.

The following arguments must be included when running this program:
./chessstat.py [team4545 or lonewolf] [season number e.g. 1] [an ordered set of numbers denoting the round number(s) where the first element is the start of the round and the last is the round after which one wants to generate stats e.g 1,2 is round 1 4,6 is round 4 and 5 and 1,9 is rounds 1 to 8]

Optional argument(s):
[Usernames in lowercase of any player's games to be excluded, separated by commas and no spaces e.g. player1,player2]

extractpgns.py is a tool to take the output of chessstat.py and provide all games in PGN format. To run, use the following syntax including quote marks:
./extractpgns.py "outputfilename"

for example: ./extractpgns.py "team4545GamesS8R(8, 9)"
will create a new file in the same directory called team4545GamesS8R(8, 9)pgns.pgn

