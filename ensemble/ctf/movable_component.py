from __future__ import unicode_literals
from enable.api import Container
from enable.toolkit_constants import pointer_names
from traits.api import Enum, Float


PointerEnum = Enum('arrow', values=set(pointer_names))


class MovableComponent(Container):
    """ A `Container` which can be manipulated by the user
    """

    # This component is not resizable
    resizable = ''

    # We only want two states
    event_state = Enum('normal', 'moving')

    # What should the mouse pointer be when the mouse is over this component?
    hover_pointer = PointerEnum

    # Where did a drag start relative to this component's origin
    _offset_x = Float
    _offset_y = Float

    # -----------------------------------------------------------------------
    # MovableComponent interface
    # -----------------------------------------------------------------------

    def move(self, delta_x, delta_y):
        """ Move the component.
        """
        raise NotImplementedError

    def parent_changed(self, parent):
        """ Called when the parent of this component changes instances or
        bounds.
        """
        raise NotImplementedError

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

    def normal_mouse_move(self, event):
        event.window.set_pointer(self.hover_pointer)
        event.handled = True

    def normal_mouse_leave(self, event):
        event.window.set_pointer('arrow')
        event.handled = True

    def moving_mouse_move(self, event):
        delta = (event.x - self._offset_x - self.x,
                 event.y - self._offset_y - self.y)
        self.move(*delta)
        event.handled = True

    def moving_left_up(self, event):
        self.event_state = 'normal'
        event.window.set_mouse_owner(None)
        event.handled = True
        self.request_redraw()

    def moving_mouse_leave(self, event):
        self.moving_left_up(event)
        event.handled = True

    # -----------------------------------------------------------------------
    # Traits handlers
    # -----------------------------------------------------------------------

    def _container_changed(self, old, new):
        super(MovableComponent, self)._container_changed(old, new)
        if new is not None:
            self.parent_changed(new)

    # -----------------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------------

    def _event_in_bounds(self, event):
        x, y, ex, ey = self.x, self.y, event.x, event.y
        w, h = self.bounds
        return (ex > x and ey > y and (ex - x) < w and (ey - y) < h)
