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
        The probability is adjusted based on the number of opponents, decreasing by 10% per additional opponent.
        """
        if not community_cards:
            strength = self.evaluator.preflop_hand_strength(hand)
            return strength

        base_probability = self.evaluator.monte_carlo_simulation(hand, community_cards)
        adjustment_factor = max(0.3, 1 - (0.10 * (num_opponents - 1)))
        adjusted_probability = max(0.2, base_probability * adjustment_factor)
        return max(0, min(1, adjusted_probability))  # Ensure valid probability range

    def should_bluff(self):
        """Determines if the bot should bluff with a 15% probability."""
        return random.random() > 0.85

    def is_pot_committed(self, bot, pot, bot_type):
        """Determines if the bot is pot-committed based on stack and pot size."""
        commitment_thresholds = {
            'aggressive': (0.30, 0.20),
            'conservative': (0.65, 0.50),
            'random': (0.50, 0.35),
            'allin': (0.25, 0.15)
        }
        stack_threshold, pot_threshold = commitment_thresholds.get(bot_type, (0.50, 0.35))
        invested_fraction = bot.current_bet / max(bot.stack + bot.current_bet, 1)
        pot_share = bot.current_bet / max(pot, 1)
        return invested_fraction > stack_threshold or pot_share > pot_threshold

class AggressiveStrategy(BaseStrategy):
    def decide(self, game_state, hand):
        num_opponents = game_state.get('num_opponents', 1)
        win_probability = self.estimate_win_probability(hand, game_state['community_cards'], num_opponents)
        pot = game_state.get('pot', 1)
        current_bet = game_state.get('minimum_bet', 10)
        is_committed = self.is_pot_committed(game_state['bot'], pot, 'aggressive')

        #print(f"\n🤖 {game_state['bot'].name} Decision:")
        #print(f"  - Win Probability: {win_probability:.2f}")
        #print(f"  - Current Bet: {current_bet}")
        #print(f"  - Pot Size: {pot}")
        #print(f"  - Is Committed? {is_committed}")

        # More hands should be played pre-flop
        if not game_state['community_cards'] and win_probability > 0.01:
            return ('call', current_bet)  # Looser pre-flop play

        # Prevent excessive raising
        if is_committed and win_probability < 0.003:
            #print(f"🏳️ {game_state['bot'].name} FOLDS.")
            return ('fold', 0)  # Avoid over-investing when the hand is weak

        # Prevent infinite raising
        if game_state.get('raise_count', 0) > 2:
            #print(f"🔵 {game_state['bot'].name} CALLS {current_bet}.")
            return ('call', current_bet)

        def execute_raise(multiplier):
            raise_amount = max(20, int(win_probability * pot * multiplier))
            raise_amount = min(game_state['bot'].stack, raise_amount)  # Prevent betting more than stack
            #print(f"🔺 {game_state['bot'].name} RAISES {raise_amount} chips!")
            return ('raise', raise_amount)

        if not game_state['community_cards'] and win_probability > 0.30:
            return execute_raise(0.5)
        if win_probability > 0.05:
            return execute_raise(0.4)
        if 0.02 < win_probability <= 0.95 and random.random() > 0.1:
            return execute_raise(0.3)
        if win_probability > 0.70:
            return execute_raise(0.5)

        if win_probability > 0.07:
            #print(f"🔵 {game_state['bot'].name} CALLS {current_bet}.")
            return ('call', current_bet)

        #print(f"🏳️ {game_state['bot'].name} FOLDS.")
        return ('fold', 0)

class ConservativeStrategy(BaseStrategy):
    def decide(self, game_state, hand):
        win_probability = self.estimate_win_probability(hand, game_state['community_cards'])
        pot = game_state.get('pot', 1)
        is_committed = self.is_pot_committed(game_state['bot'], pot, 'conservative')

        if win_probability < 0.13 and not is_committed:
            return ('fold', 0)
        if is_committed and win_probability < 0.09:
            return ('fold', 0)
        if win_probability > 0.6:
            return ('call', game_state['minimum_bet'])
        return ('fold', 0)


class RandomStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.last_action = None  # Track previous action

    def decide(self, game_state, hand):
        if self.last_action == 'raise':
            return ('call', min(game_state['bot'].stack, game_state['minimum_bet']))  # Ensure consistency

        action = random.choices(['fold', 'call', 'raise'], weights=[0.5, 0.3, 0.2])[0]
        self.last_action = action  # Store last action

        if action == 'raise':
            max_raise = min(50, game_state['pot'], game_state['bot'].stack)  # Prevent excessive raises
            if max_raise <= game_state['minimum_bet']:  # Ensure a valid raise range
                return ('call', min(game_state['bot'].stack, game_state['minimum_bet']))

            raise_amount = random.randint(game_state['minimum_bet'] + 1, max_raise)
            return ('raise', raise_amount)

        elif action == 'call':
            return ('call', min(game_state['bot'].stack, game_state['minimum_bet']))

        return ('fold', 0)


class AllIn(BaseStrategy):
    """
    Strategy for players who ALWAYS go all-in, every hand.
    """
    def decide(self, game_state, hand):
        bot_stack = game_state['bot'].stack
        if bot_stack > 0:
            return ('allin', bot_stack)  # Always go all-in with full stack
        return ('fold', 0)  # If bot is already at 0 chips, fold automatically