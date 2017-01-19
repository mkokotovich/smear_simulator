# Simulator for the card game smear

import pydealer
from pydealer.const import POKER_RANKS
from smear_utils import SmearUtils as utils
from trick import Trick


# Everything regarding the state of a hand, so a player can look at this and chose a card to play
class SmearHand:
    def __init__(self, num_players, debug=False):
        self.num_players = num_players
        self.trump = ""
        self.bid = 0
        self.bidder = 0
        self.first_player = 0
        self.debug = debug
        self.current_trick = Trick(self.trump, debug)

    def set_trump(self, trump):
        self.trump = trump
        self.current_trick.trump = trump

    def add_card(self, player_id, card):
        if card is not None:
            self.current_trick.add_card(player_id, card)

    def prepare_for_next_trick(self):
        self.current_trick = Trick(self.trump, self.debug)

    def get_cards_played(self):
        return self.current_trick.get_cards_played()

# A hand is one deal, play until all cards are out, and tally the score iteration
class SmearHandManager:
    def __init__(self, players_dict, cards_to_deal=6, debug=False):
        self.players = players_dict
        self.num_players = len(players_dict.values())
        self.cards_to_deal = cards_to_deal
        self.deck = pydealer.Deck(ranks=POKER_RANKS)
        if self.num_players * cards_to_deal > self.deck.size:
            raise ValueError("num_players ({}) times cards_to_deal ({}) is larger than the size of the deck ({})".format(self.num_players, cards_to_deal, deck.size))
        self.reset_players()
        self.current_hand_id = 0
        self.current_hand = SmearHand(self.num_players, debug)
        self.scores = {}
        self.current_low_id = 0
        self.current_low = None
        self.all_bids_are_in = False
        self.forced_two_set = False
        self.debug = debug

    def reset_players(self):
        for i in range(0, self.num_players):
            self.players[i].reset()

    def deal_new_deck(self):
        self.deck = pydealer.Deck(ranks=POKER_RANKS)
        self.deck.shuffle()
        for j in range(0, self.cards_to_deal):
            for i in range(0, self.num_players):
                self.players[i].receive_dealt_card(self.deck.deal(1))

    def reset_for_next_hand(self):
        self.reset_players()
        self.deal_new_deck()
        self.current_hand_id += 1
        self.current_hand = SmearHand(self.num_players, self.debug)
        self.scores = {}
        self.current_low_id = 0
        self.current_low = None
        self.all_bids_are_in = False
        self.forced_two_set = False

    def is_hand_over(self):
        return not self.players[0].has_cards()

    def get_scores(self, dealer_id):
        if self.forced_two_set:
            self.scores = {}
            for i in range(0, self.num_players):
                self.scores[i] = 0
            self.scores[dealer_id] = -2
            return self.scores

        if not self.is_hand_over():
            print "Hand isn't over yet"
            return None
        self.scores = {}
        current_winner_ids = []
        current_winning_score = 0
        current_high_id = 0
        current_high = None
        for i in range(0, self.num_players):
            game_score = self.players[i].calculate_game_score()
            if current_winning_score < game_score:
                current_winning_score = game_score
                current_winner_ids = [ i ]
            elif current_winning_score == game_score:
                current_winner_ids.append(i)
            high = self.players[i].get_high_trump_card(self.current_hand.trump)
            if (not high == None) and (current_high == None or utils.is_less_than(current_high, high, self.current_hand.trump)):
                current_high = high
                current_high_id = i
            self.scores[i] = self.players[i].get_jacks_and_jicks_count(self.current_hand.trump)
        # No ties for game, there is just no winner then
        if len(current_winner_ids) == 1:
            self.scores[current_winner_ids[0]] += 1
            if self.debug:
                print "{} won game with {} points".format(self.players[current_winner_ids[0]].name, current_winning_score)
        elif self.debug:
            print "No one won game, there was a tie at {} points between {}".format(current_winning_score, ", ".join(self.players[x].name for x in current_winner_ids))
        self.scores[current_high_id] += 1
        if self.debug:
            print "{} won high with a {}".format(self.players[current_high_id].name, current_high)
        self.scores[self.current_low_id] += 1
        if self.debug:
            print "{} won low with a {}".format(self.players[self.current_low_id].name, self.current_low)
        # Check to see if bidder was set
        if self.scores[self.current_hand.bidder] < self.current_hand.bid:
            if self.debug:
                print "{} bid {} and only got {}: is set!".format(self.players[self.current_hand.bidder].name, self.current_hand.bid, self.scores[self.current_hand.bidder])
            self.scores[self.current_hand.bidder] = -self.current_hand.bid
        else:
            if self.debug:
                print "{} got their bid of {} with {} points".format(self.players[self.current_hand.bidder].name, self.current_hand.bid, self.scores[self.current_hand.bidder])

        return self.scores

    def get_players(self):
        return self.players.values()

    def post_hand_summary(self):
        msg = ""
        for i in range(0, self.num_players):
            msg +=  "{} received {} points\n".format(self.players[i].name, self.scores[i])
        return msg

    def __str__(self):
        msg = ""
        for i in range(0, self.num_players):
            msg += str(self.players[i]) + "\n"
        return msg

    def next_player_id(self, current_id):
        next_id = current_id + 1
        if next_id == self.num_players:
            next_id = 0
        return next_id

    def get_bids(self, dealer_id):
        self.current_hand.bid = 0
        self.current_hand.bidder = 0
        # Will actually bid last
        current_bidder = dealer_id
        for i in range(0, self.num_players):
            current_bidder = self.next_player_id(current_bidder)
            bid = self.players[current_bidder].declare_bid(self.current_hand, force_two=(current_bidder==dealer_id))
            if bid == 1:
                print "Illegal bid of 1, resetting to 0"
                bid = 0
            elif bid > 5:
                print "Illegal bid of > 5 ({}) resetting to 5".format(bid)
                bid = 5
            if self.debug:
                print "{} bid {} and has {}".format(self.players[current_bidder].name, bid, " ".join(x.abbrev for x in self.players[current_bidder].hand))
            if bid > self.current_hand.bid:
                self.current_hand.bid = bid
                self.current_hand.bidder = current_bidder
        self.all_bids_are_in = True
        if self.current_hand.bid == 0:
            # No one bid, the dealer takes a two set
            self.forced_two_set = True
        self.current_hand.first_player = self.current_hand.bidder
        if self.debug and not self.forced_two_set:
            print "{} has the highest bid of {}".format(self.players[self.current_hand.bidder].name, self.current_hand.bid)
        if self.debug and self.forced_two_set:
            print "{} was forced to take a two set".format(self.players[dealer_id].name)
        return self.forced_two_set

    def reveal_trump(self):
        self.current_hand.set_trump(self.players[self.current_hand.bidder].get_trump())
        if self.debug:
            print "{} picks {} to be trump".format(self.players[self.current_hand.bidder].name, self.current_hand.trump)

    def update_low_if_needed(self, card, player_id):
        if utils.is_trump(card, self.current_hand.trump) and (self.current_low == None or utils.is_less_than(card, self.current_low, self.current_hand.trump)):
            self.current_low = card
            self.current_low_id = player_id

    def play_trick(self):
        current_player = self.current_hand.first_player
        msg = ""
        for i in range(0, self.num_players):
            if self.debug:
                # Grab this before playing a card so that card is included
                msg = str(self.players[current_player])
            card = self.players[current_player].play_card(self.current_hand)
            # Because you don't need to take low home to get the point
            self.update_low_if_needed(card, current_player)
            if self.debug:
                print "{} plays {}".format(msg, str(card))
            self.current_hand.add_card(current_player, card)
            current_player = self.next_player_id(current_player)
        # Give all cards to winner
        cards = self.current_hand.current_trick.get_all_cards_as_stack()
        winner_id = self.current_hand.current_trick.get_winner_id()
        self.players[winner_id].add_cards_to_pile(cards)
        # Tell each player the results of the trick
        for i in range(0, self.num_players):
            self.players[i].save_results_of_trick(winner_id, self.current_hand.get_cards_played())
        # Reset for the next trick
        self.current_hand.prepare_for_next_trick()
        self.current_hand.first_player = winner_id
        if self.debug:
            print "{} won {}\n".format(self.players[winner_id].name, " ".join(x.abbrev for x in cards))
