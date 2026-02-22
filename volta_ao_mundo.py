import random
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- GAME DATA & DEFINITIONS ---
DECK_COMP_DICT = {
    '1000': 10, '2000': 10, '3000': 10, '4000': 12, '8000': 4,
    'Orientacao': 10, 'Trabalho': 6, 'Fuga': 6, 'Remedio': 6,
    'Perdido': 5, 'Fim do Dinheiro': 3, 'Povos Hostis': 3, 'Epidemia': 3,
    'Civilizada': 5, 'Selvagem': 4, 'Mar': 4, 'Sem Recursos': 3,
    'Saude': 1, 'Diplomacia': 1, 'Riqueza': 1, 'Rotas Alternativas': 1
}

CURES = {'Perdido': 'Orientacao', 'Fim do Dinheiro': 'Trabalho', 'Povos Hostis': 'Fuga', 'Epidemia': 'Remedio'}
DEFENSES = {'Epidemia': 'Saude', 'Povos Hostis': 'Diplomacia', 'Fim do Dinheiro': 'Riqueza', 'Perdido': 'Rotas Alternativas'}
TERRAIN_RULES = {
    'Civilizada': ['1000', '2000', '4000', '8000'],
    'Selvagem': ['1000', '2000', '8000'],
    'Mar': ['3000', '8000'],
    'Sem Recursos': ['1000']
}

class Player:
    def __init__(self, name, strategy):
        self.name = name
        self.strategy = strategy
        self.hand = []
        self.distance = 0
        self.cards_played_distance = []
        self.active_hazard = None
        self.terrain = 'Civilizada'
        self.defenses_active = []
        self.has_orientacao = False
        self.counter_attacks = 0
        self.score = 0

class VoltaAoMundoSim:
    def __init__(self, p1_strat, p2_strat):
        self.deck = []
        for card, count in DECK_COMP_DICT.items():
            self.deck.extend([card] * count)
        random.shuffle(self.deck)
        self.discard = []
        self.p1 = Player(f"P1 ({p1_strat})", p1_strat)
        self.p2 = Player(f"P2 ({p2_strat})", p2_strat)

        for _ in range(6):
            self.p1.hand.append(self.draw())
            self.p2.hand.append(self.draw())

    def draw(self):
        return self.deck.pop() if self.deck else None

    def can_move(self, player):
        if player.active_hazard: return False
        # Orientacao no longer required to move unless hazard specifically stops you (Perdido logic handled by active_hazard)
        return True

    def get_legal_moves(self, player, opponent):
        moves = []
        for d in ['Saude', 'Diplomacia', 'Riqueza', 'Rotas Alternativas']:
            if d in player.hand: moves.append(('defense', d))

        if player.active_hazard and CURES[player.active_hazard] in player.hand:
            moves.append(('cure', CURES[player.active_hazard]))

        # Still need Orientacao to cure Perdido, or if player wants to play it (maybe for points/discard/stats?)
        # But strictly speaking, if not required for movement, is it playable as an action?
        # Usually yes, as a "green card" action.
        if 'Orientacao' in player.hand:
            moves.append(('orientacao', 'Orientacao'))

        if self.can_move(player):
            allowed = TERRAIN_RULES[player.terrain]
            if 'Rotas Alternativas' in player.defenses_active: allowed = ['1000', '2000', '3000', '4000', '8000']
            balloons = player.cards_played_distance.count('8000')
            for card in set(player.hand):
                if card in allowed:
                    if card == '8000' and balloons >= 2: continue
                    # STRICT 40K ENFORCEMENT
                    if player.distance + int(card) <= 40000: moves.append(('travel', card))

        for hazard in ['Epidemia', 'Povos Hostis', 'Fim do Dinheiro', 'Perdido']:
            if hazard in player.hand and opponent.active_hazard is None and DEFENSES[hazard] not in opponent.defenses_active:
                moves.append(('attack_hazard', hazard))

        for t in ['Civilizada', 'Selvagem', 'Mar', 'Sem Recursos']:
            if t in player.hand and opponent.terrain != t and 'Rotas Alternativas' not in opponent.defenses_active:
                moves.append(('attack_terrain', t))
        return moves

    def take_turn(self, player, opponent):
        drawn_card = self.draw()
        if drawn_card: player.hand.append(drawn_card)
        if not player.hand: return

        legal_moves = self.get_legal_moves(player, opponent)
        chosen_action = None

        if player.strategy == 'random':
            all_possible = legal_moves + [('discard', c) for c in set(player.hand)]
            chosen_action = random.choice(all_possible)
        else: # Tiered
            defenses = [m for m in legal_moves if m[0] == 'defense']
            cures = [m for m in legal_moves if m[0] == 'cure']
            orientacaos = [m for m in legal_moves if m[0] == 'orientacao']
            travels = [m for m in legal_moves if m[0] == 'travel']
            # Sort travels descending
            travels.sort(key=lambda x: int(x[1]), reverse=True)
            attacks = [m for m in legal_moves if m[0] in ['attack_hazard', 'attack_terrain']]

            if defenses: chosen_action = random.choice(defenses)
            elif cures: chosen_action = random.choice(cures)
            elif orientacaos: chosen_action = random.choice(orientacaos)
            elif travels: chosen_action = travels[0] # Pick best distance
            elif attacks: chosen_action = random.choice(attacks)
            else:
                vital = ['Orientacao', 'Saude', 'Diplomacia', 'Riqueza', 'Rotas Alternativas', 'Remedio', 'Fuga', 'Trabalho']
                safe = [c for c in player.hand if c not in vital]
                chosen_action = ('discard', random.choice(safe) if safe else random.choice(player.hand))

        action, card = chosen_action
        player.hand.remove(card)

        if action == 'defense':
            player.defenses_active.append(card)
            if card == 'Rotas Alternativas': player.has_orientacao = True
            if self.deck: self.take_turn(player, opponent)

        elif action == 'cure':
            self.discard.append(card)
            player.active_hazard = None
            if card != 'Orientacao': player.has_orientacao = False

        elif action == 'orientacao':
            self.discard.append(card)
            player.has_orientacao = True

        elif action == 'attack_hazard':
            defense_needed = DEFENSES[card]
            if defense_needed in opponent.hand:
                will_counter = random.choice([True, False]) if opponent.strategy == 'random' else True
                if will_counter:
                    self.discard.append(card)
                    opponent.hand.remove(defense_needed)
                    opponent.defenses_active.append(defense_needed)
                    opponent.counter_attacks += 1
                    if defense_needed == 'Rotas Alternativas': opponent.has_orientacao = True
                    self.take_turn(opponent, player)
                    return
            opponent.active_hazard = card

        elif action == 'attack_terrain':
            self.discard.append(card)
            opponent.terrain = card

        elif action == 'travel':
            player.distance += int(card)
            player.cards_played_distance.append(card)
            self.discard.append(card)

        elif action == 'discard':
            self.discard.append(card)

    def calculate_scores(self):
        is_deck_empty = len(self.deck) == 0
        for p, opp in [(self.p1, self.p2), (self.p2, self.p1)]:
            score = p.distance
            score += len(p.defenses_active) * 4000
            if len(p.defenses_active) == 4: score += 12000
            score += p.counter_attacks * 12000
            if p.distance == 40000:
                score += 16000
                if '8000' not in p.cards_played_distance: score += 12000
                if is_deck_empty: score += 12000
                if opp.distance == 0: score += 20000
            p.score = score

    def play_game(self):
        while True:
            if self.p1.distance == 40000 or self.p2.distance == 40000:
                self.calculate_scores()
                return self
            if not self.deck and not self.p1.hand and not self.p2.hand:
                self.calculate_scores()
                return self

            if self.deck or self.p1.hand: self.take_turn(self.p1, self.p2)
            if self.p1.distance == 40000:
                self.calculate_scores()
                return self

            if self.deck or self.p2.hand: self.take_turn(self.p2, self.p1)

