import unittest

import numpy as np

from traits_enaml.testing.enaml_test_assistant import EnamlTestAssistant

from ensemble.volren.volume_data import VolumeData
from ensemble.volren.volume_renderer import VolumeRenderer


class VolumeRendererTestCase(EnamlTestAssistant, unittest.TestCase):

    def setUp(self):

        EnamlTestAssistant.setUp(self)

        enaml_source = """
from enaml.widgets.api import Container
from ensemble.volren.volume_render_view import VolumeRenderView

enamldef MainView(Container): view:
    attr renderer

    VolumeRenderView:
        renderer << view.renderer

"""
        volume = np.random.normal(size=(32, 32, 32))
        volume = (255*(volume-volume.min())/volume.ptp()).astype(np.uint8)
        volume_data = VolumeData(data=volume)
        self.renderer = VolumeRenderer(volume_data=volume_data)
        self.view, _ = self.parse_and_create(enaml_source,
                                             renderer=self.renderer)

    def tearDown(self):
        self.view = None
        self.renderer = None
        EnamlTestAssistant.tearDown(self)

    def test_renderer_initialized(self):
        self.assertTrue(self.renderer.volume is not None)


if __name__ == "__main__":
    unittest.main()
