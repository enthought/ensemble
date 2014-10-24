from traits.api import Bool, Float, Instance, Property, Tuple

from .function_node import FunctionNode
from .linked import LinkedFunction
from .movable_component import MovableComponent
from .utils import clip, clip_to_unit

# A place for FunctionNode subclasses to be registered (for deserialization)
_function_component_class_registry = {}


def register_function_component_class(node_class, cls):
    global _function_component_class_registry
    _function_component_class_registry[node_class] = cls


MINIMUM_RADIUS = 0.01


class FunctionComponent(MovableComponent):
    """ A `Container` which corresponds to a node in the CTF editor.
    """

    # Can this component be removed?
    removable = Bool(True)

    # The function node for this component
    node = Instance(FunctionNode)

    # What are the screen bounds of the parent component
    parent_bounds = Property

    # The linked function where `self.node` lives
    _linked_function = Instance(LinkedFunction)

    # Movement limits for `self.node.center`
    _center_limits = Tuple(Float, Float)

    # -----------------------------------------------------------------------
    # FunctionComponent interface
    # -----------------------------------------------------------------------

    def add_function_nodes(self, linked_function):
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

    def node_limits(self, linked_function):
        """ Compute the movement bounds of the function node.
        """
        raise NotImplementedError

    def remove_function_nodes(self, linked_function):
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

    def set_node_center(self, node, rel_x):
        node.center = clip(rel_x, self._center_limits)

    def set_node_radius(self, node, rel_rad):
        min_center, max_center = self._center_limits
        center = node.center
        radius_limit = min(center - min_center, max_center - center)
        node.radius = max(min(rel_rad, radius_limit), MINIMUM_RADIUS)

    def update_function(self):
        # Let the world know that the function has changed.
        if self._linked_function is not None:
            self._linked_function.updated = True

    # -----------------------------------------------------------------------
    # Traits handlers
    # -----------------------------------------------------------------------

    def _get_parent_bounds(self):
        return self.container.bounds

    def _event_state_changed(self, new):
        if new == 'moving':
            self._center_limits = self.node_limits(self._linked_function)
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
