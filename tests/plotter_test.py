import functools
import unittest
import UFOS_plotter
import tests.settings_for_tests as sft
import os
import datetime
import numpy as np


def get_name(s):
    def decorator_repeat(func):
        @functools.wraps(func)
        def wrapper_repeat(*args, **kwargs):
            print(func.__dict__['_testMethodName'])
            return func(*args, **kwargs)
        return wrapper_repeat
    return decorator_repeat


class Test_get_new_corrects(unittest.TestCase):
    """===== Module procedures.py ====="""

    @get_name
    def test_get_new_corrects_correct_data(self):
        self.assertEqual(UFOS_plotter.get_new_corrects([279, 285, 275, 271, 268, 275, 282, 274, 282, 272],
                                                       [279, 285, 275, 271, 268, 275, 282, 274, 282, 272],
                                                       sft.settings()),
                         (['1', '1', '1', '1', '1', '1', '1', '1', '1', '1'], 5.22, 276))

    def test_get_new_corrects_uncorrect_data(self):
        self.assertEqual(UFOS_plotter.get_new_corrects([279, 285, 275, 271, 268, 700, 1500, 274, 2000, 272],
                                                       [279, 285, 275, 271, 268, 275, 282, 274, 282, 272],
                                                       sft.settings()),
                         (['1', '1', '1', '1', '1', '0', '0', '1', '0', '1'], 5.22, 276))

    def test_get_new_corrects_raise_ValueError(self):
        self.assertRaises(ValueError, UFOS_plotter.get_new_corrects, [279, 285, 275], [], '')

    def test_get_new_corrects_raise_TypeError(self):
        self.assertRaises(TypeError, UFOS_plotter.get_new_corrects, [279, 285, 275], [279, 285, 275], '')

    def test_get_new_corrects_raise_exception(self):
        self.assertRaises(KeyError, UFOS_plotter.get_new_corrects, [279, 285, 275], [279, 285, 275], {})

    def test_finalfile_prepare_datetime_string(self):
        init = UFOS_plotter.FinalFile(sft.settings(), '.', True, '')
        self.assertEqual(init.prepare('20181203 06:43:55', {'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1}),
                         ('20181203 06:43:55', 5.475, {'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1}))

    def test_finalfile_prepare_datetime_datetime(self):
        init = UFOS_plotter.FinalFile(sft.settings(), '.', True, '')
        self.assertEqual(init.prepare(datetime.datetime.strptime('20181203 06:43:55', '%Y%m%d %H:%M:%S'),
                                      {'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1}),
                         ('20181203 06:43:55', 5.475, {'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1}))


if __name__ == '__main__':
    unittest.main()
