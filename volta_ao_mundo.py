import random

# --- GAME DATA & DEFINITIONS ---
DECK_COMP_DICT = {
    '1000': 10, '2000': 10, '3000': 10, '4000': 12, '8000': 4,
    'Orientacao': 14, 'Trabalho': 6, 'Fuga': 6, 'Remedio': 6,
    'Perdido': 5, 'Fim do Dinheiro': 3, 'Povos Hostis': 3, 'Epidemia': 3,
    'Civilizada': 5, 'Selvagem': 4, 'Mar': 4, 'Sem Recursos': 3,
    'Saude': 1, 'Diplomacia': 1, 'Riqueza': 1, 'Rotas Alternativas': 1
}

CURES = {
    'Perdido': 'Orientacao',
    'Fim do Dinheiro': 'Trabalho',
    'Povos Hostis': 'Fuga',
    'Epidemia': 'Remedio'
}

DEFENSES = {
    'Epidemia': 'Saude',
    'Povos Hostis': 'Diplomacia',
    'Fim do Dinheiro': 'Riqueza',
    'Perdido': 'Rotas Alternativas'
}

TERRAIN_RULES = {
    'Civilizada': ['1000', '2000', '4000', '8000'],
    'Selvagem': ['1000', '2000', '8000'],
    'Mar': ['3000', '8000'],
    'Sem Recursos': ['1000']
}

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.distance = 0
        self.cards_played_distance = []
        self.active_hazard = None
        self.terrain = 'Civilizada'
        self.defenses_active = []
        self.has_orientacao = False

        # Stats tracking
        self.attacks_launched = 0
        self.cures_played = 0
        self.counter_attacks = 0
        self.score = 0
        self.turns_played = 0

