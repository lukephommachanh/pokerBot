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


# === BETTING ROUND FUNCTION ===
def betting_round(bots, minimum_bet=10, community_cards=[], stage="Pre-flop", big_blind_position=0):
    """
    Handles a full betting round, ensuring that bots act in correct order,
    follow the betting rules, and avoid miscommunications.
    """
    MAX_RAISES = {'Pre-flop': 3, 'Flop': 2, 'Turn': 1, 'River': 1}
    raise_limit = MAX_RAISES.get(stage, 2)

    pot = 0
    active_bots = [bot for bot in bots if bot.stack > 0]
    current_bet = minimum_bet
    raise_count = 0

    # Assign blinds
    if len(active_bots) >= 2:
        small_blind_position = (big_blind_position - 1) % len(active_bots)
        big_blind_position = big_blind_position % len(active_bots)

        small_blind = active_bots[small_blind_position]
        big_blind = active_bots[big_blind_position]

        small_blind.bet(minimum_bet // 2)  # Small Blind
        big_blind.bet(minimum_bet)  # Big Blind

        #print(f"{small_blind.name} posts the Small Blind ({minimum_bet // 2} chips).")
        #print(f"{big_blind.name} posts the Big Blind ({minimum_bet} chips).\n")

        pot += (minimum_bet + minimum_bet // 2)

    # Betting starts **AFTER** the Big Blind
    starting_index = (big_blind_position + 1) % len(active_bots)
    betting_order = active_bots[starting_index:] + active_bots[:starting_index]

    print("")

    while len(active_bots) > 1:
        betting_complete = True  # Assume betting is complete unless a raise occurs
        bots_to_remove = []

        for bot in betting_order:
            if bot.stack <= 0:
                continue  # Skip bots who are all-in

            game_state = {
                'bot': bot,
                'community_cards': community_cards,
                'pot': pot,
                'minimum_bet': current_bet,
                'money_committed': bot.current_bet,
                'num_opponents': len(active_bots) - 1
            }

            action, amount = bot.decide_action(game_state, current_bet)



            # 🏳️ **FOLD LOGIC**
            if action == 'fold':
                print(f"{bot.name} 🏳️ folds.")
                bots_to_remove.append(bot)
                continue  # Move to the next bot

            # 🔵 **CALL LOGIC**
            elif action == 'call':
                call_amount = min(current_bet - bot.current_bet, bot.stack)  # Ensure it's within stack
                placed_bet = bot.bet(call_amount)
                pot += placed_bet
                print(f"{bot.name} 🔵 calls with {placed_bet} chips. (Pot: {pot})")

            # 🔺 **RAISE LOGIC**
            elif action == 'raise' and raise_count < raise_limit:
                raise_amount = max(amount, minimum_bet)
                if raise_amount > bot.stack:
                    raise_amount = bot.stack  # Go all-in if not enough

                total_raise = current_bet + raise_amount
                placed_bet = bot.bet(total_raise - bot.current_bet)

                if placed_bet > 0:
                    pot += placed_bet
                    current_bet = total_raise
                    raise_count += 1
                    betting_complete = False  # Restart the betting cycle
                    print(f"{bot.name} 🔺 raises with {placed_bet} chips. (Pot: {pot})")

            # 🚫 **DEFAULT TO CHECK**
            else:
                print(f"{bot.name} ✅ checks.")

        # Remove folded bots
        for bot in bots_to_remove:
            active_bots.remove(bot)

        # If only one player remains, they instantly win the pot
        if len(active_bots) == 1:
            winner = active_bots[0]
            print(f"\n🏆 {winner.name} wins the pot of {pot} chips! (All others folded)")
            winner.stack += pot
            return pot, []

        if betting_complete:
            break  # Exit loop if no raises happened

    # Reset betting amounts for the next round
    for bot in bots:
        bot.reset_bet()

    return pot, active_bots


# === PLAY HAND FUNCTION ===
def play_hand(deck, bots, evaluator, big_blind_position):
    community_cards = []
    stages = ['Pre-flop', 'Flop', 'Turn', 'River']
    cards_to_deal = [0, 3, 1, 1]

    # Deal hole cards **after** blinds are posted
    for bot in bots:
        bot.set_hand(deck.deal(2))

    pot = sum(bot.current_bet for bot in bots)  # Start pot with blinds

    for stage, num_cards in zip(stages, cards_to_deal):
        if num_cards > 0:
            community_cards.extend(deck.deal(num_cards))

        print(f"\n===== {stage} =====")
        display_community_cards(community_cards)

        for bot in bots:
            display_hand(bot)

        # Betting starts **after** blinds have already been posted
        pot_round, active_bots = betting_round(
            bots, minimum_bet=10, community_cards=community_cards, stage=stage, big_blind_position=big_blind_position
        )
        pot += pot_round

        # If only one player remains, **end the hand immediately**
        if len(active_bots) == 1:
            winner = active_bots[0]
            print(f"\n🏆 {winner.name} wins the pot of {pot} chips! (Other bots folded)")
            winner.stack += pot
            return  # **Skip Turn & River**

    # If multiple players reach showdown, evaluate the best hand
    best_hands = {}
    for bot in bots:
        best_hand, hand_type = evaluator.get_best_hand(bot.hand, community_cards)
        best_hands[bot] = (best_hand, hand_type)

    # Determine the winner based on hand strength
    winner = min(best_hands, key=lambda bot: evaluator.evaluate_hand(bot.hand, community_cards))

    # Get the winner's best hand and hand type
    winning_hand, winning_hand_type = best_hands[winner]

    # Display winning hand details
    print(f"\n🏆 Winner: {winner.name} with a {winning_hand_type}! ({', '.join(map(str, winning_hand))})")
    print(f"💰 Wins {pot} chips!")
    winner.stack += pot

# === RUN GAME FUNCTION ===
def run_texas_holdem(rounds= 1):
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

        # Remove eliminated bots
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
    else:
        overall_winner = max(bots, key=lambda bot: bot.stack)
        print(f"\n🏆 Overall Winner: {overall_winner.name} with {overall_winner.stack} chips!")



# === MAIN EXECUTION ===
if __name__ == "__main__":
    run_texas_holdem(rounds=1)
