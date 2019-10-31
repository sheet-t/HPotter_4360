import unittest
from unittest.mock import MagicMock, call
from hpotter.plugins.handler import *

class TestPluginHandler(unittest.TestCase):
    @unittest.skip('Skipping until we can get a chance to fix this')
    def test_rm_container(self):
        rm_container()
        assert(Singletons.current_container == None)
        Singletons.current_container = MagicMock()
        Singletons.current_thread = unittest.mock.Mock()
        rm_container()
        assert(Singletons.current_container == None)
    @unittest.skip('Skipping until we can get a chance to fix this')
    def test_start_server(self):
        Singletons.current_thread == None
        start_server('httpipe', 0)
        assert(Singletons.current_thread != None)
    @unittest.skip('Skipping until we can get a chance to fix this')
    def test_stop_server(self):
        Singletons.current_container = MagicMock()
        assert(Singletons.current_container is not None)
        stop_server(MagicMock())
        assert(Singletons.current_container == None)
