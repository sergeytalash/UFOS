import unittest
import UFOS_plotter
import tests.settings_for_tests as sft
import os
import datetime


def print_name(*args):
    print(str(args[0]).split()[1])


class TestProcedures(unittest.TestCase):
    def test_get_new_corrects_a_correct_data(self):
        # print('name')
        self.assertEqual(UFOS_plotter.get_new_corrects([279, 285, 275, 271, 268, 275, 282, 274, 282, 272],
                                                       [279, 285, 275, 271, 268, 275, 282, 274, 282, 272],
                                                       sft.settings()),
                         (['1', '1', '1', '1', '1', '1', '1', '1', '1', '1'], 5.22, 276))

    def test_get_new_corrects_b_uncorrect_data(self):
        self.assertEqual(UFOS_plotter.get_new_corrects([279, 285, 275, 271, 268, 700, 1500, 274, 2000, 272],
                                                       [279, 285, 275, 271, 268, 275, 282, 274, 282, 272],
                                                       sft.settings()),
                         (['1', '1', '1', '1', '1', '0', '0', '1', '0', '1'], 5.22, 276))

    def test_finalfile_prepare_a_datetime_string(self):
        init = UFOS_plotter.FinalFile(sft.settings(), '.', True, '')
        self.assertEqual(init.prepare('20181203 06:43:55', {'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1}),
                         ('20181203 06:43:55', 5.475, {'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1}))

    def test_finalfile_prepare_b_datetime_datetime(self):
        init = UFOS_plotter.FinalFile(sft.settings(), '.', True, '')
        self.assertEqual(init.prepare(datetime.datetime.strptime('20181203 06:43:55', '%Y%m%d %H:%M:%S'),
                                      {'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1}),
                         ('20181203 06:43:55', 5.475, {'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1}))

    def test_finalfile_save_a(self):
        init = UFOS_plotter.FinalFile(sft.settings(), '.', True, '')
        try:
            os.remove(r'tests\Ufos_14\Ozone\2018\2018-12\New_m14_Ozone_20181203.txt')
        except IOError:
            pass
        self.assertEqual(init.save(sft.settings(), 'tests', 'ZD',
                                   ['20181203 06:43:55',
                                    '20181203 06:48:37',
                                    '20181203 06:54:19',
                                    '20181203 06:59:00',
                                    '20181203 07:03:44'],
                                   [5.475, 5.857, 6.307, 6.665, 7.018],
                                   [{'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1},
                                    {'o3_1': 755, 'o3_2': 285, 'correct_1': 0, 'correct_2': 1},
                                    {'o3_1': 718, 'o3_2': 275, 'correct_1': 0, 'correct_2': 1},
                                    {'o3_1': 731, 'o3_2': 271, 'correct_1': 0, 'correct_2': 1},
                                    {'o3_1': 713, 'o3_2': 268, 'correct_1': 0, 'correct_2': 1}]),
                         r'tests\Ufos_14\Ozone\2018\2018-12\New_m14_Ozone_20181203.txt')

    def test_finalfile_save_b_file_is_correct(self):
        with open(r'tests\Ufos_14\Ozone\2018\2018-12\New_m14_Ozone_20181203.txt') as fr:
            d = fr.readlines()
            self.assertEqual(d[0],
                             'DatetimeUTC;DatetimeLocal;Sunheight[°];OzoneP1[D.u.];CorrectP1;OzoneP2[D.u.];CorrectP2\n')
            self.assertEqual(d[1], '20181203 06:43:55;20181203 09:43:55;5.5;713;0;279;1\n')
            self.assertEqual(d[2], '20181203 06:48:37;20181203 09:48:37;5.9;755;0;285;1\n')
            self.assertEqual(d[3], '20181203 06:54:19;20181203 09:54:19;6.3;718;0;275;1\n')
            self.assertEqual(d[4], '20181203 06:59:00;20181203 09:59:00;6.7;731;0;271;1\n')

    def test_annualozone_a(self):
        init = UFOS_plotter.AnnualOzone('tests', ent_year, data, root, but_annual_ozone)


class TestPlotter(unittest.TestCase):
    def test_1(self):
        # print('name')
        self.assertEqual(1, 1)

    if __name__ == '__main__':
        unittest.main()
