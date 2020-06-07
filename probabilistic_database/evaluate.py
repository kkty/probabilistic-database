from typing import Dict, Set, cast

import itertools
import functools
import operator
import sys

from typing import Tuple
from probabilistic_database.query import Atom, Query, Variable
from probabilistic_database.store import Store


def contain(query: Query, variable: Variable) -> Set[Atom]:
    """Returns all the atoms in the query which contain the variable."""

    atoms = set()
    for atom in query.atoms:
        for item in atom.tuple:
            if isinstance(item, Variable) and item == variable:
                atoms.add(item)
    return atoms


def rewrite_atom(atom: Atom, variable: Variable, constant: str) -> Atom:
    """Rewrites the variable with the constant in the atom.

    A new Atom instance is returned and the original instance is not modified.
    """

    tuple_ = []
    for item in atom.tuple:
        if isinstance(item, Variable) and item == variable:
            tuple_.append(constant)
        else:
            tuple_.append(item)
    return Atom(atom.relation, tuple(tuple_))


def rewrite_query(query: Query, variable: Variable, constant: str) -> Query:
    """Rewrites the variable with the constant in the query.

    A new Query instance is returned and the original instance is not modified.
    """

    atoms = [rewrite_atom(atom, variable, constant) for atom in query.atoms]
    return Query(atoms)


class EvaluationError(Exception):
    pass


def evaluate_query(query: Query, store: Store, depth=0) -> float:
    """Evaluates the query using the store as a backend."""

    evaluate_query_ = functools.partial(
        evaluate_query, store=store, depth=depth+1)

    print('  ' * depth + f'evaluating: {query}', file=sys.stderr)

    if len(query.atoms) == 1:
        atom = query.atoms[0]
        if all(isinstance(item, str) for item in atom.tuple):
            return store.get(atom.relation, cast(Tuple[str, ...], atom.tuple))

    # For each variable in the query, list up the atoms where that variable
    # appears.
    variables: Dict[Variable, Set[Atom]] = {}
    for variable in query.variables:
        variables[variable] = contain(query, variable)

    # Check if the query is hierarchical.
    for s1, s2 in itertools.product(variables.values(), variables.values()):
        if not s1.issubset(s2) and s2.issubset(s1) and s1 & s2:
            raise EvaluationError('The query is not hierarchical.')

    # Select the variable that appears most in the query.
    variable, _ = max(variables.items(), key=lambda item: len(item[1]))

    # The atoms which contain "variable".
    atoms1 = []
    # The atoms which do not contain "variable".
    atoms2 = []

    for atom in query.atoms:
        if any(isinstance(item, Variable) and item == variable for item in atom.tuple):
            atoms1.append(atom)
        else:
            atoms2.append(atom)

    if len(atoms1) == len(query.atoms):
        # "variable" is a separator variable.

        def evaluate_sub():
            for constant in store.domain():
                yield evaluate_query_(rewrite_query(query, variable, constant))

        return 1 - functools.reduce(operator.mul, ((1 - p) for p in evaluate_sub()))
    else:
        # Query(atoms1) and Query(atoms2) are independent.

        return evaluate_query_(Query(atoms1)) * evaluate_query_(Query(atoms2))
