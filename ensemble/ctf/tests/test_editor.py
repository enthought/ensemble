import unittest

# Do a dance to force ETS to use Qt and make sure that enaml imports Qt first.
from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'
import enaml.qt  # NOQA

from enable.testing import EnableTestAssistant
from enable.window import Window
from traits_enaml.testing.gui_test_assistant import GuiTestAssistant

from ensemble.ctf.editor import CtfEditor


def get_color(starting_color=None):
    if starting_color:
        return starting_color
    return (0.0, 1.0, 0.0)


def get_filename(action='save'):
    return 'temp.json'


class TestCtfEditor(EnableTestAssistant, GuiTestAssistant, unittest.TestCase):

    def setUp(self):
        super(TestCtfEditor, self).setUp()

        tool = CtfEditor(bounds=(400, 100),
                         prompt_color_selection=get_color,
                         prompt_file_selection=get_filename)
        tool.add_function_node(tool.opacities, (0.5, 0.5))
        tool.add_function_node(tool.colors, (0.25, 1.0, 0.0, 0.0))
        self.tool = tool
        self.window = Window(None, size=(100, 100), component=tool)
        with self.event_loop():
            self.window.control.show()

    def test_mouse_drag_alpha(self):
        tool = self.tool
        self.press_move_release(tool, [(50, 50), (51, 50), (52, 50),
                                       (53, 50), (54, 50), (55, 50)],
                                window=self.window)

    def test_mouse_drag_color(self):
        tool = self.tool
        self.press_move_release(tool, [(25, 10), (25, 10), (40, 10)],
                                window=self.window)

if __name__ == '__main__':
    unittest.main()
