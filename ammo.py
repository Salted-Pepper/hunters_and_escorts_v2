class Ammunition:
    def __init__(self, attacker: str, attacker_skill: str, defender: str,
                 weapon_range: float, stock: int):
        self.attacker = attacker
        self.attacker_skill = attacker_skill
        self.defender = defender
        self.range = weapon_range
        self.stock = stock
