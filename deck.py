from treys import Card, Evaluator
from itertools import combinations
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


# Precompute Card Map for Faster Conversion
RANK_MAP = {'2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8',
            '9': '9', '10': 'T', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'}

SUIT_MAP = {'Hearts': 'h', 'Diamonds': 'd', 'Clubs': 'c', 'Spades': 's'}

CARD_MAP = {f"{rank} of {suit}": f"{RANK_MAP[rank]}{SUIT_MAP[suit]}"
            for rank in RANK_MAP for suit in SUIT_MAP}


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
        """ Convert human-readable card format to Treys format using precomputed CARD_MAP. """
        return [CARD_MAP[card] for card in cards]

    def monte_carlo_simulation(self, hand, community_cards, num_simulations=1000):
        """Simulates future hands to estimate win probability."""
        wins = 0

        for _ in range(num_simulations):
            simulated_deck = PokerDeck()
            simulated_deck.shuffle()

            # Avoid using already dealt cards
            used_cards = set(hand + community_cards)

            # Generate missing community cards
            missing_cards = 5 - len(community_cards)
            simulated_board = community_cards[:]

            while len(simulated_board) < 5:
                card = simulated_deck.deal(1)[0]
                if card not in used_cards:
                    simulated_board.append(card)
                    used_cards.add(card)

            # Generate a valid opponent hand
            opponent_hand = []
            while len(opponent_hand) < 2:
                card = simulated_deck.deal(1)[0]
                if card not in used_cards:
                    opponent_hand.append(card)
                    used_cards.add(card)

            # Convert hands to Treys format
            try:
                treys_community = [Card.new(card) for card in self.convert_to_treys(simulated_board)]
                treys_hand = [Card.new(card) for card in self.convert_to_treys(hand)]
                treys_opponent = [Card.new(card) for card in self.convert_to_treys(opponent_hand)]
            except KeyError as e:
                print(f"Error converting cards: {e}")
                continue  # Skip this simulation if conversion fails

            # Evaluate both hands
            our_score = self.evaluator.evaluate(treys_community, treys_hand)
            opponent_score = self.evaluator.evaluate(treys_community, treys_opponent)

            if our_score < opponent_score:  # Lower score = better hand in Treys
                wins += 1

        return wins / num_simulations if num_simulations > 0 else 0.5  # Default to 50% if no valid simulations

    def preflop_hand_strength(self, hand):
        """Returns a probability estimate of hand strength pre-flop."""
        ranked_hands = {
            ('A', 'A'): 0.85, ('K', 'K'): 0.82, ('Q', 'Q'): 0.80, ('J', 'J'): 0.77,
            ('A', 'A'): 0.85, ('K', 'K'): 0.82, ('Q', 'Q'): 0.80, ('J', 'J'): 0.77,
            ('A', 'K'): 0.75, ('10', '10'): 0.73, ('A', 'Q'): 0.70, ('A', 'J'): 0.68,
            ('K', 'Q'): 0.66, ('J', '10'): 0.64, ('A', '10'): 0.62, ('K', 'J'): 0.60,
            ('Q', 'J'): 0.58, ('K', '10'): 0.55, ('Q', '10'): 0.52,
            ('2', '7'): 0.10, ('3', '8'): 0.12, ('4', '9'): 0.14, ('5', '10'): 0.16,
        }
        values = sorted([hand[0][0], hand[1][0]])  # Sort card values
        return ranked_hands.get(tuple(values), 0.35)  # Default mid-range strength

    def determine_best_five(self, full_hand):
        """
        Determines the best five-card hand from a set of seven cards.
        Uses Treys' evaluator to score all possible 5-card hands and picks the best.
        """
        best_hand = None
        best_score = float('inf')  # Lower score is better in Treys

        # Convert human-readable cards to Treys format before evaluation
        treys_full_hand = [Card.new(card) for card in self.convert_to_treys(full_hand)]

        # Generate all possible 5-card combinations from the 7 cards
        for five_card_hand in combinations(treys_full_hand, 5):
            five_card_list = list(five_card_hand)  # Convert tuple to list
            score = self.evaluator.evaluate([], five_card_list)

            if score < best_score:
                best_score = score
                best_hand = five_card_list  # Store the best 5-card list

        return best_hand

    def evaluate_hand_type(self, hand):
        """
        Determines the type of the best five-card poker hand.
        Uses Treys' ranking system and converts it into human-readable format.
        """
        evaluator = Evaluator()

        # Ensure 'hand' is a list of Treys card objects, not human-readable format
        if isinstance(hand[0], str):  # If the first element is a string, convert it
            treys_hand = [Card.new(card) for card in self.convert_to_treys(hand)]
        else:
            treys_hand = hand  # Already in Treys format, no need to convert

        rank_class = evaluator.get_rank_class(evaluator.evaluate([], treys_hand))

        hand_names = {
            1: "Royal Flush",
            2: "Straight Flush",
            3: "Four of a Kind",
            4: "Full House",
            5: "Flush",
            6: "Straight",
            7: "Three of a Kind",
            8: "Two Pair",
            9: "One Pair",
            10: "High Card"
        }

        return hand_names.get(rank_class, "Unknown Hand")

    def get_best_hand(self, hand, community_cards):
        """Returns the best five-card hand and its type."""
        full_hand = hand + community_cards  # Combine hole cards with community cards
        best_five = self.determine_best_five(full_hand)  # Use self to call instance method
        hand_type = self.evaluate_hand_type(best_five)  # Use self to call instance method
        return best_five, hand_type
