from unittest import TestCase

from grid_note import *


class TestMainWindow(TestCase):

    def test_multi_tab_model(self):
        app = QApplication(sys.argv)
        grid_note = MainWindow(False)

        src_data = [('1st page', [[None] * 10 for r in range(10)]),
                    ('2nd page', [[None] * 10 for r in range(10)])]

        grid_note.load_models(src_data)
        grid_note.cur_model.set_data_at(0, 0, 'aaa')

        print(grid_note.cur_page_name)
        self.assertTrue(grid_note.cur_page_name == '1st page')
        print(grid_note.cur_model.data_at(0, 0))
        self.assertTrue(grid_note.cur_model.data_at(0, 0).content == 'aaa')
