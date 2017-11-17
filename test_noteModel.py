from unittest import TestCase
from grid_note import *


class TestJobModel(TestCase):
    def test_set_bgcolor(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = NoteModel(src_data, None)

        model.set_style_at(0, 0, Qt.red)
        self.assertTrue(model.style_at(0, 0).bgcolor == Qt.red)

    def test_get_parent(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_data_at(model.index(0, 0), 'parent')
        model.set_data_at(model.index(1, 1), 'child1')
        model.set_data_at(model.index(2, 1), 'child2')

        p_index = model.parent_job_index(model.index(1, 1))
        print(str(p_index))
        print('{}:{}'.format(p_index.row(), p_index.column()))
        self.assertTrue(p_index == model.index(0, 0))

        p_index = model.parent_job_index(model.index(2, 1))
        self.assertTrue(p_index == model.index(0, 0))

        model.set_data_at(model.index(3, 2), 'sub-child1')
        model.set_data_at(model.index(4, 2), 'sub-child2')

        p_index = model.parent_job_index(model.index(3, 2))
        self.assertTrue(p_index == model.index(2, 1))
        p_index = model.parent_job_index(model.index(4, 2))
        self.assertTrue(p_index == model.index(2, 1))

        model.set_data_at(model.index(5, 1), 'child3')
        p_index = model.parent_job_index(model.index(5, 1))
        self.assertTrue(p_index == model.index(0, 0))

    def test_set_checker(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_data_at(model.index(0, 5), 'parent')

        model.set_checker(0, 'o')
        self.assertTrue(model.index(0, model.check_col).data() == 'o')

    def test_get_children_job_index(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_data_at(model.index(0, 5), 'parent')
        model.set_data_at(model.index(1, 6), 'child1')
        model.set_data_at(model.index(2, 6), 'child2')
        model.set_data_at(model.index(3, 7), 'sub-child1')
        model.set_data_at(model.index(4, 7), 'sub-child2')
        model.set_data_at(model.index(5, 7), 'sub-child3')
        model.set_data_at(model.index(6, 6), 'child3')
        # model.set_data_at(model.index(7, 6), 'child4')
        model.set_data_at(model.index(8, 6), 'child5')

        indexes = model.children_job_indexes(model.index(0, 5))
        print('len', len(indexes))
        print(indexes)
        self.assertTrue(4 == len(indexes))
        self.assertTrue([model.index(1, 6), model.index(2, 6), model.index(6, 6), model.index(8, 6)] == indexes)

        indexes = model.children_job_indexes(model.index(2, 6))
        print('len', len(indexes))
        print(indexes)
        self.assertTrue(3 == len(indexes))
        self.assertTrue([model.index(3, 7), model.index(4, 7), model.index(5, 7)] == indexes)

    def test_first_data_index_from_checker(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_data_at(model.index(0, 5), 'parent')
        model.set_data_at(model.index(1, 6), 'child1')
        model.set_data_at(model.index(2, 6), 'child1')

        index = model.first_data_index_from_checker(1)
        self.assertTrue(model.index(1, 6) == index)

    def test_parent_checker_by_child_mod(self):
        src_data = [[None for c in range(10)] for r in range(10)]
        model = JobModel(src_data, None)

        model.set_data_at(model.index(0, 5), 'parent')
        model.set_data_at(model.index(1, 6), 'child1')
        model.set_data_at(model.index(2, 6), 'child2')
        model.set_data_at(model.index(3, 7), 'sub-child1')
        model.set_data_at(model.index(4, 7), 'sub-child2')

        model.set_checker(3, '>')
        c_cherker = model.checker(3)
        p_index = model.parent_job_index(model.index(3, 7))
        p_data = p_index.data()
        p_checker = model.rel_checker(p_index)
        print('child checker : ', c_cherker)
        print('parent data :', p_data)
        print('parent checker : ', p_checker)
        self.assertTrue(c_cherker == '>')
        self.assertTrue(p_data == 'child2')
        self.assertTrue(p_checker == '>')