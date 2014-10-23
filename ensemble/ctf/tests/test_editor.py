import unittest

from enable.testing import EnableTestAssistant
from traits_enaml.testing.enaml_test_assistant import EnamlTestAssistant

from ensemble.ctf.api import CtfEditor, ColorNode, OpacityNode


def get_color(starting_color=None):
    if starting_color:
        return starting_color
    return (0.0, 1.0, 0.0)


class TestEditor(EnamlTestAssistant, EnableTestAssistant, unittest.TestCase):

    def setUp(self):
        EnamlTestAssistant.setUp(self)

        enaml_source = """
from enaml.widgets.api import MainWindow
from traits_enaml.widgets.enable_canvas import EnableCanvas

enamldef MainView(MainWindow):
    attr editor

    initial_size = (400, 100)

    EnableCanvas:
        component << editor
"""

        editor = CtfEditor(bounds=(400, 100),
                           prompt_color_selection=get_color)

        function = editor.function.copy()
        function.color.insert(ColorNode(center=0.25, color=(1.0, 0.0, 0.0)))
        function.opacity.insert(OpacityNode(center=0.5, opacity=0.5))
        editor.function = function

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
        self.press_move_release(editor, [(200, 50), (220, 50), (240, 50),
                                         (260, 50), (280, 50), (300, 50)],
                                window=editor.window)
        editor.request_redraw()

    def test_mouse_drag_color(self):
        editor = self.editor
        self.press_move_release(editor, [(100, 50), (120, 50), (140, 50),
                                         (160, 50), (180, 50), (200, 50)],
                                window=editor.window)

if __name__ == '__main__':
    unittest.main()