def run_matchup(strat1, strat2, iterations=5000):
    p1_wins, p2_wins, stalemates = 0, 0, 0
    total_score_p1, total_score_p2 = 0, 0
    locked_players = 0

    for i in range(iterations):
        game = VoltaAoMundoSim(strat1, strat2).play_game()
        if game.p1.distance == 40000: p1_wins += 1
        elif game.p2.distance == 40000: p2_wins += 1
        else: stalemates += 1

        total_score_p1 += game.p1.score
        total_score_p2 += game.p2.score

        # Check if players were locked (could not move) at end of game
        # Simple heuristic: if distance < 40000 and has cards but cannot move?
        # Or just use the fact they didn't win.
        # But 'stalemate' covers it.
        # Let's verify 'locked' concept. The prompt says "Generate... Stalemate/Lock rates".
        # Stalemate is when game ends without a winner.
        pass

    return {
        "Matchup": f"{strat1} vs {strat2}",
        "P1 Wins": p1_wins,
        "P2 Wins": p2_wins,
        "Stalemates": stalemates,
        "P1 Avg Score": total_score_p1 / iterations,
        "P2 Avg Score": total_score_p2 / iterations
    }

if __name__ == "__main__":
    print("Running simulations...")
    results = [
        run_matchup('tiered', 'tiered', 5000),
        run_matchup('tiered', 'random', 5000),
        run_matchup('random', 'random', 5000)
    ]
    df = pd.DataFrame(results)
    print("\n--- Simulation Results ---")
    print(df)

    df.to_csv('simulation_results.csv', index=False)
    print("\nResults saved to simulation_results.csv")

    # Plotting
    # 1. Stalemate Rates
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Matchup', y='Stalemates', data=df)
    plt.title('Stalemate Count by Matchup (5000 Games)')
    plt.ylabel('Number of Stalemates')
    plt.tight_layout()
    plt.savefig('stalemate_comparison.png')

    # 2. Win Rates (Stacked Bar)
    win_data = df[['Matchup', 'P1 Wins', 'P2 Wins', 'Stalemates']].set_index('Matchup')
    win_data.plot(kind='bar', stacked=True, figsize=(10, 6))
    plt.title('Game Outcome Distribution by Matchup')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig('win_rate_comparison.png')

    print("Plots saved: stalemate_comparison.png, win_rate_comparison.png")
