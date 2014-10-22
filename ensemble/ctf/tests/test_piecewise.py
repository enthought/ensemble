from ensemble.ctf.api import PiecewiseFunction, OpacityNode

NODES = [OpacityNode(center=0.0, opacity=0.0),
         OpacityNode(center=0.5, opacity=0.5),
         OpacityNode(center=0.9, opacity=1.0)]


def _basic_piecewise():
    pf = PiecewiseFunction()
    for n in NODES:
        pf.insert(n)

    return pf


def _compare_piecewise(func0, func1):
    assert func0 is not func1
    assert func0.nodes != func1.nodes
    assert func0.size() == func1.size()
    assert all([n0.center == n1.center and n0.opacity == n1.opacity
                for n0, n1 in zip(func0.nodes, func1.nodes)])


def test_piecewise_insert():
    pf = _basic_piecewise()

    assert pf.size() == len(NODES)
    assert pf.nodes == NODES
    assert pf.node_at(1) == NODES[1]


def test_piecewise_remove():
    pf = _basic_piecewise()

    pf.remove(NODES[0])
    assert pf.size() == 2


def test_piecewise_copy():
    pf = _basic_piecewise()
    _compare_piecewise(pf, pf.copy())


def test_dictionary_roundtrip():
    pf = _basic_piecewise()
    d = pf.to_dict()

    _compare_piecewise(pf, PiecewiseFunction.from_dict(d))


def test_node_limits():
    pf = _basic_piecewise()
    limits = pf.node_limits(NODES[1])

    assert limits[0] == NODES[0].center and limits[1] == NODES[-1].center


def test_node_ordering():
    pf = _basic_piecewise()
    reverse_pf = PiecewiseFunction()
    for n in reversed(NODES):
        reverse_pf.insert(n.copy())

    _compare_piecewise(pf, reverse_pf)
