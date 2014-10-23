from bisect import bisect
from operator import add, sub

from traits.api import HasStrictTraits, Instance, List, Property

from .function_node import FunctionNode


class PiecewiseFunction(HasStrictTraits):
    """ A piecewise linear function.
    """

    nodes = Property(List(Instance(FunctionNode)), depends_on='_nodes')
    _nodes = List(Instance(FunctionNode))

    def clear(self):
        self._nodes = []

    def copy(self):
        cls = type(self)
        return cls(_nodes=[n.copy() for n in self._nodes])

    @classmethod
    def from_dict(cls, dictionary):
        node_dicts = dictionary.get('nodes', [])
        return cls(_nodes=[FunctionNode.from_dict(nd) for nd in node_dicts])

    def index_of(self, node):
        return self._nodes.index(node)

    def insert(self, new_node):
        centers = [node.center for node in self._nodes]
        index = bisect(centers, new_node.center)
        self._nodes.insert(index, new_node)

    def node_at(self, index):
        return self._nodes[index]

    def node_limits(self, node):
        if node not in self._nodes:
            return []

        index = self._nodes.index(node)
        max_index = self.size() - 1

        if index == 0:
            # The first item can't move
            return (0.0, 0.0)
        elif index == max_index:
            # Neither can the last item
            return (1.0, 1.0)

        neighbors = self._nodes[index - 1], self._nodes[index + 1]
        return tuple([op(n.center, n.radius)
                      for n, op in zip(neighbors, (add, sub))])

    def remove(self, node):
        if node not in self._nodes:
            raise ValueError("Node not in piecewise function.")

        index = self._nodes.index(node)
        del self._nodes[index]

    def size(self):
        return len(self._nodes)

    def to_dict(self):
        return {'nodes': [node.to_dict() for node in self._nodes]}

    def values(self):
        return [v for n in self._nodes for v in n.values()]

    def _get_nodes(self):
        return self._nodes
