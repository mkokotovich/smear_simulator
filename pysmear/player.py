# Simulator for the card game smear

import pydealer
from pydealer.const import POKER_RANKS
from bidding_logic import *
from playing_logic import *
from player_input import *



class Player:
    def __init__(self, player_id, initial_cards=None, debug=False):
        self.reset()
        self.debug = debug
        if initial_cards:
            self.hand += initial_cards
        self.name = player_id
        self.bid = 0
        self.bid_trump = None
        self.is_bidder = False
        self.playing_logic = JustGreedyEnough()
        self.bidding_logic = BasicBidding(debug=debug)

    def reset(self):
        self.hand = pydealer.Stack()
        self.pile = pydealer.Stack()
        self.bid = 0
        self.bid_trump = None
        self.is_bidder = False

    def set_initial_cards(self, initial_cards):
        self.hand = pydealer.Stack()
        self.hand += initial_cards

    def receive_dealt_card(self, dealt_card):
        self.hand += dealt_card

    def print_cards(self, print_pile=False):
        msg = "{} hand: {}".format(self.name, " ".join(x.abbrev for x in self.hand))
        if print_pile:
            msg += "\n"
            msg += "{} pile: {}".format(self.name, " ".join(x.abbrev for x in self.pile))
        return msg

    # Returns a single card
    def play_card(self, current_hand):
        if self.hand.size == 0:
            return None
        card_index = self.playing_logic.choose_card(current_hand, self.hand)
        card_to_play = self.hand[card_index]
        del self.hand[card_index]
        return card_to_play

    def has_cards(self):
        return self.hand.size != 0

    def declare_bid(self, current_hand, force_two=False):
        if self.debug:
            print "{} is calculating bid".format(self.name)
        self.bid, self.bid_trump = self.bidding_logic.declare_bid(current_hand, self.hand, force_two)
        return self.bid

    def get_trump(self):
        return self.bid_trump

    def calculate_game_score(self):
        game_score = 0
        for card in self.pile:
            if card.value == "10":
                game_score += 10
            if card.value == "Ace":
                game_score += 4
            elif card.value == "King":
                game_score += 3
            elif card.value == "Queen":
                game_score += 2
            elif card.value == "Jack":
                game_score += 1
        return game_score

    def get_high_trump_card(self, trump):
        high_trump = None
        my_trump = utils.get_trump_indices(trump, self.pile)
        if len(my_trump) != 0:
            high_trump = self.pile[my_trump[-1]]
        return high_trump

    def get_jacks_and_jicks_count(self, trump):
        my_trump = utils.get_trump_indices(trump, self.pile)
        points = 0
        for idx in my_trump:
            if self.pile[idx].value == "Jack":
                points += 1
        return points

    def add_cards_to_pile(self, cards):
        self.pile += cards

    def __str__(self):
        return "{}: {}".format(self.name, " ".join(x.abbrev for x in self.hand))


class InteractivePlayer(Player):
    def __init__(self, player_id, initial_cards=None, debug=False):
        Player.__init__(self, player_id, initial_cards, debug)
        self.playing_logic = PlayerInput(debug=debug)
        self.bidding_logic = self.playing_logic
