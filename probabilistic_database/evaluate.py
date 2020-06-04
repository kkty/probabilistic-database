from .util import DisjointSet, powerset
from .store import Store
from .query import Atom, Conjunction, Disjunction, ExistentialQuantifier, Query, Variable
from typing import List, Set, Tuple, Optional, Union
from operator import add, mul
from functools import partial, reduce
from itertools import product


def get_atoms(query: Query) -> List[Atom]:
    """Lists all the atoms in the query."""

    if isinstance(query, Atom):
        return [query]
    elif isinstance(query, (Conjunction, Disjunction)):
        return reduce(add, map(get_atoms, query.children))
    assert False


def get_variables(query: Query) -> Set[Variable]:
    """Lists all the variables in the query."""

    variables = set()
    for atom in get_atoms(query):
        for variable in (i for i in atom.tuple if isinstance(i, Variable)):
            variables.add(variable)
    return variables


def find_occurrences(query: Query, variable: Variable) -> Set[Tuple[str, int]]:
    """Lists all the occurrences of the variable in the query.

    An occurrence is represented as a tuple of the relation name and
    the position in the tuple. Duplicates are removed.
    """

    occurrences = set()
    for atom in get_atoms(query):
        for i, item in enumerate(atom.tuple):
            if item == variable:
                occurrences.add((atom.relation, i))
    return occurrences


def is_separator_variable(variable: Variable, query: Query) -> bool:
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
    elif isinstance(query, Conjunction):
        return Conjunction([rewrite_partial(child) for child in query.children])
    elif isinstance(query, Disjunction):
        return Disjunction([rewrite_partial(child) for child in query.children])
    elif isinstance(query, ExistentialQuantifier):
        return ExistentialQuantifier(query.variable, rewrite_partial(query.inner))
    assert False


def remove_quantifiers(query: Query) -> Union[Atom, Conjunction, Disjunction]:
    """Removes existential quantifiers from the query."""

    if isinstance(query, Atom):
        return query
    elif isinstance(query, Conjunction):
        return Conjunction([remove_quantifiers(child) for child in query.children])
    elif isinstance(query, Disjunction):
        return Disjunction([remove_quantifiers(child) for child in query.children])
    elif isinstance(query, ExistentialQuantifier):
        return remove_quantifiers(query.inner)
    assert False


def push_disjunction(query: Disjunction) -> Union[Conjunction, Disjunction]:
    """Push disjunctions inwards using the distributive law.

    If query.children does not contain conjunctions, the query is
    returned unchanged.
    """

    subqueries = []
    for q in query.children:
        if isinstance(q, Atom):
            subqueries.append([q])
        elif isinstance(q, Conjunction):
            subqueries.append(q.children)
        else:
            assert False
    product_ = list(product(*subqueries))
    if len(product_) == 1:
        return query
    return Conjunction([Disjunction(children) for children in product_])


def is_unifiable(atom1: Atom, atom2: Atom) -> bool:
    """Returns True if two atoms are unifiable.

    atom1 and atom2 are unifiable if there exists a set of variable-constant
    rewriting rule R such that R(atom1) == R(atom2).
    """

    if atom1.relation != atom2.relation:
        return False

    for item1, item2 in zip(atom1.tuple, atom2.tuple):
        if isinstance(item1, str) and isinstance(item2, str) and item1 != item2:
            return False

    return True


def is_independent(query1: Query, query2: Query) -> bool:
    """Returns True if query1 and query2 are independent.

    query1 and query2 are dependent when there is a pair of atom
    (a1, a2) such that 1) a1 appears in query1 2) a2 appears in query2
    and 3) a1 and a2 unify. Otherwise, the two queries are independent.
    """

    return all(not is_unifiable(atom1, atom2) for atom1, atom2 in product(get_atoms(query1), get_atoms(query2)))


def decompose(queries: List[Query]) -> List[List[Query]]:
    """Decomposes a list of queries to independent groups.

    If [q1, q2, q3, q4, q5] is given and (q1, q2), (q2, q3), (q4, q5)
    are dependent pairs, [[q1, q2, q3], [q4, q5]] is returned.
    """

    disjoint_set = DisjointSet(queries)
    for query1, query2 in product(queries, queries):
        if not is_independent(query1, query2):
            disjoint_set.unite(query1, query2)
    return disjoint_set.groups()


class EvaluationError(Exception):
    pass


def evaluate_query(query: Query, store: Store) -> float:
    """Evaluates the query using the store as back-end."""

    query = remove_quantifiers(query)

    if isinstance(query, Atom):
        tuple_: Tuple[str, ...] = ()
        for item in query.tuple:
            assert isinstance(item, str)
            tuple_ += (item,)
        return store.get(query.relation, tuple_)

    if isinstance(query, Disjunction):
        query = push_disjunction(query)

    if isinstance(query, Conjunction):
        decomposed = decompose(query.children)

        if len(decomposed) > 1:
            def wrap(queries):
                return Conjunction(queries) if len(queries) > 1 else queries[0]
            return reduce(mul, (evaluate_query(wrap(queries), store) for queries in decomposed))

        plus = []
        minus = []

        for subset in powerset(query.children):
            if len(subset) % 2 == 0:
                minus.append(Disjunction(subset))
            else:
                plus.append(Disjunction(subset))

        def cancel() -> bool:
            """Cancels out queries that exist both in plus and minus.

            If query q is found such that q exists both in plus and minus,
            one occurrence of q is removed each from plus and minus and
            True is returned. Otherwise, False is returned.
            """
            for p, m in product(plus, minus):
                if p == m:
                    plus.remove(p)
                    minus.remove(m)
                    return True
            return False

        while cancel():
            pass

        return sum(evaluate_query(query, store) for query in plus) - sum(evaluate_query(query, store) for query in minus)

    decomposed = decompose(query.children)

    if len(decomposed) > 1:
        def wrap(queries):
            return Disjunction(queries) if len(queries) > 1 else queries[0]
        return 1 - reduce(mul, ((1 - evaluate_query(wrap(queries), store)) for queries in decomposed))

    variables = get_variables(query)

    separator_variable: Optional[Variable] = None
    for variable in variables:
        if is_separator_variable(variable, query):
            separator_variable = variable
            break

    if not separator_variable:
        raise EvaluationError('The query is intractable.')

    domain: Set[str] = set()
    for relation, position in find_occurrences(query, separator_variable):
        for value in store.values(relation=relation, position=position):
            domain.add(value)

    rewrite_partial = partial(rewrite, (query, separator_variable))
    return 1 - reduce(mul, ((1 - evaluate_query(rewrite_partial(c), store) for c in domain)))
