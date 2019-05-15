from __future__ import unicode_literals
from traits.api import Bool, Float, Instance, Property, Tuple

from .function_node import FunctionNode
from .movable_component import MovableComponent
from .transfer_function import TransferFunction
from .utils import clip, clip_to_unit

# A place for FunctionNode subclasses to be registered (for deserialization)
_function_component_class_registry = {}


def register_function_component_class(node_class, cls):
    global _function_component_class_registry
    _function_component_class_registry[node_class] = cls


class FunctionComponent(MovableComponent):
    """ A `Container` which corresponds to a node in the CTF editor.
    """

    # Can this component be removed?
    removable = Bool(True)

    # The function node for this component
    node = Instance(FunctionNode)

    # What are the screen bounds of the parent component
    parent_bounds = Property

    # The transfer function where `self.node` lives
    _transfer_function = Instance(TransferFunction)

    # Movement limits for `self.node.center`
    _center_limits = Tuple(Float, Float)

    # -----------------------------------------------------------------------
    # FunctionComponent interface
    # -----------------------------------------------------------------------

    def add_function_nodes(self, transfer_function):
        """ Add the node(s) for this component.
        """
        raise NotImplementedError

    def draw_contents(self, gc):
        """ Draw the component.
        """
        raise NotImplementedError

    @classmethod
    def from_function_nodes(cls, *nodes):
        """ Create an instance from `nodes`.
        """
        node = nodes[0]
        factory = _function_component_class_registry[node.__class__]
        return factory.from_function_nodes(*nodes)

    def node_limits(self, transfer_function):
        """ Compute the movement bounds of the function node.
        """
        raise NotImplementedError

    def remove_function_nodes(self, transfer_function):
        """ Remove the node(s) for this component.
        """
        raise NotImplementedError

    # -----------------------------------------------------------------------
    # FunctionComponent protected interface
    # -----------------------------------------------------------------------

    def relative_to_screen(self, x, y):
        parent_width, parent_height = self.parent_bounds
        return (clip_to_unit(x) * float(parent_width),
                clip_to_unit(y) * float(parent_height))

    def screen_to_relative(self, x, y):
        parent_width, parent_height = self.parent_bounds
        return (x / float(parent_width), y / float(parent_height))

    def update_node_center(self, node, rel_x):
        min_c, max_c = self._center_limits
        rad = node.radius
        node.center = clip(node.center + rel_x, (min_c + rad, max_c - rad))

    def update_function(self):
        # Let the world know that the function has changed.
        if self._transfer_function is not None:
            self._transfer_function.updated = True

    # -----------------------------------------------------------------------
    # Traits handlers
    # -----------------------------------------------------------------------

    def _get_parent_bounds(self):
        return self.container.bounds

    def _event_state_changed(self, new):
        if new == 'moving':
            self._center_limits = self.node_limits(self._transfer_function)
        elif new == 'normal':
            self._center_limits = (0.0, 1.0)

    # -----------------------------------------------------------------------
    # Enable Component methods
    # -----------------------------------------------------------------------

    def moving_mouse_move(self, event):
        super(FunctionComponent, self).moving_mouse_move(event)
        self.update_function()

    def _draw_overlay(self, gc, view_bounds=None, mode='default'):
        self.draw_contents(gc)
