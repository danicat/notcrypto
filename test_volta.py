import unittest
from volta_ao_mundo import Player, VoltaAoMundoSim

class TestVoltaAoMundo(unittest.TestCase):
    def setUp(self):
        self.game = VoltaAoMundoSim()
        # Empty hands to control test
        self.game.p1.hand = []
        self.game.p2.hand = []

    def test_hazard_application(self):
        p1 = self.game.p1
        p2 = self.game.p2

        # P1 has hazard, P2 has no defense in hand or active
        p1.hand = ['Epidemia']
        p2.hand = ['1000'] # Irrelevant card
        p2.defenses_active = []

        self.game.play_attack(p1, p2, 'Epidemia')

        self.assertEqual(p2.active_hazard, 'Epidemia')
        self.assertFalse(p2.has_orientacao)
        self.assertFalse(self.game.can_move(p2))

    def test_cure_logic_normal(self):
        p = self.game.p1
        p.active_hazard = 'Epidemia'
        p.has_orientacao = False
        p.hand = ['Remedio']

        self.game.play_cure(p, 'Remedio')

        self.assertIsNone(p.active_hazard)
        self.assertFalse(p.has_orientacao) # Needs Orientacao next

    def test_cure_logic_perdido(self):
        p = self.game.p1
        p.active_hazard = 'Perdido'
        p.has_orientacao = False
        p.hand = ['Orientacao']

        self.game.play_cure(p, 'Orientacao')

        self.assertIsNone(p.active_hazard)
        self.assertTrue(p.has_orientacao) # Cured and oriented

    def test_counter_attack(self):
        p1 = self.game.p1
        p2 = self.game.p2

        p1.hand = ['Epidemia']
        p2.hand = ['Saude', '1000']

        # Mock p2.take_turn to avoid infinite recursion or random play during test
        original_take_turn = self.game.take_turn
        self.game.take_turn = lambda p, o: None # Do nothing for bonus turn

        self.game.play_attack(p1, p2, 'Epidemia')

        self.game.take_turn = original_take_turn # Restore

        self.assertIn('Saude', p2.defenses_active)
        self.assertIsNone(p2.active_hazard)
        self.assertEqual(p2.counter_attacks, 1)
        self.assertNotIn('Saude', p2.hand)

    def test_scoring_win(self):
        p1 = self.game.p1
        p2 = self.game.p2

        p1.distance = 40000
        p1.defenses_active = ['Saude'] # 4000 pts
        p1.cards_played_distance = ['1000'] # No 8000 bonus (+12000)
        p2.distance = 1000

        # Setup deck to be not empty
        self.game.deck = ['1000']

        self.game.calculate_scores()

        # Base score: 40000 (distance)
        # Defense: +4000
        # Win: +16000
        # No 8000: +12000
        # Deck not empty
        # Not Capote
        # Total: 40000 + 4000 + 16000 + 12000 = 72000

        self.assertEqual(p1.score, 72000)

if __name__ == '__main__':
    unittest.main()
