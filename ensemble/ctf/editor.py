import numpy as np

from enable.api import ColorTrait, Container
from pyface.action.api import Action
from traits.api import Callable, Either, Instance, Tuple, on_trait_change

from .color_function_component import ColorNode, ColorComponent
from .function_component import FunctionComponent
from .linked import LinkedFunction
from .menu_tool import menu_tool_with_actions
from .opacity_function_component import OpacityNode, OpacityComponent
from .utils import build_screen_to_function


class BaseCtfAction(Action):
    container = Instance(Container)
    screen_to_function = Callable

    def _screen_to_function_default(self):
        return build_screen_to_function(self.container)


class AddColorAction(BaseCtfAction):
    name = 'Add Color...'

    # A callable which prompts the user for a color
    prompt_color = Callable

    def perform(self, event):
        new_color = self.prompt_color()
        if new_color is None:
            return

        screen_position = (event.enable_event.x, 0.0)
        rel_x, _ = self.screen_to_function(screen_position)
        node = ColorNode(center=rel_x, color=new_color)
        component = ColorComponent(node=node,
                                   _linked_function=self.container.function)

        self.container.add_function_component(component)


class AddOpacityAction(BaseCtfAction):
    name = 'Add Opacity'

    def perform(self, event):
        screen_position = (event.enable_event.x, event.enable_event.y)
        rel_x, rel_y = self.screen_to_function(screen_position)
        node = OpacityNode(center=rel_x, opacity=rel_y)
        component = OpacityComponent(node=node,
                                     _linked_function=self.container.function)

        self.container.add_function_component(component)


class CtfEditor(Container):
    """ A widget for editing transfer functions.
    """

    # The function
    function = Instance(LinkedFunction)

    # A callable which prompts the user for a color
    # A single keyword argument 'starting_color' will be passed to the callable
    # and its value will be None or an RGB tuple with values in the range
    # [0, 1]. An RGB tuple should be returned.
    prompt_color_selection = Callable

    # Numpy histogram tuple, if any. (values, bin_edges)
    histogram = Either(Tuple, None)

    # The color to use when drawing the histogram
    histogram_color = ColorTrait('gray')

    # Add some padding to allow mouse interaction near the edge more pleasant.
    padding_left = 5
    padding_bottom = 5
    padding_top = 5
    padding_right = 5
    fill_padding = True

    # Give child components the first crack at events
    intercept_events = False

    # -----------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------

    def add_function_component(self, component):
        self.add(component)
        component.add_function_nodes(self.function)
        self.function.updated = True
        self.request_redraw()

    def remove_function_component(self, component):
        self.remove(component)
        component.remove_function_nodes(self.function)
        self.function.updated = True
        self.request_redraw()

    # -----------------------------------------------------------------------
    # Traits initialization
    # -----------------------------------------------------------------------

    def _function_default(self):
        function = LinkedFunction()
        self._add_function_components(function)

        return function

    def _tools_default(self):
        prompt_color = self.prompt_color_selection
        actions = [
            AddColorAction(container=self, prompt_color=prompt_color),
            AddOpacityAction(container=self),
        ]
        return [menu_tool_with_actions(self, actions)]

    # -----------------------------------------------------------------------
    # Traits notifications
    # -----------------------------------------------------------------------

    def _bounds_changed(self, old, new):
        super(CtfEditor, self)._bounds_changed(old, new)
        for child in self.components:
            if isinstance(child, FunctionComponent):
                child.parent_changed(self)

    def _function_changed(self, new):
        for child in self.components[:]:
            if isinstance(child, FunctionComponent):
                self.remove(child)

        if new is not None:
            self._add_function_components(new)

        self.request_redraw()

    @on_trait_change('function:updated')
    def _function_updated(self):
        self.request_redraw()

    def _histogram_changed(self):
        self.request_redraw()

    # -----------------------------------------------------------------------
    # Drawing
    # -----------------------------------------------------------------------

    def _draw_container_mainlayer(self, gc, *args, **kwargs):
        color_nodes = self.function.color.values()
        alpha_nodes = self.function.opacity.values()

        gc.clear()

        with gc:
            # Move the origin to the lower left padding.
            gc.translate_ctm(self.padding_left, self.padding_bottom)

            self._draw_colors(color_nodes, gc)
            if self.histogram is not None:
                self._draw_histogram(gc)
            self._draw_alpha(alpha_nodes, gc)

    def _draw_alpha(self, alpha_nodes, gc):
        """ Draw the opacity curve.
        """
        w, h = self.width, self.height
        points = [(w * i, h * v) for (i, v) in alpha_nodes]

        with gc:
            gc.set_line_width(1.0)
            gc.set_stroke_color((0.0, 0.0, 0.0, 1.0))
            gc.lines(points)
            gc.stroke_path()

    def _draw_colors(self, color_nodes, gc):
        """ Draw the colorbar.
        """
        w, h = self.width, self.height
        grad_stops = np.array([(x, r, g, b, 1.0)
                               for x, r, g, b in color_nodes])

        with gc:
            gc.rect(0, 0, w, h)
            gc.linear_gradient(0, 0, w, 0, grad_stops, 'pad', 'userSpaceOnUse')
            gc.fill_path()

    def _draw_histogram(self, gc):
        """ Draw the logarithm of the histogram.
        """
        values, bin_edges = self.histogram
        w, h = self.width, self.height
        values = values.astype(float)
        zeros = (values == 0)
        min_nonzero = values[~zeros].min()
        values[zeros] = min_nonzero / 2.0
        log_values = np.log(values)
        log_values -= log_values.min()
        log_values /= log_values.max()

        h_values = log_values * h
        bin_edges = bin_edges - bin_edges.min()
        bin_edges *= w / bin_edges.max()
        x = np.concatenate([bin_edges[:1],
                            np.repeat(bin_edges[1:-1], 2),
                            bin_edges[-1:]])
        y = np.repeat(h_values, 2)
        points = np.column_stack([x, y])

        with gc:
            gc.set_line_width(1.0)
            gc.set_stroke_color(self.histogram_color_)
            gc.lines(points)
            gc.stroke_path()

    # -----------------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------------

    def _add_function_components(self, function):
        for func in (function.color, function.opacity):
            last_index = func.size() - 1
            for idx, node in enumerate(func.nodes):
                component = FunctionComponent.from_function_nodes(node)
                component._linked_function = function
                component.removable = (idx not in (0, last_index))
                self.add(component)
