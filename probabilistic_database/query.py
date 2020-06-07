from typing import Dict, List, Tuple, Union


class Variable:
    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: 'Variable') -> bool:
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return f'variable({self.name})'


class Atom:
    def __init__(self, relation: str, tuple_: Tuple[Union[Variable, str], ...]):
        self.relation = relation
        self.tuple = tuple_

    def __eq__(self, other):
        return self.relation == other.relation and self.tuple == other.tuple

    def __hash__(self):
        return hash((self.relation, self.tuple))

    def __str__(self):
        return f'{self.relation}({", ".join(map(str, self.tuple))})'


class Query:
    def __init__(self, atoms: List[Atom]) -> None:
        self.atoms = atoms

        variables: List[Variable] = []
        for atom in atoms:
            for item in atom.tuple:
                if isinstance(item, Variable):
                    variables.append(item)
        # Remove duplicates.
        variables = list(dict.fromkeys(variables))
        self.variables = variables

    def __str__(self) -> str:
        buf = []
        for variable in self.variables:
            buf.append(f'∃{variable.name}')
        buf.append(' ∧ '.join(map(str, self.atoms)))
        return ' '.join(buf)


class ParseError(ValueError):
    pass


def parse_query(query: str, variables: Dict[str, Variable] = {}) -> Query:
    """Parses a query string. ParseError is raised when it fails."""

    def parse_variables(s: str) -> Dict[str, Variable]:
        variables = {}
        for name in s.split(','):
            if name == '':
                raise ParseError()
            if name in variables:
                raise ParseError('Two variables cannot have the same name.')
            variables[name] = Variable(name)
        return variables

    def parse_atoms(s: str, variables: Dict[str, Variable]) -> List[Atom]:
        def parse_atom(s: str) -> Atom:
            if s.count('(') != 1 or s.count(')') != 1:
                raise ParseError()

            open_ = s.index('(')
            close = s.index(')')
            if open_ == 0 or close != len(s) - 1:
                raise ParseError()

            relation = s[:open_]
            tuple_ = []
            for item in s[open_+1:close].split(','):
                if item == '':
                    raise ParseError()
                tuple_.append(variables.get(item, item))

            return Atom(relation, tuple(tuple_))

        level = 0
        buf = []
        atoms = []
        for c in s:
            if c == ',' and level == 0:
                atoms.append(parse_atom(''.join(buf)))
                buf.clear()
            else:
                buf.append(c)
                if c == '(':
                    level += 1
                elif c == ')':
                    level -= 1
        atoms.append(parse_atom(''.join(buf)))

        return atoms

    query = query.replace(' ', '')

    if '|' in query:
        if query.count('|') >= 2:
            raise ParseError('"|" cannot appear more than once.')
        vertical = query.index('|')
        variables = parse_variables(query[:vertical])
        atoms = parse_atoms(query[vertical+1:], variables)
    else:
        atoms = parse_atoms(query, {})
        variables = {}

    return Query(atoms)
