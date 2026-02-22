import unittest
from volta_ao_mundo import Player, VoltaAoMundoSim

class TestVoltaAoMundo(unittest.TestCase):
    def setUp(self):
        # Default strategies to 'tiered' for testing unless specified
        self.game = VoltaAoMundoSim('tiered', 'tiered')
        self.game.p1.hand = []
        self.game.p2.hand = []

    def test_hazard_application(self):
        p1 = self.game.p1
        p2 = self.game.p2

        p1.hand = ['Epidemia']
        p2.hand = ['1000']
        p2.defenses_active = []

        # Manually invoke turn logic or helper if needed.
        # But here we can simulate the attack logic by calling the method that handles it?
        # The new code puts logic inside `take_turn`.
        # We can test `take_turn` by setting up the state.

        # P1 needs to choose attack.
        # Tiered strategy: Defense > Cure > Orient > Travel > Attack.
        # So P1 should attack if no other options.
        # But P1 needs to draw. `take_turn` draws.
        # We can mock `draw` to return None so hand doesn't change unexpectedly.
        self.game.draw = lambda: None

        self.game.take_turn(p1, p2)

        self.assertEqual(p2.active_hazard, 'Epidemia')

    def test_strict_40k_rule(self):
        p1 = self.game.p1
        p2 = self.game.p2

        p1.distance = 38000
        p1.has_orientacao = True
        p1.active_hazard = None
        p1.terrain = 'Civilizada'

        # 3000 would exceed 40000 (38000 + 3000 = 41000) -> Should NOT play
        # 2000 would fit exactly (40000) -> Should play

        p1.hand = ['3000']
        self.game.draw = lambda: None

        # Tiered strategy should NOT play 3000 because it's not a legal move
        # It should discard instead.
        self.game.take_turn(p1, p2)

        self.assertEqual(p1.distance, 38000)
        self.assertEqual(len(self.game.discard), 1)
        self.assertEqual(self.game.discard[0], '3000')

        # Now give 2000
        p1.hand = ['2000']
        self.game.take_turn(p1, p2)
        self.assertEqual(p1.distance, 40000)

    def test_counter_attack_logic(self):
        # We need to test if counter attack happens.
        # P1 attacks P2. P2 has Defense.
        p1 = self.game.p1
        p2 = self.game.p2

        p1.hand = ['Epidemia']
        p2.hand = ['Saude'] # Defense for Epidemia
        self.game.draw = lambda: None

        # P2 is 'tiered', so `will_counter` is True.

        # We need to mock P2's turn to prevent recursion loop or random actions
        # But `take_turn` calls `self.take_turn(opponent, player)` for bonus turn.
        # We can let it run once.

        # To avoid infinite recursion if P2 draws/plays repeatedly, ensure deck is empty or mocked.
        # Deck is already empty since `draw` returns None.

        self.game.take_turn(p1, p2)

        # P2 should have played Saude out of turn
        self.assertIn('Saude', p2.defenses_active)
        self.assertNotIn('Saude', p2.hand)
        # P2 counter_attacks count should increase
        self.assertEqual(p2.counter_attacks, 1)

if __name__ == '__main__':
    unittest.main()