class VoltaAoMundoSim:
    def __init__(self):
        self.deck = []
        for card, count in DECK_COMP_DICT.items():
            self.deck.extend([card] * count)
        random.shuffle(self.deck)
        self.discard_pile = []
        self.p1 = Player("Player 1")
        self.p2 = Player("Player 2")

        # Deal 6 cards
        for _ in range(6):
            self.p1.hand.append(self.draw())
            self.p2.hand.append(self.draw())

    def draw(self):
        if not self.deck:
            return None
        return self.deck.pop()

    def can_move(self, player):
        if player.active_hazard:
            return False
        if not player.has_orientacao and 'Rotas Alternativas' not in player.defenses_active:
            return False
        return True

    def take_turn(self, player, opponent):
        # Draw a card at the start of the turn
        drawn_card = self.draw()
        if drawn_card:
            player.hand.append(drawn_card)

        # If hand is empty (and deck was empty), nothing to do
        if not player.hand:
            return

        player.turns_played += 1
        action_taken = False

        # --- Decision Logic ---

        # 1. Play Defense (if holding one that matches active hazard OR just to be safe/score)
        defenses_in_hand = [c for c in player.hand if c in ['Saude', 'Diplomacia', 'Riqueza', 'Rotas Alternativas']]

        # Priority: Cure active hazard with defense
        for d in defenses_in_hand:
            # Find which hazard this defense cures
            hazard_for_defense = [h for h, df in DEFENSES.items() if df == d][0]
            if player.active_hazard == hazard_for_defense:
                self.play_defense(player, d)
                action_taken = True
                break

        if not action_taken and defenses_in_hand:
            # Play defense for points/immunity even if no hazard
            # Prefer playing 'Rotas Alternativas' if we need orientation
            if 'Rotas Alternativas' in defenses_in_hand and not player.has_orientacao:
                d = 'Rotas Alternativas'
            else:
                d = defenses_in_hand[0] # Pick first available
            self.play_defense(player, d)
            action_taken = True

        # 2. Cure Hazard with Green Card
        if not action_taken and player.active_hazard:
            required_cure = CURES.get(player.active_hazard)
            if required_cure and required_cure in player.hand:
                self.play_cure(player, required_cure)
                action_taken = True

        # 3. Play Orientacao
        # If we need orientation (and have no hazard or cured it but need Orientacao)
        if not action_taken and not player.active_hazard and not player.has_orientacao and 'Rotas Alternativas' not in player.defenses_active:
            if 'Orientacao' in player.hand:
                self.play_orientacao(player)
                action_taken = True

        # 4. Travel
        if not action_taken and self.can_move(player):
            allowed_distances = TERRAIN_RULES[player.terrain]
            if 'Rotas Alternativas' in player.defenses_active:
                allowed_distances = ['1000', '2000', '3000', '4000', '8000']

            balloons_played = player.cards_played_distance.count('8000')
            travel_candidates = []

            # Identify playable distance cards
            # Must handle multiple copies in hand
            unique_hand = set(player.hand)
            for card in unique_hand:
                if card in ['1000', '2000', '3000', '4000', '8000']:
                    if card in allowed_distances:
                        if card == '8000' and balloons_played >= 2:
                            continue
                        if player.distance + int(card) <= 40000:
                            travel_candidates.append(card)

            if travel_candidates:
                # Pick largest distance usually better
                travel_candidates.sort(key=lambda x: int(x), reverse=True)
                card = travel_candidates[0]
                self.play_travel(player, card)
                action_taken = True

        # 5. Attack (Hazard)
        if not action_taken:
            hazards_in_hand = [c for c in player.hand if c in ['Epidemia', 'Povos Hostis', 'Fim do Dinheiro', 'Perdido']]
            possible_attacks = []
            for h in hazards_in_hand:
                if opponent.active_hazard is None:
                    defense_needed = DEFENSES[h]
                    if defense_needed not in opponent.defenses_active:
                        possible_attacks.append(h)

            if possible_attacks:
                attack_card = random.choice(possible_attacks)
                self.play_attack(player, opponent, attack_card)
                action_taken = True

        # 6. Change Terrain
        if not action_taken:
            terrains = ['Civilizada', 'Selvagem', 'Mar', 'Sem Recursos']
            terrains_in_hand = [c for c in player.hand if c in terrains]
            possible_terrains = []
            for t in terrains_in_hand:
                if opponent.terrain != t and 'Rotas Alternativas' not in opponent.defenses_active:
                    possible_terrains.append(t)

            if possible_terrains:
                t = random.choice(possible_terrains)
                self.play_terrain(player, opponent, t)
                action_taken = True

        # 7. Discard
        if not action_taken:
            # Discard strategy:
            # 1. Duplicate unique cards (defenses) - unlikely since we play them.
            # 2. Unplayable hazards (if opponent immune).
            # 3. Weak distance cards?
            # 4. Random.

            # Simple safe discard logic
            vital = ['Orientacao', 'Saude', 'Diplomacia', 'Riqueza', 'Rotas Alternativas', 'Remedio', 'Fuga', 'Trabalho']
            safe_discards = [c for c in player.hand if c not in vital]

            if safe_discards:
                card = random.choice(safe_discards)
            else:
                card = random.choice(player.hand)
            self.discard_card(player, card)

    def play_defense(self, player, card):
        player.hand.remove(card)
        player.defenses_active.append(card)

        # Rotas Alternativas provides permanent orientation
        if card == 'Rotas Alternativas':
            player.has_orientacao = True

        # Check if it cures active hazard
        hazard_for_defense = [h for h, df in DEFENSES.items() if df == card][0]
        if player.active_hazard == hazard_for_defense:
            player.active_hazard = None
            # If not Rotas Alternativas, do we need Orientacao?
            # "Removes the hazard". Doesn't say grants orientation.
            # Assuming standard mechanics: if you were stopped, you need to restart (Orientacao), unless the card itself says otherwise.
            # Rotas Alternativas says it ignores orientation.
            # Others don't. So if I use Saude to cure Epidemia, I am safe, but stationary.
            pass

    def play_cure(self, player, card):
        player.hand.remove(card)
        self.discard_pile.append(card)
        player.cures_played += 1

        if card == 'Orientacao' and player.active_hazard == 'Perdido':
            # Special case: Orientacao cures Perdido and grants orientation
            player.active_hazard = None
            player.has_orientacao = True
        else:
            # Other cures remove hazard but require Orientacao next
            player.active_hazard = None
            player.has_orientacao = False

    def play_orientacao(self, player):
        player.hand.remove('Orientacao')
        self.discard_pile.append('Orientacao')
        player.has_orientacao = True

    def play_travel(self, player, card):
        player.hand.remove(card)
        player.distance += int(card)
        player.cards_played_distance.append(card)
        self.discard_pile.append(card)

    def play_attack(self, player, opponent, card):
        player.hand.remove(card)
        player.attacks_launched += 1

        defense_needed = DEFENSES[card]
        if defense_needed in opponent.hand:
            # Counter-Attack!
            opponent.hand.remove(defense_needed)
            opponent.defenses_active.append(defense_needed)
            opponent.counter_attacks += 1
            if defense_needed == 'Rotas Alternativas':
                opponent.has_orientacao = True

            self.discard_pile.append(card)

            # Opponent gets bonus turn
            # Recursive call? Yes, but check depth/stack?
            # In Python recursion limit is 1000. Unlikely to hit that in one turn chain.
            self.take_turn(opponent, player)
        else:
            opponent.active_hazard = card
            if 'Rotas Alternativas' not in opponent.defenses_active:
                opponent.has_orientacao = False

    def play_terrain(self, player, opponent, card):
        player.hand.remove(card)
        self.discard_pile.append(card)
        opponent.terrain = card
        player.attacks_launched += 1

    def discard_card(self, player, card):
        player.hand.remove(card)
        self.discard_pile.append(card)

    def calculate_scores(self):
        is_deck_empty = len(self.deck) == 0

        for p, opp in [(self.p1, self.p2), (self.p2, self.p1)]:
            score = p.distance

            score += len(p.defenses_active) * 4000
            if len(p.defenses_active) == 4:
                score += 12000

            score += p.counter_attacks * 12000

            # Win Bonuses
            if p.distance == 40000:
                score += 16000
                if '8000' not in p.cards_played_distance:
                    score += 12000
                if is_deck_empty:
                    score += 12000
                if opp.distance == 0:
                    score += 20000

            p.score = score

    def play_game(self):
        while True:
            if self.p1.distance == 40000 or self.p2.distance == 40000:
                self.calculate_scores()
                return self

            if not self.deck and not self.p1.hand and not self.p2.hand:
                self.calculate_scores()
                return self

            # P1 Turn
            if self.deck or self.p1.hand:
                self.take_turn(self.p1, self.p2)
                if self.p1.distance == 40000:
                    self.calculate_scores()
                    return self

            # P2 Turn
            if self.deck or self.p2.hand:
                self.take_turn(self.p2, self.p1)
                if self.p2.distance == 40000:
                    self.calculate_scores()
                    return self

            # Break if no one can move and deck empty (handled by hand check usually)
            if not self.deck and not self.p1.hand and not self.p2.hand:
                self.calculate_scores()
                return self

