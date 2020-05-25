from probabilistic_database.store import Store
from pytest import raises


def test_store():
    store = Store()
    store.add('r1', ('x', 'y'), 0.5)
    store.add('r2', ('u', 'v', 'w'), 0.8)
    assert store.get('r1', ('x', 'y')) == 0.5
    assert store.values() == set(['x', 'y', 'u', 'v', 'w'])


def test_store_arity_check():
    store = Store()
    store.add('r', ('x', 'y'), 0.5)
    with raises(ValueError):
        store.add('r', ('u', 'v', 'w'), 0.5)
