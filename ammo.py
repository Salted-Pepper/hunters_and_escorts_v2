class Ammunition:
    def __init__(self, attacker: str, attacker_skill: str, defender: str,
                 weapon_range: float, stock: int):
        self.attacker = attacker
        self.attacker_skill = attacker_skill
        self.defender = defender
        self.range = weapon_range
        self.stock = stock

    def __str__(self):
        return f"Ammunition for {self.attacker} w/ {self.attacker_skill} vs {self.defender} - stock is {self.stock}"
