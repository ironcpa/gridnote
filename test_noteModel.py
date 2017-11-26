from unittest import TestCase
from grid_note import *
import common_util as cu


class TestJobModel(TestCase):
    def test_set_bgcolor(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = NoteModel(src_data, None)

        model.set_style_at(0, 0, Qt.red)
        self.assertTrue(model.style_at(0, 0).bgcolor == Qt.red)

    def test_get_parent(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_data_at(0, 0, 'parent')
        model.set_data_at(1, 1, 'child1')
        model.set_data_at(2, 1, 'child2')

        p_index = model.parent_job_index(model.index(1, 1))
        print(cu.str_index(p_index))
        print('{}:{}'.format(p_index.row(), p_index.column()))
        self.assertTrue(p_index == model.index(0, 0))

        p_index = model.parent_job_index(model.index(2, 1))
        self.assertTrue(p_index == model.index(0, 0))

        model.set_data_at(3, 2, 'sub-child1')
        model.set_data_at(4, 2, 'sub-child2')

        p_index = model.parent_job_index(model.index(3, 2))
        self.assertTrue(p_index == model.index(2, 1))
        p_index = model.parent_job_index(model.index(4, 2))
        self.assertTrue(p_index == model.index(2, 1))

        model.set_data_at(5, 1, 'child3')
        p_index = model.parent_job_index(model.index(5, 1))
        self.assertTrue(p_index == model.index(0, 0))

        '''''''''''''''''''''''''''
        exception : checker column
        '''''''''''''''''''''''''''
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_checker(0, Checker.DONE)
        model.set_data_at(1, 5, 'parent')
        p_index = model.parent_job_index(model.index(1, 5))
        print('p index:', cu.str_index(p_index))
        self.assertTrue(p_index == None)

    def test_set_checker(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_data_at(0, 5, 'parent')

        model.set_checker(0, Checker.DONE)
        self.assertTrue(model.index(0, model.check_col).data() == 'o')

    def test_get_children_job_index(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_data_at(0, 5, 'parent')
        model.set_data_at(1, 6, 'child1')
        model.set_data_at(2, 6, 'child2')
        model.set_data_at(3, 7, 'sub-child1')
        model.set_data_at(4, 7, 'sub-child2')
        model.set_data_at(5, 7, 'sub-child3')
        model.set_data_at(6, 6, 'child3')
        # model.set_data_at(7, 6, 'child4')
        model.set_data_at(8, 6, 'child5')

        indexes = model.children_job_indexes(model.index(0, 5))
        print('len', len(indexes), cu.str_indexes(indexes))
        self.assertTrue(4 == len(indexes))
        self.assertTrue([model.index(1, 6), model.index(2, 6), model.index(6, 6), model.index(8, 6)] == indexes)

        indexes = model.children_job_indexes(model.index(2, 6))
        print('len', len(indexes), cu.str_indexes(indexes))
        self.assertTrue(3 == len(indexes))
        self.assertTrue([model.index(3, 7), model.index(4, 7), model.index(5, 7)] == indexes)

    def test_imaginary_root_get_children_indexes(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.clear()
        model.set_data_at(1, model.date_col, '2017-11-10')
        model.set_data_at(1, 5, 'parent1')
        model.set_checker(1, Checker.DONE)

        imaginary_root_index = model.index(0, 4)
        indexes = model.children_job_indexes(imaginary_root_index)
        print('len', len(indexes), cu.str_indexes(indexes))
        self.assertTrue(1 == len(indexes))
        self.assertTrue(cu.make_index(model, (1, 5)) == indexes)

    def test_first_data_index_from_checker(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_data_at(0, 5, 'parent')
        model.set_data_at(1, 6, 'child1')

        model.set_data_at(2, 6, 'child1')

        index = model.first_data_index_from_checker(1)
        self.assertTrue(model.index(1, 6) == index)

    def test_parent_checker_by_child_mod(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_data_at(0, 5, 'parent')
        model.set_data_at(1, 6, 'child1')
        model.set_data_at(2, 6, 'child2')
        model.set_data_at(3, 7, 'sub-child1')
        model.set_data_at(4, 7, 'sub-child2')

        model.set_checker(3, Checker.PROGRESS)
        c_checker = model.checker(3)
        p_index = model.parent_job_index(model.index(3, 7))
        p_data = p_index.data()
        p_checker = model.checker(p_index.row())
        print('child checker : ', c_checker)
        print('parent data :', p_data)
        print('parent checker : ', p_checker)
        self.assertTrue(c_checker == Checker.PROGRESS)
        self.assertTrue(p_data == 'child2')
        self.assertTrue(p_checker == Checker.PROGRESS)

    def test_find_last_row(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_data_at(0, 5, 'parent')
        model.set_data_at(1, 6, 'child1')
        model.set_data_at(2, 6, 'child2')
        model.set_data_at(3, 7, 'sub-child1')
        model.set_data_at(4, 7, 'sub-child2')

        print('last row', model.get_last_row())
        self.assertTrue(model.get_last_row() == 4)

    def test_latest_date_row(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_data_at(0, 0, '2017-11-19')
        model.set_data_at(5, 0, '2017-11-20')

        row = model.get_latest_date_row()
        self.assertTrue(row == 5)

    def test_find_prev_date_movetos(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.clear()
        model.set_data_at(1, model.date_col, '2017-11-10')

        model.set_data_at(1, 5, 'parent1')
        model.set_data_at(2, 6, 'child11')
        model.set_data_at(3, 6, 'child12')

        model.set_data_at(5, 5, 'parent2')
        model.set_data_at(6, 6, 'child21')
        model.set_data_at(7, 6, 'child22')

        '''don't use set_checker : it update parent checkers'''
        model.set_data_at(1, model.check_col, Checker.MOVETO.str)
        model.set_data_at(2, model.check_col, Checker.MOVETO.str)
        model.set_data_at(3, model.check_col, Checker.MOVETO.str)
        model.set_data_at(5, model.check_col, Checker.MOVETO.str)
        model.set_data_at(6, model.check_col, Checker.MOVETO.str)
        model.set_data_at(7, model.check_col, Checker.MOVETO.str)
        # model.set_checker(1, Checker.MOVETO)
        # model.set_checker(2, Checker.MOVETO)
        # model.set_checker(3, Checker.MOVETO)
        # model.set_checker(5, Checker.MOVETO)
        # model.set_checker(6, Checker.MOVETO)
        # model.set_checker(7, Checker.MOVETO)

        expect_rows = cu.make_index(model, (1, 5), (2, 6), (3, 6), (5, 5), (6, 6), (7, 6))
        # expect_rows = [1]
        found_rows = model.find_child_indexes_with_checker(model.index(1, 0), Checker.MOVETO)
        print('move to rows 2', cu.str_indexes(found_rows))
        self.assertTrue(expect_rows == found_rows)

        # '''check include none m> childrens'''
        # model.clear()
        # model.set_data_at(0, 5, 'parent')
        # model.set_data_at(1, 6, 'child1')
        # model.set_data_at(2, 6, 'child2')
        # model.set_data_at(3, 7, 'sub-child1')
        # model.set_data_at(4, 7, 'sub-child2')
        #
        # model.set_data_at(0, model.check_col, Checker.MOVETO.str)
        # coping_rows = [0, 1, 2, 3, 4]
        # found_rows = model.find_child_rows_with_checker(model.index(0, 0), Checker.MOVETO)
        # print('move to rows : ', found_rows)
        # self.assertTrue(coping_rows == found_rows)

    def test_copy_from_last_date_movetos(self):
        src_data = [[None] * 10 for r in range(100)]
        model = JobModel(src_data, None)

        model.clear()
        model.set_data_at(1, model.date_col, '2017-11-10')

        model.set_data_at(1, 5, 'm task 1d')
        model.set_data_at(2, 6, 'aaa')
        model.set_data_at(3, 6, 'm task 2d')
        model.set_data_at(4, 7, 'ccc')
        model.set_data_at(5, 7, 'ddd')
        model.set_data_at(6, 5, 'm task 1d 2')

        model.set_data_at(1, model.check_col, Checker.MOVETO.str)
        model.set_data_at(3, model.check_col, Checker.MOVETO.str)
        model.set_data_at(6, model.check_col, Checker.MOVETO.str)

        model.add_copy_from_last_date(Checker.MOVETO, None, Checker.PROGRESS, Checker.MISSED)
        self.assertTrue(model.content_at(7, 0).startswith('2017'))
        self.assertTrue(model.content_at(7, 5) == model.content_at(1, 5))
        self.assertTrue(model.content_at(8, 6) == model.content_at(2, 6))
        self.assertTrue(model.content_at(9, 6) == model.content_at(3, 6))
        self.assertTrue(model.content_at(10, 7) == model.content_at(4, 7))
        self.assertTrue(model.content_at(11, 7) == model.content_at(5, 7))
        self.assertTrue(model.content_at(12, 5) == model.content_at(6, 5))

        '''''''''''''''''''''''''''''''''''
        exception : if there's prev date's last job  
        '''''''''''''''''''''''''''''''''''
        model.clear()
        model.set_data_at(2, model.date_col, '2017-11-10')

        model.set_data_at(1, 5, 'prev date data')
        model.set_data_at(2, 5, 'm task 1d')
        model.set_data_at(3, 6, 'aaa')
        model.set_data_at(4, 6, 'm task 2d')
        model.set_data_at(5, 7, 'ccc')
        model.set_data_at(6, 7, 'ddd')
        model.set_data_at(7, 5, 'm task 1d 2')

        model.set_data_at(1, model.check_col, Checker.MOVETO.str)
        model.set_data_at(2, model.check_col, Checker.MOVETO.str)
        model.set_data_at(4, model.check_col, Checker.MOVETO.str)
        model.set_data_at(7, model.check_col, Checker.MOVETO.str)

        model.add_copy_from_last_date(Checker.MOVETO, None, Checker.PROGRESS, Checker.MISSED)
        self.assertTrue(model.content_at(8, 0).startswith('2017'))
        self.assertTrue(model.content_at(8, 5) == model.content_at(2, 5))
        self.assertTrue(model.content_at(9, 6) == model.content_at(3, 6))
        self.assertTrue(model.content_at(10, 6) == model.content_at(4, 6))
        self.assertTrue(model.content_at(11, 7) == model.content_at(5, 7))
        self.assertTrue(model.content_at(12, 7) == model.content_at(6, 7))
        self.assertTrue(model.content_at(13, 5) == model.content_at(7, 5))


