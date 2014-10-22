from abc import abstractmethod

from traits.api import ABCHasStrictTraits, Float

# A place for FunctionNode subclasses to be registered (for deserialization)
_function_node_class_registry = {}


def register_function_node_class(cls):
    global __function_node_class_registry
    _function_node_class_registry[cls.__name__] = cls


class FunctionNode(ABCHasStrictTraits):
    """ An object which represents some contiguous portion of a piecewise
    function.
    """

    # The position of the node in the function
    center = Float

    # Half the width of the node. Can be zero for single value nodes.
    radius = Float

    def copy(self):
        """ Return a copy of this node.
        """
        cls = self.__class__
        return cls(center=self.center, radius=self.radius)

    @classmethod
    def from_dict(cls, dictionary):
        """ Create an instance from the data in `dictionary`.
        """
        factory = _function_node_class_registry[dictionary['class']]
        return factory.from_dict(dictionary)

    def to_dict(self):
        """ Create a dictionary which represents the state of the node.
        """
        return {
            'class': self.__class__.__name__,
            'center': self.center,
            'radius': self.radius
        }

    @abstractmethod
    def values(self):
        """ Return a sequence of value tuples for this portion of the function.
        """
