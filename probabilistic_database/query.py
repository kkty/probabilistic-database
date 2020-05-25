from typing import Dict, Tuple, Union


class Variable:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f'variable({self.name})'

    __repr__ = __str__


class Atom:
    def __init__(self, relation: str, tuple_: Tuple[Union[Variable, str], ...]):
        self.relation = relation
        self.tuple = tuple_

    def __str__(self):
        return f'{self.relation}({", ".join(map(str, self.tuple))})'

    __repr__ = __str__


class Negation:
    def __init__(self, inner):
        self.inner = inner

    def __str__(self):
        return f'not({self.inner})'

    __repr__ = __str__


class Conjunction:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self):
        return f'and({self.left}, {self.right})'

    __repr__ = __str__


class Disjunction:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self):
        return f'or({self.left}, {self.right})'

    __repr__ = __str__


class ExistentialQuantifier:
    def __init__(self, variable, inner):
        self.variable = variable
        self.inner = inner

    def __str__(self):
        return f'exist({self.variable}, {self.inner})'

    __repr__ = __str__


class UniversalQuantifier:
    def __init__(self, variable, inner):
        self.variable = variable
        self.inner = inner

    def __str__(self):
        return f'forall({self.variable}, {self.inner})'

    __repr__ = __str__


Query = Union[Atom, Negation, Conjunction, Disjunction,
              ExistentialQuantifier, UniversalQuantifier]


class ParseError(ValueError):
    pass


def parse_query(query: str, variables: Dict[str, Variable] = {}) -> Query:
    """Parses a query string. ParseError is raised when it fails."""

    operator_name = ''
    children = []

    level = 0
    buf = []
    for c in query:
        if c == '(':
            if level == 0:
                operator_name = ''.join(buf)
                buf.clear()
            else:
                buf.append(c)
            level += 1
        elif c == ')':
            level -= 1
            if level == 0:
                children.append(''.join(buf))
                buf.clear()
            elif level < 0:
                raise ParseError()
            else:
                buf.append(c)
        elif c == ' ':
            pass
        elif c == ',' and level == 1:
            children.append(''.join(buf))
            buf.clear()
        else:
            buf.append(c)
    if level != 0:
        raise ParseError()

    if operator_name is None:
        raise ParseError()

    if operator_name == 'not':
        if len(children) != 1:
            raise ParseError()
        return Negation(parse_query(children[0], variables))
    elif operator_name == 'and':
        if len(children) != 2:
            raise ParseError()
        return Conjunction(parse_query(children[0], variables), parse_query(children[1], variables))
    elif operator_name == 'or':
        if len(children) != 2:
            raise ParseError()
        return Disjunction(parse_query(children[0], variables), parse_query(children[1], variables))
    elif operator_name == 'exist':
        if len(children) != 2:
            raise ParseError()
        variable = Variable(children[0])
        variables = variables.copy()
        variables[children[0]] = variable
        return ExistentialQuantifier(variable, parse_query(children[1], variables))
    elif operator_name == 'forall':
        if len(children) != 2:
            raise ParseError()
        variable = Variable(children[0])
        variables = variables.copy()
        variables[children[0]] = variable
        return UniversalQuantifier(variable, parse_query(children[1], variables))
    else:
        return Atom(operator_name, tuple(variables.get(child, child) for child in children))
