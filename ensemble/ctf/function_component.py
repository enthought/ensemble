from enable.api import Component
from traits.api import Bool, Enum, Float, Instance, Property, Tuple

from .function_node import FunctionNode
from .linked import LinkedFunction
from .utils import clip, clip_to_unit

# A place for FunctionNode subclasses to be registered (for deserialization)
_function_component_class_registry = {}


def register_function_component_class(node_class, cls):
    global _function_component_class_registry
    _function_component_class_registry[node_class] = cls


class FunctionComponent(Component):
    """ A `Component` which corresponds to a node in the CTF editor.
    """

    # Can this component be removed?
    removable = Bool(True)

    # The function node for this component
    node = Instance(FunctionNode)

    # We only want two states
    event_state = Enum('normal', 'moving')

    # What are the screen bounds of the parent component
    parent_bounds = Property

    # This component is not resizable
    resizable = ''

    # The linked function where `self.node` lives
    _linked_function = Instance(LinkedFunction)

    # Movement limits for `self.node.center`
    _center_limits = Tuple(Float, Float)

    # Where did a drag start relative to this component's origin
    _offset_x = Float
    _offset_y = Float

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

    def move(self, delta_x, delta_y):
        """ Move the component.
        """
        raise NotImplementedError

    def node_limits(self, linked_function):
        """ Compute the movement bounds of the function node.
        """
        raise NotImplementedError

    def parent_changed(self, parent):
        """ Called when the CTF editor changes.
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

    def set_node_center(self, rel_x):
        self.node.center = clip(rel_x, self._center_limits)

    # -----------------------------------------------------------------------
    # Traits handlers
    # -----------------------------------------------------------------------

    def _container_changed(self, old, new):
        super(FunctionComponent, self)._container_changed(old, new)
        if new is not None:
            self.parent_changed(new)

    def _get_parent_bounds(self):
        return self.container.bounds

    def _event_state_changed(self, new):
        if new == 'moving':
            radius = self.node.radius
            min_center, max_center = self.node_limits(self._linked_function)
            self._center_limits = (min_center + radius, max_center - radius)
        elif new == 'normal':
            self._center_limits = (0.0, 1.0)

    # -----------------------------------------------------------------------
    # Enable event handlers
    # -----------------------------------------------------------------------

    def normal_left_down(self, event):
        if self._event_in_bounds(event):
            self._offset_x = event.x - self.x
            self._offset_y = event.y - self.y
            self.event_state = 'moving'
            event.window.set_mouse_owner(self, event.net_transform())
            event.handled = True

    def moving_mouse_move(self, event):
        delta = (event.x - self._offset_x - self.x,
                 event.y - self._offset_y - self.y)
        self.move(*delta)
        event.handled = True
        self._linked_function.updated = True

    def moving_left_up(self, event):
        self.event_state = 'normal'
        event.window.set_mouse_owner(None)
        event.handled = True
        self.request_redraw()

    def moving_mouse_leave(self, event):
        self.moving_left_up(event)
        event.handled = True

    # -----------------------------------------------------------------------
    # Enable draw handlers
    # -----------------------------------------------------------------------

    def _draw_overlay(self, gc, view_bounds=None, mode='default'):
        self.draw_contents(gc)

    # -----------------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------------

    def _event_in_bounds(self, event):
        x, y, ex, ey = self.x, self.y, event.x, event.y
        w, h = self.bounds
        return (ex > x and ey > y and (ex - x) < w and (ey - y) < h)
