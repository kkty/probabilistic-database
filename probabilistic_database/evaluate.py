from .store import Store
from .query import Atom, Conjunction, Disjunction, ExistentialQuantifier, Negation, Query, UniversalQuantifier, Variable
from typing import List, Set, Tuple, cast
from operator import mul
from functools import partial, reduce


def get_atoms(query: Query) -> List[Atom]:
    """Lists all the atoms in the query."""

    if isinstance(query, Atom):
        return [query]
    elif isinstance(query, (Negation, ExistentialQuantifier, UniversalQuantifier)):
        return get_atoms(query.inner)
    elif isinstance(query, (Conjunction, Disjunction)):
        return get_atoms(query.left) + get_atoms(query.right)
    assert False


def get_relations(query: Query) -> Set[str]:
    """Lists all the relations that appear in the query."""

    relations = set()
    for atom in get_atoms(query):
        relations.add(atom.relation)
    return relations


def is_independent(query1: Query, query2: Query):
    """Returns True if query1 and query2 do not share any relations."""

    return len(get_relations(query1) & get_relations(query2)) == 0


def is_separator_variable(variable: Variable, query: Query):
    """Returns True if the variable is a separator variable of the query.

    Variable v is a separator variable of query Q when 1) every atom in Q
    has one occurrence of v 2) for any relation r, there exists i such that
    v is at the ith position in every atom with r.
    """

    relation_to_position = {}
    for atom in get_atoms(query):
        if atom.tuple.count(variable) != 1:
            return False
        position = atom.tuple.index(variable)
        if atom.relation not in relation_to_position:
            relation_to_position[atom.relation] = position
        elif relation_to_position[atom.relation] != position:
            return False
    return True


def rewrite(query: Query, variable: Variable, constant: str) -> Query:
    """Rewrites a query by replacing the variable with the constant.

    A new query is returned instead of modifying in-place.
    """

    rewrite_partial = partial(rewrite, variable=variable, constant=constant)
    if isinstance(query, Atom):
        def replace_if_match(v):
            return constant if v == variable else v
        return Atom(query.relation, tuple(map(replace_if_match, query.tuple)))
    elif isinstance(query, Negation):
        return Negation(rewrite_partial(query.inner))
    elif isinstance(query, Conjunction):
        return Conjunction(rewrite_partial(query.left), rewrite_partial(query.right))
    elif isinstance(query, Disjunction):
        return Disjunction(rewrite_partial(query.left), rewrite_partial(query.right))
    elif isinstance(query, ExistentialQuantifier):
        return ExistentialQuantifier(query.variable, rewrite_partial(query.inner))
    elif isinstance(query, UniversalQuantifier):
        return UniversalQuantifier(query.variable, rewrite_partial(query.inner))
    assert False


def evaluate_query(query: Query, store: Store) -> float:
    """Evaluates the query using the store as a backend."""

    if isinstance(query, Atom):
        assert all(isinstance(item, str) for item in query.tuple)
        return store.get(query.relation, cast(Tuple[str], query.tuple))
    elif isinstance(query, Negation):
        return 1.0 - evaluate_query(query.inner, store)
    elif isinstance(query, Conjunction) and is_independent(query.left, query.right):
        return evaluate_query(query.left, store) * evaluate_query(query.right, store)
    elif isinstance(query, Disjunction) and is_independent(query.left, query.right):
        return 1.0 - (1.0 - evaluate_query(query.left, store)) * (1.0 - evaluate_query(query.right, store))
    elif isinstance(query, UniversalQuantifier) and is_separator_variable(query.variable, query.inner):
        return reduce(mul, (evaluate_query(rewrite(query.inner, query.variable, constant), store) for constant in store.values()))
    elif isinstance(query, ExistentialQuantifier) and is_separator_variable(query.variable, query.inner):
        return 1.0 - reduce(mul, ((1.0 - evaluate_query(rewrite(query.inner, query.variable, constant), store)) for constant in store.values()))
    else:
        raise NotImplementedError('The query is too hard.')
