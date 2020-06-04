from collections import defaultdict
from typing import Dict, Generic, Iterable, List, TypeVar

T = TypeVar('T')


class DisjointSet(Generic[T]):
    def __init__(self, values: Iterable[T]):
        self.parent: Dict[T, T] = {value: value for value in values}

    def find_root(self, x: T) -> T:
        if self.parent[x] == x:
            return x
        return self.find_root(self.parent[x])

    def unite(self, x: T, y: T):
        """Updates the set so that x and y belong to the same group."""

        x = self.find_root(x)
        y = self.find_root(y)
        if x != y:
            self.parent[y] = x

    def same(self, x: T, y: T) -> bool:
        """Returns True if x and y belong to the same group."""

        return self.find_root(x) == self.find_root(y)

    def groups(self) -> List[List[T]]:
        """Returns a list of groups."""

        d = defaultdict(list)
        for value in self.parent:
            d[self.find_root(value)].append(value)
        return list(d.values())


def powerset(s: List[T]) -> List[List[T]]:
    """Lists all subsets of s."""

    N = len(s)
    powerset_ = []
    for i in range(2 ** N):
        subset = []
        for j in range(N):
            if (1 << j) & i > 0:
                subset.append(s[j])
        powerset_.append(subset)
    return powerset_
