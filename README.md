# Probabilistic Database

This is an implementation of one type of [probabilistic databases](https://en.wikipedia.org/wiki/Probabilistic_database).

In this implementation, non-repeating conjunctive queries, a limited class of first order logic formulae, are used as queries.
A non-repeating conjunctive query looks like this: `∃x1 ∃x2 ... ∃xn R1(t1) ∧ R2(t2) ∧ ... ∧ Rm(tm)`, where each `ti` is a tuple which might contain variables (`x1 ... xn`) or constants.

The probability calculation for some non-repeating CQs are tractable (can be done in polynomial time) but that of others are not.
Formally, the probability calculation for a non-repeating CQ is tractable if and only if the query is "hierarchical".

This implementation can compute the probability of any hierarchical non-repeating CQs in polynomial time.

Please refer to [this book](https://www.morganclaypool.com/doi/abs/10.2200/S00362ED1V01Y201105DTM016) for the description of the algorithm, the formal definitions of "non-repeating CQs" and "hierarchical", and the theories of probabilistic databases in general. It covers a wide range of topics regarding probabilistic databases.

## Example

### Adding data

Let's create a database and populate it with some data. We create a `Store` instance and add tuples to them with probabilities.

```python
from probabilistic_database.store import Store

store = Store()
store.add('R', ('a', 'b'), 0.8)
store.add('R', ('b', 'c'), 0.7)
store.add('R', ('a', 'c'), 0.6)
store.add('S', ('a',), 0.5)
store.add('S', ('b',), 0.4)
```

It can be interpreted like this.

- `R(a, b)` is true with the probability of 0.8.
- `R(b, c)` is true with the probability of 0.7.
- `R(a, c)` is true with the probability of 0.6.
- `S(a)` is true with the probability of 0.5.
- `S(b)` is true with the probability of 0.4.

### Querying

Next, let's run some queries against the data we just added.

```python
from probabilistic_database.evaluate import evaluate_query
from probabilistic_database.query import parse_query

for query in (
        'R(a, b)',
        'x | R(x, c)',
        'x, y | R(x, y)',
        'x | R(x, c), S(x)',
        'x, y | R(x, y), S(x)'):
    parsed_query = parse_query(query)
    probability = evaluate_query(parsed_query, store)
    print(probability)
```

As you can see, an original query language for conjunctive queries is used here. To be more formal, we are considering these 5 queries.

1. `R(a, b)`
2. `∃x R(x, c)`
3. `∃x ∃y R(x, y)`
4. `∃x R(x, c) ∧ S(x)`
5. `∃x ∃y R(x, y) ∧ S(y)`

The output will be like this.

```
0.8
0.88
0.976
0.496
0.6112
```

It means that the 1st query is true with the probability of 0.8, the 2nd query is true with the probability of 0.88, and so on.

By passing `debug=True` to `evaluate_query`, you can also take a look at how a query is decomposed while evaluation. The following is the debugging output for the 5th query.

```
evaluating: ∃x ∃y R(variable(x), variable(y)) ∧ S(variable(x))
  evaluating: ∃y R(c, variable(y)) ∧ S(c)
    evaluating: ∃y R(c, variable(y))
      evaluating: R(c, c)
      evaluating: R(c, a)
      evaluating: R(c, b)
    evaluating: S(c)
  evaluating: ∃y R(a, variable(y)) ∧ S(a)
    evaluating: ∃y R(a, variable(y))
      evaluating: R(a, c)
      evaluating: R(a, a)
      evaluating: R(a, b)
    evaluating: S(a)
  evaluating: ∃y R(b, variable(y)) ∧ S(b)
    evaluating: ∃y R(b, variable(y))
      evaluating: R(b, c)
      evaluating: R(b, a)
      evaluating: R(b, b)
    evaluating: S(b)
```
