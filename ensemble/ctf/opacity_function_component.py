from traits.api import Float

from .function_component import (FunctionComponent,
                                 register_function_component_class)
from .function_node import FunctionNode, register_function_node_class
from .menu_tool import RemoveComponentAction, menu_tool_with_actions
from .utils import clip_to_unit


COMPONENT_SIZE = 8.0
BLACK = (0.0, 0.0, 0.0, 1.0)
GRAY = (0.6, 0.6, 0.6, 1.0)


class OpacityNode(FunctionNode):
    """ A `FunctionNode` representing a single opacity
    """

    # Infinitely thin!
    radius = 0.0

    # The opacity for this node
    opacity = Float

    def copy(self):
        obj = super(OpacityNode, self).copy()
        obj.opacity = self.opacity
        return obj

    @classmethod
    def from_dict(cls, dictionary):
        """ Create an instance from the data in `dictionary`.
        """
        return cls(center=dictionary['center'], radius=dictionary['radius'],
                   opacity=dictionary['opacity'])

    def to_dict(self):
        """ Create a dictionary which represents the state of the node.
        """
        dictionary = super(OpacityNode, self).to_dict()
        dictionary['opacity'] = self.opacity
        return dictionary

    def values(self):
        return [(self.center, self.opacity)]


class OpacityComponent(FunctionComponent):

    # Let the user know that we can be moved
    hover_pointer = 'hand'

    # -----------------------------------------------------------------------
    # FunctionComponent methods
    # -----------------------------------------------------------------------

    def add_function_nodes(self, linked_function):
        """ Add the node(s) for this component.
        """
        linked_function.opacity.insert(self.node)

    def draw_contents(self, gc):
        """ Draw the component.
        """
        x, y = self._get_screen_position()

        with gc:
            gc.set_stroke_color(BLACK)
            gc.set_fill_color(GRAY)
            gc.set_line_width(1.0)
            gc.rect(x - COMPONENT_SIZE/2.0, y - COMPONENT_SIZE/2.0,
                    COMPONENT_SIZE, COMPONENT_SIZE)
            gc.draw_path()

    @classmethod
    def from_function_nodes(cls, *nodes):
        """ Create an instance from `nodes`.
        """
        if len(nodes) > 1 or not isinstance(nodes[0], OpacityNode):
            raise ValueError('Expecting an OpacityNode instance!')

        return cls(node=nodes[0])

    def move(self, delta_x, delta_y):
        """ Move the component.
        """
        rel_x, rel_y = self.screen_to_relative(delta_x, delta_y)
        self.node.opacity = clip_to_unit(self.node.opacity + rel_y)
        self.set_node_center(self.node, self.node.center + rel_x)
        self._sync_component_position()

    def node_limits(self, linked_function):
        """ Compute the movement bounds of the function node.
        """
        limits = linked_function.opacity.node_limits(self.node)
        radius = self.node.radius
        return (limits[0] + radius, limits[1] - radius)

    def parent_changed(self, parent):
        """ Called when the parent of this component changes instances or
        bounds.
        """
        self._sync_component_position()

    def remove_function_nodes(self, linked_function):
        """ Remove the node(s) for this component.
        """
        linked_function.opacity.remove(self.node)

    # -----------------------------------------------------------------------
    # Traits initialization
    # -----------------------------------------------------------------------

    def _bounds_default(self):
        return (COMPONENT_SIZE, COMPONENT_SIZE)

    def _tools_default(self):
        actions = [RemoveComponentAction(component=self)]
        return [menu_tool_with_actions(self, actions)]

    # -----------------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------------

    def _get_screen_position(self):
        return self.relative_to_screen(self.node.center, self.node.opacity)

    def _sync_component_position(self):
        x, y = self._get_screen_position()
        self.position = (x - COMPONENT_SIZE/2.0, y - COMPONENT_SIZE/2.0)


# Register our function node
register_function_node_class(OpacityNode)
# ... and our function component
register_function_component_class(OpacityNode, OpacityComponent)
