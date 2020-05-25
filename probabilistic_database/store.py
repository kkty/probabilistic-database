from typing import Optional, Tuple, Set


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

    def values(self, relation: Optional[str] = None, position: Optional[int] = None) -> Set[str]:
        """Returns a set of all the values."""

        s = set()
        for relation_, tuple_ in self.probabilities:
            if relation is not None and relation_ != relation:
                continue
            for position_, item in enumerate(tuple_):
                if position is not None and position_ != position:
                    continue
                s.add(item)
        return s
