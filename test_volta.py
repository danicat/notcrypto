import unittest
from volta_ao_mundo import Player, VoltaAoMundoSim

class TestVoltaAoMundo(unittest.TestCase):
    def setUp(self):
        # Default strategies to 'tiered' for testing unless specified
        self.game = VoltaAoMundoSim('tiered', 'tiered')
        self.game.p1.hand = []
        self.game.p2.hand = []

    def test_movement_without_orientacao(self):
        p1 = self.game.p1
        p1.has_orientacao = False
        p1.active_hazard = None
        p1.defenses_active = []

        # Should be able to move
        self.assertTrue(self.game.can_move(p1))

        p1.hand = ['1000']
        self.game.draw = lambda: None

        # Play 1000
        self.game.take_turn(p1, self.game.p2)

        self.assertEqual(p1.distance, 1000)

    def test_perdido_stops_movement(self):
        p1 = self.game.p1
        p1.active_hazard = 'Perdido'
        p1.has_orientacao = False

        self.assertFalse(self.game.can_move(p1))

        # Cure with Orientacao
        p1.hand = ['Orientacao']
        # Mock CURES logic in case needed? No, built-in.

        self.game.draw = lambda: None

        # play_cure('Orientacao') should happen
        self.game.take_turn(p1, self.game.p2)

        self.assertIsNone(p1.active_hazard)
        # Should be able to move next turn
        self.assertTrue(self.game.can_move(p1))

    def test_other_hazard_stops_movement(self):
        p1 = self.game.p1
        p1.active_hazard = 'Epidemia'
        self.assertFalse(self.game.can_move(p1))

    def test_strict_40k_rule(self):
        p1 = self.game.p1
        p2 = self.game.p2
        p1.distance = 38000

        p1.hand = ['3000']
        self.game.draw = lambda: None

        # Should discard
        self.game.take_turn(p1, p2)
        self.assertEqual(p1.distance, 38000)
        self.assertEqual(self.game.discard[-1], '3000')

if __name__ == '__main__':
    unittest.main()
