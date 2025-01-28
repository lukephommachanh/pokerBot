from mechanics import PokerDeck
from deck import PokerHandEvaluator
from logic import PokerBot
from strategies import AggressiveStrategy, ConservativeStrategy, RandomStrategy, AllIn

# test push


def betting_round(bots, minimum_bet=10, community_cards=[]):
    pot = 0
    active_bots = [bot for bot in bots if bot.stack > 0]
    current_bet = minimum_bet
    raise_count = 0

    while True:
        betting_complete = True

        for bot in active_bots[:]:
            if bot.current_bet < current_bet:
                game_state = {
                    'hand_strength': bot.stack / 100,
                    'community_cards': community_cards,
                    'pot': pot,
                    'minimum_bet': current_bet,
                }

                action, amount = bot.decide_action(game_state, current_bet)
                if action == 'fold':
                    print(f"{bot.name} folds.")
                    active_bots.remove(bot)
                elif action == 'call':
                    call_amount = current_bet - bot.current_bet
                    if call_amount > bot.stack:
                        call_amount = bot.stack
                    placed_bet = bot.bet(call_amount)
                    pot += placed_bet
                    print(f"{bot.name} calls with {placed_bet} chips. Total pot: {pot}.")
                elif action == 'raise' and raise_count < 2:
                    raise_amount = max(amount, minimum_bet)
                    total_raise = current_bet + raise_amount
                    placed_bet = bot.bet(total_raise - bot.current_bet)
                    pot += placed_bet
                    current_bet = total_raise
                    raise_count += 1
                    betting_complete = False
                    print(f"{bot.name} raises with {raise_amount} chips. Total pot: {pot}.")
                else:
                    print(f"{bot.name} cannot raise further and calls.")
                    call_amount = current_bet - bot.current_bet
                    placed_bet = bot.bet(call_amount)
                    pot += placed_bet
                    print(f"{bot.name} calls with {placed_bet} chips. Total pot: {pot}.")
            else:
                print(f"{bot.name} is already matched with the current bet.")

        if betting_complete:
            break

    for bot in bots:
        bot.reset_bet()
    return pot, active_bots



def play_hand(deck, bots, evaluator):
    for bot in bots:
        bot.set_hand(deck.deal(2))

    community_cards = []
    stages = ['Pre-flop', 'Flop', 'Turn', 'River']
    cards_to_deal = [0, 3, 1, 1]

    pot = 0
    for stage, num_cards in zip(stages, cards_to_deal):
        if num_cards > 0:
            community_cards.extend(deck.deal(num_cards))

        print(f"\n=== {stage} ===")
        print(f"Community Cards: {community_cards}")

        if stage == "Pre-flop":
            pot_round, active_bots = betting_round(bots, minimum_bet=10, community_cards=[])
        else:
            pot_round, active_bots = betting_round(bots, minimum_bet=10, community_cards=community_cards)

        pot += pot_round

        if len(active_bots) == 1:
            winner = active_bots[0]
            print(f"{winner.name} wins the pot of {pot} chips (other bots folded).")
            winner.stack += pot
            return

    scores = {}
    for bot in bots:
        score = evaluator.evaluate_hand(bot.hand, community_cards)
        scores[bot] = score

    winner = min(scores, key=scores.get)
    print(f"\nWinner: {winner} with hand {winner.hand}. Wins pot of {pot} chips!")
    winner.stack += pot





def run_texas_holdem(rounds=10):
    bots = [
        PokerBot("AggressiveBot", AggressiveStrategy(), stack=200),
        PokerBot("ConservativeBot", ConservativeStrategy(), stack=200),
        PokerBot("AllInBot", AllIn(), stack=200),
        PokerBot("RandomBot", RandomStrategy(), stack=200)
    ]

    # Initialize hand evaluator
    evaluator = PokerHandEvaluator()

    for round_num in range(1, rounds + 1):
        print(f"\n=== Round {round_num} ===")
        deck = PokerDeck()
        deck.shuffle()
        play_hand(deck, bots, evaluator)

        # Display bot standings after each round
        print("\nChip standings:")
        for bot in bots:
            print(f"{bot.name}: {bot.stack} chips")

    # Determine the overall winner
    overall_winner = max(bots, key=lambda bot: bot.stack)
    print(f"\nOverall Winner: {overall_winner} with {overall_winner.stack} chips!")


if __name__ == "__main__":
    run_texas_holdem(rounds=10)
