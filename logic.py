class PokerBot:
    def __init__(self, name, strategy, stack=100):
        self.name = name
        self.strategy = strategy
        self.hand = []
        self.stack = stack
        self.current_bet = 0
        self.folded = False  # ✅ Initialize folded status

    def set_hand(self, hand):
        self.hand = hand
        self.folded = False  # ✅ Reset folded status for a new hand

    def decide_action(self, game_state, minimum_bet):
        action = self.strategy.decide(game_state, self.hand)

        if action == 'fold':
            return 'fold', 0
        elif action == 'call':
            call_amount = min(minimum_bet - self.current_bet, self.stack)
            return 'call', call_amount
        elif action == 'raise':
            raise_amount = min(minimum_bet * 2, self.stack)
            return 'raise', raise_amount
        elif action == 'allin':
            raise_amount = self.stack
            return 'raise', raise_amount
        else:
            return 'check', 0

    def bet(self, amount):
        if amount > self.stack:
            amount = self.stack
        self.stack -= amount
        self.current_bet += amount
        return amount

    def reset_bet(self):
        self.current_bet = 0

    def __repr__(self):
        return f"{self.name} (Chips: {self.stack})"
