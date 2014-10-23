from traits.api import HasStrictTraits, Event, Instance, List

from .piecewise import PiecewiseFunction


COLOR_DEFAULT = {
    'nodes': [
        {'class': 'ColorNode',
         'radius': 0.0, 'center': 0.0, 'color': [0.0, 0.0, 0.0]},
        {'class': 'ColorNode',
         'radius': 0.0, 'center': 1.0, 'color': [1.0, 1.0, 1.0]},
    ]
}
OPACITY_DEFAULT = {
    'nodes': [
        {'class': 'OpacityNode', 'radius': 0.0, 'center': 0.0, 'opacity': 0.0},
        {'class': 'OpacityNode', 'radius': 0.0, 'center': 1.0, 'opacity': 1.0},
    ]
}


def _get_link(color_node, opacity_node):
    return (color_node, opacity_node)


class LinkedFunction(HasStrictTraits):
    """ A function containing two `PiecewiseFunction` instances which contain
    nodes that are (sometimes) linked.
    """

    # The colors
    color = Instance(PiecewiseFunction)

    # The opacities
    opacity = Instance(PiecewiseFunction)

    # The nodes in `color` and `opacity` which exist as a pair.
    links = List([])

    # An event that should fire when the function is updated
    updated = Event

    # -----------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------

    def add_linked_nodes(self, color_node, opacity_node):
        self.color.insert(color_node)
        self.opacity.insert(opacity_node)

        self.links.append(_get_link(color_node, opacity_node))

    def remove_linked_nodes(self, color_node, opacity_node):
        self.color.remove(color_node)
        self.opacity.remove(opacity_node)

        link = _get_link(color_node, opacity_node)
        self.links.remove(link)

    def copy(self):
        link_indices = self._links_as_indices()
        color = self.color.copy()
        opacity = self.opacity.copy()
        links = self._links_from_indices(color, opacity, link_indices)

        cls = type(self)
        return cls(color=color, opacity=opacity, links=links)

    @classmethod
    def from_dict(cls, dictionary):
        """ Load a function from a dict.
        """
        piecewise_from_dict = PiecewiseFunction.from_dict
        color = piecewise_from_dict(dictionary.get('color', {}))
        opacity = piecewise_from_dict(dictionary.get('opacity', {}))

        link_indices = dictionary.get('links', [])
        links = cls._links_from_indices(color, opacity, link_indices)

        return cls(color=color, opacity=opacity, links=links)

    def to_dict(self):
        """ Flatten the function into a dictionary.
        """
        return {
            'color': self.color.to_dict(),
            'opacity': self.opacity.to_dict(),
            'links': self._links_as_indices(),
        }

    # -----------------------------------------------------------------------
    # Traits initialization
    # -----------------------------------------------------------------------

    def _color_default(self):
        return PiecewiseFunction.from_dict(COLOR_DEFAULT)

    def _opacity_default(self):
        return PiecewiseFunction.from_dict(OPACITY_DEFAULT)

    # -----------------------------------------------------------------------
    # Private interface
    # -----------------------------------------------------------------------

    def _links_as_indices(self):
        """ Return the list of a links as a list of indices.
        """
        return [(self.color.index_of(c), self.opacity.index_of(o))
                for c, o in self.links]

    @staticmethod
    def _links_from_indices(color, opacity, indices):
        return [(color.node_at(c_idx), opacity.node_at(o_idx))
                for c_idx, o_idx in indices]
