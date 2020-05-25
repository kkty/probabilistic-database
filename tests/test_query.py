from probabilistic_database.query import parse_query


def test_parse_query():
    for query, expected in (
        ('or(r1(x, y, z), r2(u, v, w))', 'or(r1(x, y, z), r2(u, v, w))'),
        ('forall(x, r(x, y))', 'forall(variable(x), r(variable(x), y))'),
        ('exist(y, and(r1(x, y), r2(y, z)))',
         'exist(variable(y), and(r1(x, variable(y)), r2(variable(y), z)))'),
    ):
        assert str(parse_query(query)) == expected
