from typing import Tuple, Set


class Store:
    """An object to store probabilities for each (relation, tuple) pair."""

    def __init__(self):
        self.probabilities = {}
        self.arities = {}

    def add(self, relation: str, tuple_: Tuple[str, ...], probability: float):
        if relation not in self.arities:
            self.arities[relation] = len(tuple_)
        elif self.arities[relation] != len(tuple_):
            raise ValueError('Arity does not match.')

        self.probabilities[(relation, tuple_)] = probability

    def get(self, relation: str, tuple_: Tuple[str, ...]) -> float:
        return self.probabilities.get((relation, tuple_), 0.0)

    def domain(self) -> Set[str]:
        domain_ = set()
        for _, tuple_ in self.probabilities:
            for item in tuple_:
                domain_.add(item)
        return domain_
