import random
from deck import PokerHandEvaluator

class BaseStrategy:
    """
    Base strategy class for poker bots, providing methods for hand evaluation
    and decision-making based on win probability.
    """
    def __init__(self):
        self.evaluator = PokerHandEvaluator()

    def evaluate_strength(self, hand, community_cards):
        """Evaluates hand strength if at least five cards are available."""
        if len(community_cards) + len(hand) < 5:
            return None
        return self.evaluator.evaluate_hand(hand, community_cards)

    def estimate_win_probability(self, hand, community_cards, num_opponents=3):
        """
        Estimates win probability using Monte Carlo simulation with an opponent scaling factor.
        The probability is adjusted based on the number of opponents.
        """
        if not community_cards:
            strength = self.evaluator.preflop_hand_strength(hand)
            print(f"🃏 Pre-flop: Hand {hand}, Strength: {strength:.2f}")
            return strength

        base_probability = self.evaluator.monte_carlo_simulation(hand, community_cards)

        # Increase penalty for more opponents
        adjustment_factor = max(0.05, 1 - (0.15 * (num_opponents - 1)))
        adjusted_probability = base_probability * adjustment_factor

        final_prob = max(0, min(1, adjusted_probability))

        print(f"📊 Hand: {hand}, Community: {community_cards}, Base Prob: {base_probability:.2f}, "
              f"Adj Factor: {adjustment_factor:.2f}, Final Prob: {final_prob:.2f}")

        return final_prob

    def should_bluff(self):
        """
        Determines if the bot should bluff based on a random probability.
        There is a 15% chance the bot will decide to bluff.
        """
        return random.random() > 0.85

    def is_pot_committed(self, bot, pot, bot_type):
        """
        Checks if the bot is pot-committed based on its current bet relative to its stack and the total pot.
        Different bot types have different commitment thresholds.
        """
        commitment_thresholds = {
            'aggressive': (0.40, 0.25),  # Aggressive bots commit a bit more
            'conservative': (0.75, 0.55),  # Conservative bots require much larger investment
            'random': (0.55, 0.40),  # Random behavior
            'allin': (0.30, 0.20)  # All-in bots commit sooner
        }

        stack_threshold, pot_threshold = commitment_thresholds.get(bot_type, (0.60, 0.40))
        invested_fraction = bot.current_bet / max(bot.stack + bot.current_bet, 1)
        pot_share = bot.current_bet / max(pot, 1)

        return invested_fraction > stack_threshold or pot_share > pot_threshold


class AggressiveStrategy(BaseStrategy):
    def decide(self, game_state, hand):
        num_opponents = game_state.get('num_opponents', 1)
        win_probability = self.estimate_win_probability(hand, game_state['community_cards'], num_opponents)
        pot = game_state.get('pot', 1)
        is_committed = self.is_pot_committed(game_state['bot'], pot, 'aggressive')

        if win_probability < 0.4 and not is_committed:
            return ('fold', 0)  # Now folds more often

        if win_probability > 0.6:
            return ('raise', int(win_probability * 140))

        return ('call', 10)


class ConservativeStrategy(BaseStrategy):
    def decide(self, game_state, hand):
        win_probability = float(self.estimate_win_probability(hand, game_state['community_cards']))
        pot = game_state.get('pot', 1)
        is_committed = self.is_pot_committed(game_state['bot'], pot, 'conservative')

        if win_probability < 0.65 and not is_committed:
            return ('fold', 0)  # Conservative bots fold even more

        if is_committed and win_probability < 0.3:
            return ('fold', 0)  # If they are pot-committed but still weak, fold

        if win_probability > 0.7:
            return ('raise', 20)

        return 'fold'


class RandomStrategy(BaseStrategy):
    """
    Strategy for unpredictable players who make random decisions.
    This adds an element of surprise to the game, making it harder to predict their moves.
    """
    def decide(self, game_state, hand):
        return random.choices(['fold', 'call', 'raise'], weights=[0.5, 0.3, 0.2])[0]


class AllIn(BaseStrategy):
    def decide(self, game_state, hand):
        win_probability = self.estimate_win_probability(hand, game_state['community_cards'])

        if win_probability < 0.8:
            return ('fold', 0)  # No more going all-in on weak hands

        if win_probability >= 0.8:
            return ('allin', game_state['bot'].stack)

        return ('call', 10)

class fold(BaseStrategy):
    def decide(self, game_state, hand):
        return ('fold', 0)