def run_monte_carlo(iterations=1000):
    results = []

    for i in range(iterations):
        game = VoltaAoMundoSim().play_game()

        winner = None
        if game.p1.distance == 40000: winner = 'P1'
        elif game.p2.distance == 40000: winner = 'P2'
        else: winner = 'Stalemate'

        locked = False
        if (not game.can_move(game.p1) and game.p1.distance < 40000) or \
           (not game.can_move(game.p2) and game.p2.distance < 40000):
            locked = True # At least one player locked at end

        results.append({
            'game_id': i,
            'winner': winner,
            'p1_score': game.p1.score,
            'p2_score': game.p2.score,
            'p1_distance': game.p1.distance,
            'p2_distance': game.p2.distance,
            'turns': game.p1.turns_played + game.p2.turns_played,
            'stalemate': 1 if winner == 'Stalemate' else 0,
            'locked_players': 1 if locked else 0
        })

    return results

if __name__ == "__main__":
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns

    # Run Simulation
    print("Running simulation...")
    data = run_monte_carlo(10000)
    df = pd.DataFrame(data)

    # Save Results
    df.to_csv('simulation_results.csv', index=False)
    print("Results saved to simulation_results.csv")

    # Analysis
    win_counts = df['winner'].value_counts()
    print("\nWin Rates:")
    print(win_counts)

    avg_scores = df[['p1_score', 'p2_score']].mean()
    print("\nAverage Scores:")
    print(avg_scores)

    # Visualizations
    plt.figure(figsize=(8, 6))
    sns.barplot(x=win_counts.index, y=win_counts.values)
    plt.title('Win Rates (10,000 Games)')
    plt.ylabel('Count')
    plt.savefig('win_rates.png')

    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x='p1_score', color='blue', label='P1', kde=True, alpha=0.5)
    sns.histplot(data=df, x='p2_score', color='red', label='P2', kde=True, alpha=0.5)
    plt.title('Score Distribution')
    plt.legend()
    plt.savefig('score_dist.png')

    print("Plots saved.")
