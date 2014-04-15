import numpy as np

from enable.component import Component
from traits.api import Any, Callable, Event, Instance

from ensemble.ctf.editor_tools import (AlphaFunctionEditorTool,
                                       ColorFunctionEditorTool)
from ensemble.ctf.menu_tool import FunctionMenuTool
from ensemble.ctf.piecewise import PiecewiseFunction


ALPHA_DEFAULT = ((0.0, 0.0), (1.0, 1.0))
COLOR_DEFAULT = ((0.0, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0))


def create_function(values):
    fn = PiecewiseFunction(key=lambda x: x[0])
    for v in values:
        fn.insert(v)
    return fn


class CtfEditor(Component):
    """ A widget for editing transfer functions.
    """

    opacities = Instance(PiecewiseFunction)
    colors = Instance(PiecewiseFunction)

    function_updated = Event

    # A callable which prompts the user for a filename.
    # A single keyword argument 'action' will be passed to the callable and
    # its value will be 'open' or 'save'. A filename should be returned.
    prompt_file_selection = Callable

    # A callable which prompts the user for a color
    # A single keyword argument 'starting_color' will be passed to the callable
    # and its value will be None or an RGB tuple with values in the range
    # [0, 1]. An RGB tuple should be returned.
    prompt_color_selection = Callable

    # Numpy histogram tuple, if any.
    # (values, bin_edges)
    histogram = Any()

    # Add some padding to allow mouse interaction near the edge more pleasant.
    padding_left = 5
    padding_bottom = 5
    padding_top = 5
    padding_right = 5
    fill_padding = True

    #------------------------------------------------------------------------
    # Public interface
    #------------------------------------------------------------------------

    def add_function_node(self, function, value):
        function.insert(value)
        self.update_function()

    def edit_function_node(self, function, index, value):
        function.update(index, value)
        self.update_function()

    def remove_function_node(self, function, index):
        if index == 0 or index == (function.size()-1):
            return False

        function.remove(index)
        self.update_function()
        return True

    def update_function(self):
        self.function_updated = True
        self.request_redraw()

    #------------------------------------------------------------------------
    # Traits initialization
    #------------------------------------------------------------------------

    def _opacities_default(self):
        return create_function(ALPHA_DEFAULT)

    def _colors_default(self):
        return create_function(COLOR_DEFAULT)

    def _tools_default(self):
        alpha = AlphaFunctionEditorTool(self, function=self.opacities)
        color = ColorFunctionEditorTool(self, function=self.colors)
        menu = FunctionMenuTool(self)
        editor_tools = [alpha, color]
        for tool in editor_tools:
            tool.on_trait_change(self.update_function, 'function_updated')
        return editor_tools + [menu]

    #------------------------------------------------------------------------
    # Traits notifications
    #------------------------------------------------------------------------

    def _histogram_changed(self):
        self.request_redraw()

    #------------------------------------------------------------------------
    # Drawing
    #------------------------------------------------------------------------

    def draw(self, gc, **kwargs):
        color_nodes = self.colors.items()
        alpha_nodes = self.opacities.items()

        with gc:
            gc.clear()
            # Move the origin to the lower left padding.
            gc.translate_ctm(self.padding_left, self.padding_bottom)

            self._draw_colors(color_nodes, gc)
            if self.histogram is not None:
                self._draw_histogram(self.histogram, gc)
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

            gc.set_line_width(2.0)
            for x, y in points:
                gc.rect(x-2, y-2, 4, 4)
            gc.stroke_path()

    def _draw_colors(self, color_nodes, gc):
        """ Draw the colorbar and the color nodes.
        """
        w, h = self.width, self.height
        grad_stops = np.array([(x, r, g, b, 1.0)
                               for x, r, g, b in color_nodes])

        with gc:
            gc.rect(0, 0, w, h)
            gc.linear_gradient(0, 0, w, 0, grad_stops, 'pad',
                               'userSpaceOnUse')
            gc.fill_path()

            gc.set_line_width(2.0)
            for x, r, g, b in color_nodes:
                x = x * w
                # FIXME: Bad choice of contrasting color for grays.
                gc.set_stroke_color((1.0-r, 1.0-g, 1.0-b, 1.0))
                gc.rect(x-1, 0, 2, h)
                gc.stroke_path()

    def _draw_histogram(self, histogram, gc):
        """ Draw the logarithm of the histogram.
        """
        values, bin_edges = histogram
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
            gc.set_stroke_color((0.5, 0.5, 0.5, 1.0))
            gc.lines(points)
            gc.stroke_path()
