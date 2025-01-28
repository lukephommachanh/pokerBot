import random
from deck import PokerHandEvaluator

class AggressiveStrategy:
    def decide(self, game_state, hand):
        return 'raise'

class ConservativeStrategy:
    def decide(self, game_state, hand):
        hand_strength = game_state['hand_strength']
        if hand_strength > 0.9:
            return 'raise'
        elif hand_strength > 0.6:
            return 'call'
        return 'fold'

class RandomStrategy:
    def decide(self, game_state, hand):
        return random.choice(['fold', 'call', 'raise'])

class AllIn:
    def decide(self, game_state, hand):
        return 'allin'


