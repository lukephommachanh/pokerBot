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
