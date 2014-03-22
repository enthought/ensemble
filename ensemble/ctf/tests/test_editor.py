import unittest

# Do a dance to force ETS to use Qt and make sure that enaml imports Qt first.
from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'
import enaml.qt  # NOQA

from enable.testing import EnableTestAssistant
from traits_enaml.testing.enaml_test_assistant import EnamlTestAssistant

from ensemble.ctf.editor import CtfEditor


def get_color(starting_color=None):
    if starting_color:
        return starting_color
    return (0.0, 1.0, 0.0)


def get_filename(action='save'):
    return 'temp.json'


class TestEditor(EnamlTestAssistant, EnableTestAssistant, unittest.TestCase):

    def setUp(self):
        EnamlTestAssistant.setUp(self)

        enaml_source = """
from enaml.widgets.api import MainWindow
from traits_enaml.widgets.enable_canvas import EnableCanvas

enamldef MainView(MainWindow):
    attr editor

    EnableCanvas:
        component << editor
"""

        editor = CtfEditor(bounds=(400, 100),
                           prompt_color_selection=get_color,
                           prompt_file_selection=get_filename)
        editor.add_function_node(editor.opacities, (0.5, 0.5))
        editor.add_function_node(editor.colors, (0.25, 1.0, 0.0, 0.0))
        self.editor = editor
        self.view, _ = self.parse_and_create(enaml_source, editor=self.editor)

        with self.event_loop():
            self.view.show()

    def tearDown(self):
        self.editor = None
        self.view = None

        EnamlTestAssistant.tearDown(self)

    def test_mouse_drag_alpha(self):
        editor = self.editor
        self.press_move_release(editor, [(50, 50), (51, 50), (52, 50),
                                         (53, 50), (54, 50), (55, 50)],
                                window=editor.window)

    def test_mouse_drag_color(self):
        editor = self.editor
        self.press_move_release(editor, [(25, 10), (25, 10), (40, 10)],
                                window=editor.window)

if __name__ == '__main__':
    unittest.main()
