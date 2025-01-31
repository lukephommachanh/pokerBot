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

    def estimate_win_probability(self, hand, community_cards, num_opponents=1):
        """
        Estimates win probability using Monte Carlo simulation with an opponent scaling factor.
        The probability is adjusted based on the number of opponents, decreasing by 12% per additional opponent.
        """
        if not community_cards:
            strength = self.evaluator.preflop_hand_strength(hand)
            #print(f"🃏 Pre-flop: Hand {hand}, Strength: {strength:.2f}")
            return strength

        base_probability = self.evaluator.monte_carlo_simulation(hand, community_cards)
        adjustment_factor = max(0.1, 1 - (0.12 * (num_opponents - 1)))  # Reduce 12% per opponent
        adjusted_probability = base_probability * adjustment_factor
        final_prob = max(0, min(1, adjusted_probability))

        #print(f" ")
        """print(f"📊 Hand: {hand}, Community: {community_cards}, Base Prob: {base_probability:.2f}, "
              f"Adj Factor: {adjustment_factor:.2f}, Final Prob: {final_prob:.2f}")"""
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
            'aggressive': (0.30, 0.20),  # Aggressive bots commit faster
            'conservative': (0.65, 0.50),  # Conservative bots require a larger investment
            'random': (0.50, 0.35),  # Balanced decision making
            'allin': (0.25, 0.15)  # All-in bots commit more easily
        }
        stack_threshold, pot_threshold = commitment_thresholds.get(bot_type, (0.50, 0.35))
        invested_fraction = bot.current_bet / max(bot.stack + bot.current_bet, 1)
        pot_share = bot.current_bet / max(pot, 1)
        return invested_fraction > stack_threshold or pot_share > pot_threshold

class AggressiveStrategy(BaseStrategy):
    """
    Strategy for aggressive players who frequently bet and raise.
    They tend to apply pressure on opponents with frequent raises.
    """
    def decide(self, game_state, hand):
        num_opponents = game_state.get('num_opponents', 1)
        win_probability = self.estimate_win_probability(hand, game_state['community_cards'], num_opponents)
        is_big_blind = game_state.get('is_big_blind', False)
        pot = game_state.get('pot', 1)
        is_committed = self.is_pot_committed(game_state['bot'], pot, 'aggressive')

        if win_probability < 0.3:
            return ('fold', 0)
        if is_big_blind and win_probability > 0.5:
            return ('raise', int(win_probability * 120))
        if win_probability > 0.4:
            return ('raise', int(win_probability * 140))
        return ('call', 10)

class ConservativeStrategy(BaseStrategy):
    """
    Strategy for conservative players who tend to fold weak hands and play only premium hands.
    They focus on minimizing risk and maximizing strong hand plays.
    """
    def decide(self, game_state, hand):
        win_probability = self.estimate_win_probability(hand, game_state['community_cards'])
        pot = game_state.get('pot', 1)
        is_committed = self.is_pot_committed(game_state['bot'], pot, 'conservative')

        if win_probability < 0.4 and not is_committed:
            return ('fold', 0)
        if is_committed and win_probability < 0.2:
            return ('fold', 0)
        if win_probability > 0.6:
            return ('call', 10)
        return ('fold', 0)

class RandomStrategy(BaseStrategy):
    """
    Strategy for unpredictable players who make random decisions.
    This adds an element of surprise to the game, making it harder to predict their moves.
    """
    def decide(self, game_state, hand):
        return random.choices(['fold', 'call', 'raise'], weights=[0.5, 0.3, 0.2])[0]

class AllIn(BaseStrategy):
    """
    Strategy for players who go all-in when they sense a strong hand.
    They play aggressively and are willing to risk their entire stack when confident in their chances.
    """
    def decide(self, game_state, hand):
        win_probability = self.estimate_win_probability(hand, game_state['community_cards'])
        if win_probability < 0.3 and random.random() < 0.5:
            return ('fold', 0)
        if win_probability > 0.75:
            return ('allin', 1000)
        return ('call', 10)
