import unittest

import numpy as np

from traits_enaml.testing.enaml_test_assistant import EnamlTestAssistant

from ensemble.volren.volume_data import VolumeData
from ensemble.volren.volume_viewer import VolumeViewer


class VolumeViewerTestCase(EnamlTestAssistant, unittest.TestCase):

    def setUp(self):

        EnamlTestAssistant.setUp(self)

        enaml_source = """
from enaml.widgets.api import Container
from ensemble.volren.volume_viewer_ui import VolumeViewerContainer

enamldef MainView(Container): view:
    attr viewer

    VolumeViewerContainer:
        viewer << view.viewer

"""
        volume = np.random.normal(size=(32, 32, 32))
        volume = (255*(volume-volume.min())/volume.ptp()).astype(np.uint8)
        volume_data = VolumeData(raw_data=volume)
        self.viewer = VolumeViewer(volume_data=volume_data)
        self.view, _ = self.parse_and_create(enaml_source,
                                             viewer=self.viewer)

        with self.event_loop():
            self.view.show()

    def tearDown(self):
        self.view = None
        self.viewer = None
        EnamlTestAssistant.tearDown(self)

    def test_renderer_initialized(self):
        self.assertTrue(self.viewer.volume_renderer.volume is not None)

    def test_renderer_screenshot(self):
        image_array = self.viewer.screenshot()
        self.assertTrue(image_array.ndim == 3)
        self.assertTrue(image_array.shape[-1] == 3)

if __name__ == "__main__":
    unittest.main()
