from probabilistic_database.query import parse_query


def test_parse_query():
    for query, expected in (
        ('x, y | R(x, y), S(z)', '∃x ∃y R(variable(x), variable(y)) ∧ S(z)'),
        ('R(x, y)', 'R(x, y)'),
    ):
        assert str(parse_query(query)) == expected
