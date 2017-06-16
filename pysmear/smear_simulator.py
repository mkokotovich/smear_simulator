# Simulator for the card game smear

import sys
sys.path.insert(0, "..")
sys.path.insert(0, "../../pydealer")

from game_manager import SmearGameManager
from player import *
from playing_logic import *
from db_manager import DbManager

class SmearSimulator:
    def __init__(self, debug=False, num_teams=2, score_to_play_to=11, log_to_db=False, create_graphs=False):
        self.debug = debug
        self.dbm = None
        if log_to_db:
            self.dbm = DbManager(hostname="localhost", port="27017", debug=self.debug)
        static_dir=None
        graph_prefix=None
        if create_graphs:
            static_dir="static"
            graph_prefix="1234"

        self.smear = SmearGameManager(cards_to_deal=6, debug=debug, num_teams=num_teams, score_to_play_to=score_to_play_to, static_dir=static_dir, graph_prefix=graph_prefix, dbm=self.dbm)
        self.smear.add_player(Player("player0", debug=debug, playing_logic=CautiousTaker(debug=debug)))
        self.smear.add_player(Player("player1", debug=debug))
        if num_teams is not 0:
            # If playing teams, add a smart teammate
            self.smear.add_player(Player("player2", debug=debug, playing_logic=CautiousTaker(debug=debug)))
        else:
            # If not playing teams, add a simple player
            self.smear.add_player(Player("player2", debug=debug))
        self.smear.add_player(Player("player3", debug=debug))
        self.games_won = {}
        for player in [ "player0", "player1", "player2", "player3" ]:
            self.games_won[player] = 0
        self.num_games = 0
        #self.smear_stats = SmearStats()

    def play_game(self):
        if self.debug:
            print "\n\n Starting game \n"
        self.smear.reset_game()
        self.smear.start_game()
        #self.smear_stats.add_new_game()
        #for player in self.smear.get_players():
            #self.smear_stats.add_game_status(self.smear.number_of_hands, player.name, player.get_card_count(), player.number_of_cards())
        while not self.smear.is_game_over():
            self.smear.play_game_async()
            #for player in self.smear.get_players():
                #self.smear_stats.add_game_status(self.smear.number_of_hands, player.name, player.get_card_count(), player.number_of_cards())
            if self.debug:
                print self.smear
        if self.debug:
            print self.smear.post_game_summary()
        winners = self.smear.get_winners()
        for winner in winners:
            self.games_won[winner] += 1
        #self.smear_stats.finalize_game(self.smear.number_of_hands, self.smear.get_winner())

    def run(self, num_games=1):
        self.num_games=num_games
        sys.stdout.write("Running simulation")
        for n in range(0, num_games):
            sys.stdout.write(".")
            sys.stdout.flush()
            self.play_game()
        sys.stdout.write("\n")

    def stats(self):
        stats = ""
        for winner, games_won in self.games_won.items():
            stats += "{} won {} games ({}%)\n".format(winner, games_won, (100.0*games_won/self.num_games))
        return stats


