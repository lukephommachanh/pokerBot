from treys import Card, Evaluator
import random

class PokerDeck:
    def __init__(self):
        self.suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.deck = self.create_deck()

    def create_deck(self):
        return [f"{rank} of {suit}" for suit in self.suits for rank in self.ranks]

    def shuffle(self):
        random.shuffle(self.deck)

    def deal(self, num_cards):
        if num_cards > len(self.deck):
            raise ValueError("Not enough cards left in the deck to deal.")
        return [self.deck.pop() for _ in range(num_cards)]


class PokerHandEvaluator:
    def __init__(self):
        self.evaluator = Evaluator()

    def evaluate_hand(self, hand, community_cards):
        treys_hand = [Card.new(card) for card in self.convert_to_treys(hand)]
        treys_community = [Card.new(card) for card in self.convert_to_treys(community_cards)]

        all_cards = treys_hand + treys_community

        if len(all_cards) < 5:
            raise ValueError("Not enough cards to evaluate. At least 5 cards are required.")

        score = self.evaluator.evaluate(treys_community, treys_hand)
        return score

    def convert_to_treys(self, cards):
        treys_format = []
        rank_map = {'2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8',
                    '9': '9', '10': 'T', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'}
        suit_map = {'Hearts': 'h', 'Diamonds': 'd', 'Clubs': 'c', 'Spades': 's'}
        for card in cards:
            rank, suit = card.split(' of ')
            treys_format.append(f"{rank_map[rank]}{suit_map[suit]}")
        return treys_format
