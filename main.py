from mechanics import PokerDeck
from deck import PokerHandEvaluator
from logic import PokerBot
from strategies import AggressiveStrategy, ConservativeStrategy, RandomStrategy, AllIn


# === DISPLAY FUNCTIONS ===
def display_hand(bot):
    """Displays the bot's hand in a formatted way."""
    print(f"{bot.name} has: {', '.join(bot.hand)}")

def display_community_cards(community_cards):
    """Displays the community cards in a formatted way."""
    print("\nCommunity Cards: " + (", ".join(community_cards) if community_cards else "None"))
    print("")


# === POSITION ASSIGNMENT FUNCTION ===
def assign_positions(bots):
    """Assign positions dynamically based on the number of bots."""
    positions = ['Early', 'Middle', 'Late']
    num_bots = len(bots)

    for i, bot in enumerate(bots):
        if num_bots >= 3:
            bot.position = positions[i % 3]  # Assign Early, Middle, Late cyclically
        elif num_bots == 2:
            bot.position = 'Middle' if i == 0 else 'Late'  # Heads-up
        else:
            bot.position = 'Late'  # Only one player left




def betting_round(bots, minimum_bet=10, community_cards=[], stage="Pre-flop", big_blind_position=0):
    """Handles a full betting round while ensuring bots who fold do not reappear in later rounds."""

    MAX_RAISES = {'Pre-flop': 3, 'Flop': 2, 'Turn': 1, 'River': 1}
    raise_limit = MAX_RAISES.get(stage, 2)

    pot = 0
    active_bots = [bot for bot in bots if bot.stack > 0 and not getattr(bot, "folded", False)]
    current_bet = minimum_bet
    raise_count = 0
    last_raiser = None

    # Assign blinds only if two or more bots remain
    if len(active_bots) >= 2:
        small_blind_position = (big_blind_position - 1) % len(active_bots)
        big_blind_position = big_blind_position % len(active_bots)

        small_blind = active_bots[small_blind_position]
        big_blind = active_bots[big_blind_position]

        small_blind_bet = min(small_blind.stack, minimum_bet // 2)
        big_blind_bet = min(big_blind.stack, minimum_bet)

        small_blind.bet(small_blind_bet)
        big_blind.bet(big_blind_bet)

        pot += (big_blind_bet + small_blind_bet)

    # Betting starts AFTER the Big Blind
    if len(active_bots) == 0:
        print("\n🚨 No active players left. Ending round early.")
        return pot, []

    starting_index = (big_blind_position + 1) % len(active_bots)
    betting_order = active_bots[starting_index:] + active_bots[:starting_index]

    while len(active_bots) > 1:
        betting_complete = True
        bots_to_remove = set()

        for bot in betting_order[:]:  # Iterate over a copy
            if getattr(bot, "folded", False) or bot.stack <= 0:
                continue  # Skip bots that are already out

            game_state = {
                "bot": bot,
                "community_cards": community_cards,
                "pot": pot,
                "minimum_bet": current_bet,
                "money_committed": bot.current_bet,
                "num_opponents": len(active_bots) - 1,
                "raise_count": raise_count
            }

            decision = bot.strategy.decide(game_state, bot.hand)
            if not isinstance(decision, tuple) or len(decision) != 2:
                print(f"🚨 ERROR: {bot.name}'s strategy returned an invalid decision: {decision}")
                decision = ("fold", 0)  # Default to fold

            action, amount = decision
            amount = min(amount, bot.stack)  # Prevent betting more than available stack

            # **FOLD**
            if action == "fold":
                if not bot.folded:  # Print only the first time
                    print(f"{bot.name} 🏳️ folds.")
                bot.folded = True
                bots_to_remove.add(bot)
                continue

            # **CALL**
            elif action == "call" and bot.current_bet < current_bet:
                call_amount = min(current_bet - bot.current_bet, bot.stack)
                if call_amount > 0:
                    placed_bet = bot.bet(call_amount)
                    pot += placed_bet
                    print(f"{bot.name} 🔵 calls with {placed_bet} chips. (Pot: {pot})")
                    betting_complete = False
            # **ALL-IN**
            elif action == "allin":
                all_in_amount = bot.stack  # Bet entire stack
                placed_bet = bot.bet(all_in_amount)
                pot += placed_bet
                current_bet = max(current_bet, placed_bet)  # Update the current bet

                bot.allin = True  # Mark bot as all-in
                raise_count += 1  # Treat all-in as a final raise

                print(f"{bot.name} 💥 goes ALL-IN with {placed_bet} chips! (Pot: {pot})")
            # **RAISE**
            elif action == "raise" and raise_count < raise_limit:
                raise_amount = min(amount, bot.stack)
                if raise_amount > 0:
                    placed_bet = bot.bet(raise_amount)
                    pot += placed_bet
                    current_bet = placed_bet
                    raise_count += 1
                    betting_complete = False
                    last_raiser = bot
                    print(f"{bot.name} 🔺 raises with {placed_bet} chips. (Pot: {pot})")

            # **CHECK**
            elif bot.current_bet == current_bet:
                print(f"{bot.name} ✅ checks.")

        # Remove folded bots permanently
        active_bots = [bot for bot in active_bots if bot not in bots_to_remove]

        # If only one bot remains, award the pot
        if len(active_bots) == 1:
            winner = active_bots[0]
            print(f"\n🏆 {winner.name} wins the pot of {pot} chips! (All others folded)")
            winner.stack += pot
            return pot, []

        # Ensure last raiser is considered for next betting round
        if last_raiser:
            betting_order = [bot for bot in active_bots if bot != last_raiser] + [last_raiser]

        # If betting is complete, exit loop
        if betting_complete:
            break

    # Reset all betting amounts
    for bot in bots:
        bot.reset_bet()

    return pot, active_bots






# === PLAY HAND FUNCTION ===
def play_hand(deck, bots, evaluator, big_blind_position):
    community_cards = []
    stages = ['Pre-flop', 'Flop', 'Turn', 'River']
    cards_to_deal = [0, 3, 1, 1]

    # Reset statuses before the hand starts
    for bot in bots:
        bot.folded = False
        bot.allin = False
        bot.set_hand(deck.deal(2))

    # ✅ Correct Initial Pot Calculation
    pot = 0  # Start at zero and add only NEW bets
    print(f"🪙 Initial Pot: 15 chips")

    any_allin = False  # Track if an all-in occurs

    for stage, num_cards in zip(stages, cards_to_deal):
        if num_cards > 0:
            community_cards.extend(deck.deal(num_cards))

        print(f"\n===== {stage} =====")
        display_community_cards(community_cards)

        active_bots = [bot for bot in bots if not bot.folded or bot.allin]

        for bot in active_bots:
            display_hand(bot)

        # **Skip betting if at least one player is all-in**
        if any(bot.allin for bot in active_bots):
            any_allin = True
            continue

        # **Run normal betting round**
        pot_round, active_bots = betting_round(
            active_bots, minimum_bet=10, community_cards=community_cards, stage=stage, big_blind_position=big_blind_position
        )
        pot += pot_round

        # If only one player remains, they win automatically
        if len(active_bots) == 1:
            winner = active_bots[0]
            print(f"\n🏆 {winner.name} wins the pot of {pot} chips! (Other bots folded)")
            winner.stack += pot
            return

    # **Showdown Handling**
    print("\n🏆 Showdown Time! Evaluating the best hand...")

    # ✅ Properly Handle Side Pots
    sorted_bots = sorted(active_bots, key=lambda bot: bot.current_bet)
    allin_bets = sorted(set(bot.current_bet for bot in active_bots))
    side_pots = {}
    last_bet = 0

    for bet in allin_bets:
        side_pots[bet] = sum(min(bot.current_bet - last_bet, bet - last_bet) for bot in active_bots)
        last_bet = bet

    awarded_chips = {bot: 0 for bot in bots}
    remaining_pot = pot

    # ✅ Correct Side Pot Distribution
    for bet in allin_bets:
        eligible_bots = [bot for bot in sorted_bots if bot.current_bet >= bet]
        best_hands = {bot: evaluator.get_best_hand(bot.hand, community_cards) for bot in eligible_bots}
        winner = max(best_hands, key=lambda bot: evaluator.evaluate_hand(bot.hand, community_cards))

        if side_pots[bet] > 0:
            print(f"\n🏆 Winner: {winner.name} wins {side_pots[bet]} chips from a side pot with {best_hands[winner][1]}! ({', '.join(map(str, best_hands[winner][0]))})")
            winner.stack += side_pots[bet]
            awarded_chips[winner] += side_pots[bet]
            remaining_pot -= side_pots[bet]

    # ✅ Prevent Extra Chips from Being Awarded
    if remaining_pot > 0:
        remaining_bots = [bot for bot in sorted_bots if bot not in awarded_chips or awarded_chips[bot] == 0]
        if remaining_bots:
            final_winner = max(remaining_bots, key=lambda bot: evaluator.evaluate_hand(bot.hand, community_cards))
            print(f"\n🏆 Final Winner: {final_winner.name} wins remaining {remaining_pot} chips!")
            final_winner.stack += remaining_pot

    # ✅ Prevent Double Deduction of Blinds
    for bot in bots:
        if bot.folded and bot.current_bet == 10:
            bot.stack += 10  # Fix excess deduction

    # **Final Chip Standings**
    print("\n💰 Final Chip Standings:")
    for bot in bots:
        print(f"  {bot.name}: {bot.stack} chips")











# === RUN GAME FUNCTION ===
def run_texas_holdem(rounds=10):
    bots = [
        PokerBot("AggressiveBot", AggressiveStrategy(), stack=200),
        PokerBot("ConservativeBot", ConservativeStrategy(), stack=200),
        PokerBot("AllInBot", AllIn(), stack=200),
        PokerBot("RandomBot", RandomStrategy(), stack=200)
    ]

    evaluator = PokerHandEvaluator()
    dealer_position = 0  # Tracks who is the dealer, rotates every round

    for round_num in range(1, rounds + 1):
        if len(bots) <= 1:  # If only one bot remains, game ends
            break

        print(f"\n==========================")
        print(f"       ROUND {round_num}     ")
        print(f"==========================")

        deck = PokerDeck()
        deck.shuffle()

        # Remove eliminated bots (stack = 0)
        bots = [bot for bot in bots if bot.stack > 0]

        if len(bots) < 2:
            break  # Not enough players to continue

        # Assign blinds before dealing cards
        small_blind_position = dealer_position % len(bots)
        big_blind_position = (dealer_position + 1) % len(bots)

        small_blind_amount = 5
        big_blind_amount = 10

        bots[small_blind_position].bet(small_blind_amount)
        bots[big_blind_position].bet(big_blind_amount)

        print(f"{bots[small_blind_position].name} posts the Small Blind ({small_blind_amount} chips).")
        print(f"{bots[big_blind_position].name} posts the Big Blind ({big_blind_amount} chips).\n")

        # Deal hole cards **after** blinds are posted
        play_hand(deck, bots, evaluator, big_blind_position)

        dealer_position += 1  # Rotate dealer for next round

        # Display bot standings
        print("\n💰 Chip Standings:")
        for bot in bots:
            print(f"  {bot.name}: {bot.stack} chips")

    # Determine overall winner
    if len(bots) == 1:
        print(f"\n🏆 FINAL WINNER: {bots[0].name} with {bots[0].stack} chips!")


# === MAIN EXECUTION ===
if __name__ == "__main__":
    run_texas_holdem(rounds=10)
