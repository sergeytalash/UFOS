import unittest
import os
import datetime
import json
import sys
sys.path.append('../')
import UFOS_plotter
if os.name == 'posix':
    p_sep = '/'
else:
    p_sep = '\\'


from procedures import *


def settings():
    with open(r"Ufos_14\Settings\settings.json") as f:
        settings_dict = json.load(f)
    return settings_dict


def print_name(*args):
    print(str(args[0]).split()[1])


def get_tests_dir():
    path = os.path.basename(os.getcwd())
    if path == 'UFOS':
        tests_dir = 'tests' + p_sep
    elif path == 'tests':
        tests_dir = ''
    return tests_dir


class TestProcedures(unittest.TestCase):
    def test_get_new_corrects_a_correct_data(self):
        # print('name')
        self.assertEqual(Correction.get_second_corrects([279, 285, 275, 271, 268, 275, 282, 274, 282, 272],
                                                        [279, 285, 275, 271, 268, 275, 282, 274, 282, 272],
                                                        settings()),
                         (['1', '1', '1', '1', '1', '1', '1', '1', '1', '1'], 5.22, 276))

    def test_get_new_corrects_b_uncorrect_data(self):
        self.assertEqual(Correction.get_second_corrects([279, 285, 275, 271, 268, 700, 1500, 274, 2000, 272],
                                                        [279, 285, 275, 271, 268, 275, 282, 274, 282, 272],
                                                        settings()),
                         (['1', '1', '1', '1', '1', '0', '0', '1', '0', '1'], 5.22, 276))

    def test_finalfile_prepare_a_datetime_string(self):
        init = UFOS_plotter.FinalFile(settings(), '.', True, '')
        self.assertEqual(init.prepare('20181203 06:43:55', {'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1}),
                         ('20181203 06:43:55', 5.475, {'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1}))

    def test_finalfile_prepare_b_datetime_datetime(self):
        init = UFOS_plotter.FinalFile(settings(), '.', True, '')
        self.assertEqual(init.prepare(datetime.datetime.strptime('20181203 06:43:55', '%Y%m%d %H:%M:%S'),
                                      {'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1}),
                         ('20181203 06:43:55', 5.475, {'o3_1': 713, 'o3_2': 279, 'correct_1': 0, 'correct_2': 1}))

    def test_finalfile_save_a(self):
        init = UFOS_plotter.FinalFile(settings(), '.', True, '')
        ozone_file = os.path.join('{}Ufos_14'.format(get_tests_dir()), 'Ozone', '2018', '2018-12', 'New_m14_Ozone_20181203.txt')
        if os.path.exists(ozone_file):
            os.remove(ozone_file)
        self.assertEqual(init.save(settings(), get_tests_dir(), 'ZD',
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
                         ozone_file)
        self.assertEqual(calculate_final_files(settings(),
                                               ozone_file,
                                               'ZD',
                                               True,
                                               'file'), {'1': {'all': {'k': ['0', '0', '0', '0', '0'],
                                                                       'mean': 0,
                                                                       'o3': [713, 755, 718, 731, 713],
                                                                       'o3_count': 5,
                                                                       'sigma': 0,
                                                                       'text': 'Среднее значение ОСО (P1): 0\n'
                                                                               'Стандартное отклонение: 0\n'},
                                                               'evening': {'k': [], 'o3': [], 'o3_count': 0,
                                                                           'text': '\n'},
                                                               'morning': {'k': ['0', '0', '0', '0', '0'],
                                                                           'mean': 0,
                                                                           'o3': [713, 755, 718, 731, 713],
                                                                           'o3_count': 5,
                                                                           'sigma': 0,
                                                                           'text': 'Среднее значение ОСО (P1): 0\n'
                                                                                   'Стандартное отклонение: 0\n'}},
                                                         '2': {'all': {'k': ['0', '0', '0', '0', '0'],
                                                                       'mean': 0,
                                                                       'o3': [279, 285, 275, 271, 268],
                                                                       'o3_count': 5,
                                                                       'sigma': 0,
                                                                       'text': 'Среднее значение ОСО (P2): 0\n'
                                                                               'Стандартное отклонение: 0\n'},
                                                               'evening': {'k': [], 'o3': [], 'o3_count': 0,
                                                                           'text': '\n'},
                                                               'morning': {'k': ['0', '0', '0', '0', '0'],
                                                                           'mean': 0,
                                                                           'o3': [279, 285, 275, 271, 268],
                                                                           'o3_count': 5,
                                                                           'sigma': 0,
                                                                           'text': 'Среднее значение ОСО (P2): 0\n'
                                                                                   'Стандартное отклонение: 0\n'}}}
                         )
        data = ['20181203 06:43:55;20181203 09:43:55;5.475;713;0;279;1',
                '20181203 06:48:37;20181203 09:48:37;5.857;755;0;285;1',
                '20181203 06:54:19;20181203 09:54:19;6.307;718;0;275;1',
                '20181203 06:59:00;20181203 09:59:00;6.665;731;0;271;1',
                '20181203 07:03:44;20181203 10:03:44;7.018;713;0;268;1',
                '20181203 07:08:27;20181203 10:08:27;7.358;709;0;275;1',
                '20181203 07:13:07;20181203 10:13:07;7.685;741;0;282;1',
                '20181203 07:17:49;20181203 10:17:49;8.004;745;0;274;1',
                '20181203 07:22:36;20181203 10:22:36;8.317;715;0;282;1',
                '20181203 07:32:25;20181203 10:32:25;8.925;727;0;272;1',
                '20181203 07:37:05;20181203 10:37:05;9.197;714;0;272;1',
                '20181203 07:41:46;20181203 10:41:46;9.459;726;0;274;1',
                '20181203 07:46:26;20181203 10:46:26;9.708;729;0;275;1',
                '20181203 07:51:05;20181203 10:51:05;9.946;728;0;274;1',
                '20181203 07:55:44;20181203 10:55:44;10.172;723;0;269;1',
                '20181203 08:00:23;20181203 11:00:23;10.386;739;0;277;1',
                '20181203 08:05:03;20181203 11:05:03;10.59;739;0;271;1',
                '20181203 08:09:44;20181203 11:09:44;10.782;729;0;275;1',
                '20181203 08:19:05;20181203 11:19:05;11.13;737;0;271;1',
                '20181203 08:23:45;20181203 11:23:45;11.286;735;0;270;1',
                '20181203 08:28:24;20181203 11:28:24;11.429;734;0;268;1',
                '20181203 08:33:03;20181203 11:33:03;11.56;733;0;271;1',
                '20181203 08:37:43;20181203 11:37:43;11.679;729;0;273;1',
                '20181203 08:42:22;20181203 11:42:22;11.785;732;0;271;1',
                '20181203 08:51:20;20181203 11:51:20;11.955;740;0;272;1',
                '20181203 08:56:00;20181203 11:56:00;12.025;743;0;273;1',
                '20181203 09:00:39;20181203 12:00:39;12.082;732;0;266;1',
                '20181203 09:05:19;20181203 12:05:19;12.127;733;0;267;1',
                '20181203 09:10:00;20181203 12:10:00;12.16;725;0;277;1',
                '20181203 09:14:39;20181203 12:14:39;12.179;735;0;271;1',
                '20181203 09:19:18;20181203 12:19:18;12.186;747;0;272;1',
                '20181203 09:23:57;20181203 12:23:57;12.181;735;0;268;1',
                '20181203 09:28:36;20181203 12:28:36;12.163;724;0;272;1',
                '20181203 09:33:14;20181203 12:33:14;12.132;734;0;271;1',
                '20181203 09:37:54;20181203 12:37:54;12.089;735;0;271;1',
                '20181203 09:42:32;20181203 12:42:32;12.033;732;0;274;1',
                '20181203 09:47:11;20181203 12:47:11;11.965;743;0;273;1',
                '20181203 09:51:52;20181203 12:51:52;11.884;740;0;273;1',
                '20181203 10:01:52;20181203 13:01:52;11.668;725;0;272;1',
                '20181203 10:11:54;20181203 13:11:54;11.394;735;0;272;1',
                '20181203 10:16:33;20181203 13:16:33;11.248;744;0;269;1',
                '20181203 10:21:12;20181203 13:21:12;11.09;732;0;271;1',
                '20181203 10:25:52;20181203 13:25:52;10.92;732;0;278;1',
                '20181203 10:30:33;20181203 13:30:33;10.736;734;0;273;1',
                '20181203 10:35:14;20181203 13:35:14;10.541;721;0;276;1',
                '20181203 10:45:14;20181203 13:45:14;10.084;732;0;275;1',
                '20181203 10:49:53;20181203 13:49:53;9.854;727;0;277;1',
                '20181203 10:54:33;20181203 13:54:33;9.611;717;0;276;1',
                '20181203 10:59:15;20181203 13:59:15;9.355;717;0;280;1',
                '20181203 11:03:55;20181203 14:03:55;9.09;720;0;276;1',
                '20181203 11:08:34;20181203 14:08:34;8.814;724;0;274;1',
                '20181203 11:13:14;20181203 14:13:14;8.527;716;0;271;1',
                '20181203 11:23:14;20181203 14:23:14;7.875;722;0;274;1',
                '20181203 11:27:55;20181203 14:27:55;7.554;726;0;277;1',
                '20181203 11:32:35;20181203 14:32:35;7.222;707;0;273;1',
                '20181203 11:37:15;20181203 14:37:15;6.881;716;0;270;1',
                '20181203 11:41:55;20181203 14:41:55;6.53;716;0;270;1',
                '20181203 11:46:38;20181203 14:46:38;6.165;713;0;259;1',
                '20181203 11:51:20;20181203 14:51:20;5.791;721;0;270;1',
                '20181203 11:56:02;20181203 14:56:02;5.408;728;0;273;1',
                '20181203 12:00:43;20181203 15:00:43;5.016;759;0;285;1']
        out = calculate_final_files(settings(),
                                    data,
                                    'ZD',
                                    False,
                                    'calculate')

        self.assertEqual(list(out.keys()), ["1", "2"])
        # self.assertEqual(out.items(), ["1", "2"])

    def test_finalfile_save_b_file_is_correct(self):
        with open(os.path.join('{}Ufos_14'.format(get_tests_dir()), 'Ozone', '2018', '2018-12', 'New_m14_Ozone_20181203.txt')) as fr:
            d = fr.readlines()
            self.assertEqual(d[0],
                             'DatetimeUTC;DatetimeLocal;Sunheight[°];OzoneP1[D.u.];CorrectP1;OzoneP2[D.u.];CorrectP2\n')
            self.assertEqual(d[1], '20181203 06:43:55;20181203 09:43:55;5.5;713;0;279;1\n')
            self.assertEqual(d[2], '20181203 06:48:37;20181203 09:48:37;5.9;755;0;285;1\n')
            self.assertEqual(d[3], '20181203 06:54:19;20181203 09:54:19;6.3;718;0;275;1\n')
            self.assertEqual(d[4], '20181203 06:59:00;20181203 09:59:00;6.7;731;0;271;1\n')

    def test_get_polynomial_result_calc(self):
        self.assertEqual(round(get_polynomial_result([1.3834, -0.1423, 0.0147], 1.5), 3), 1.203)
        self.assertEqual(round(get_polynomial_result([5.122, 1.3834, -0.1423, 0.0147], 1.5), 3), 6.927)
        self.assertEqual(round(get_polynomial_result([50.5, -5.122, 1.3834, -0.1423, 0.0147], 1.5), 3), 45.524)

    def test_sumarize_calc(self):
        self.assertEqual(sumarize([1, 2, 3, '', 4]), 10)
        self.assertEqual(sumarize([1, 2, 3, 4]), 10)

    def test_read_nomographs(self):
        mueff_list, r12_list, ozone_list = read_nomographs(get_tests_dir(), settings()["device"]["id"], '1')
        self.assertEqual(mueff_list,
                         [1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45, 1.5, 1.55, 1.6, 1.65, 1.7, 1.75, 1.8, 1.85, 1.9,
                          1.95, 2.0, 2.05, 2.1, 2.15, 2.2, 2.25, 2.3, 2.35, 2.4, 2.45, 2.5, 2.55, 2.6, 2.65, 2.7, 2.75,
                          2.8, 2.85, 2.9, 2.95, 3.0, 3.05, 3.1, 3.15, 3.2, 3.25, 3.3, 3.35, 3.4, 3.45, 3.5, 3.55, 3.6,
                          3.65, 3.7, 3.75, 3.8, 3.85, 3.9, 3.95, 4.0, 4.05, 4.1, 4.15, 4.2, 4.25, 4.3, 4.35, 4.4, 4.45,
                          4.5, 4.55, 4.6, 4.65, 4.7, 4.75, 4.8])
        self.assertEqual(r12_list, [[0.420255532, 0.4791, 0.5245, 0.5586, 0.5894, 0.6202],
                                    [0.403777033, 0.4618, 0.5072, 0.5387, 0.5708, 0.6029],
                                    [0.387937856, 0.445, 0.4904, 0.5195, 0.5528, 0.5861],
                                    [0.372722875, 0.4288, 0.4741, 0.5011, 0.5355, 0.5698],
                                    [0.358116964, 0.4131, 0.4583, 0.4835, 0.5187, 0.554],
                                    [0.344104997, 0.398, 0.443, 0.4666, 0.5026, 0.5386],
                                    [0.330671848, 0.3834, 0.4282, 0.4505, 0.4871, 0.5237],
                                    [0.317802391, 0.3694, 0.4139, 0.4351, 0.4722, 0.5093],
                                    [0.3054815, 0.3559, 0.4001, 0.4205, 0.4579, 0.4953],
                                    [0.293694049, 0.3429, 0.3867, 0.4067, 0.4442, 0.4818],
                                    [0.282424912, 0.3305, 0.3739, 0.3936, 0.4312, 0.4688],
                                    [0.271658963, 0.3187, 0.3615, 0.3813, 0.4188, 0.4563],
                                    [0.261381076, 0.3073, 0.3497, 0.3697, 0.407, 0.4442],
                                    [0.251576125, 0.2966, 0.3382, 0.3589, 0.3958, 0.4327],
                                    [0.242228984, 0.2863, 0.3273, 0.3489, 0.3852, 0.4215],
                                    [0.233324527, 0.2767, 0.3169, 0.3396, 0.3753, 0.4109],
                                    [0.224847628, 0.2675, 0.3069, 0.3311, 0.3659, 0.4007],
                                    [0.216783161, 0.2589, 0.2973, 0.3234, 0.3572, 0.3911],
                                    [0.209116, 0.2494, 0.286, 0.3142, 0.348, 0.3818],
                                    [0.201831019, 0.2419, 0.2783, 0.3063, 0.3399, 0.3736],
                                    [0.194913092, 0.2347, 0.2708, 0.2987, 0.3321, 0.3655],
                                    [0.188347093, 0.2278, 0.2635, 0.2913, 0.3245, 0.3577],
                                    [0.182117896, 0.2212, 0.2565, 0.2842, 0.3171, 0.3501],
                                    [0.176210375, 0.2148, 0.2497, 0.2773, 0.31, 0.3428],
                                    [0.170609404, 0.2086, 0.2431, 0.2706, 0.3031, 0.3356],
                                    [0.165299857, 0.2027, 0.2367, 0.2642, 0.2964, 0.3286],
                                    [0.160266608, 0.1971, 0.2306, 0.258, 0.29, 0.3219],
                                    [0.155494531, 0.1917, 0.2246, 0.2521, 0.2837, 0.3153],
                                    [0.1509685, 0.1865, 0.2189, 0.2463, 0.2777, 0.309],
                                    [0.146673389, 0.1815, 0.2134, 0.2408, 0.2718, 0.3028],
                                    [0.142594072, 0.1767, 0.208, 0.2355, 0.2662, 0.2968],
                                    [0.138715423, 0.1722, 0.2029, 0.2303, 0.2607, 0.291],
                                    [0.135022316, 0.1678, 0.1979, 0.2254, 0.2554, 0.2854],
                                    [0.131499625, 0.1637, 0.1932, 0.2207, 0.2503, 0.28],
                                    [0.128132224, 0.1597, 0.1886, 0.2161, 0.2454, 0.2747],
                                    [0.124904987, 0.1559, 0.1842, 0.2117, 0.2407, 0.2696],
                                    [0.121802788, 0.1524, 0.1799, 0.2075, 0.2361, 0.2647],
                                    [0.118810501, 0.1489, 0.1758, 0.2035, 0.2317, 0.2599],
                                    [0.115913, 0.1457, 0.1719, 0.1996, 0.2274, 0.2553],
                                    [0.112758342, 0.1426, 0.1682, 0.1959, 0.2233, 0.2508],
                                    [0.110140851, 0.1396, 0.1646, 0.1923, 0.2194, 0.2464],
                                    [0.107644293, 0.1368, 0.1611, 0.1889, 0.2156, 0.2422],
                                    [0.105264545, 0.1342, 0.1578, 0.1856, 0.2119, 0.2382],
                                    [0.102997483, 0.1317, 0.1546, 0.1824, 0.2083, 0.2343],
                                    [0.100838983, 0.1293, 0.1516, 0.1794, 0.2049, 0.2305],
                                    [0.098784922, 0.127, 0.1487, 0.1765, 0.2016, 0.2268],
                                    [0.096831177, 0.1249, 0.146, 0.1737, 0.1985, 0.2232],
                                    [0.094973624, 0.1228, 0.1433, 0.1711, 0.1954, 0.2198],
                                    [0.093208139, 0.1209, 0.1408, 0.1685, 0.1925, 0.2164],
                                    [0.091530599, 0.119, 0.1384, 0.1661, 0.1896, 0.2132],
                                    [0.08993688, 0.1173, 0.1361, 0.1637, 0.1869, 0.2101],
                                    [0.08842286, 0.1156, 0.1339, 0.1614, 0.1842, 0.2071],
                                    [0.086984413, 0.1141, 0.1318, 0.1592, 0.1817, 0.2041],
                                    [0.085617418, 0.1126, 0.1298, 0.1571, 0.1792, 0.2013],
                                    [0.08431775, 0.1111, 0.1279, 0.1551, 0.1768, 0.1985],
                                    [0.083081286, 0.1098, 0.1261, 0.1531, 0.1745, 0.1959],
                                    [0.081903901, 0.1084, 0.1244, 0.1512, 0.1723, 0.1933],
                                    [0.080781474, 0.1072, 0.1227, 0.1494, 0.1701, 0.1907],
                                    [0.07970988, 0.1059, 0.1212, 0.1476, 0.168, 0.1883],
                                    [0.078684996, 0.1048, 0.1197, 0.1459, 0.1659, 0.1859],
                                    [0.077702697, 0.1036, 0.1183, 0.1442, 0.1639, 0.1835],
                                    [0.076758862, 0.1025, 0.1169, 0.1425, 0.1619, 0.1813],
                                    [0.075849365, 0.1013, 0.1156, 0.1409, 0.16, 0.179],
                                    [0.074970085, 0.1002, 0.1143, 0.1393, 0.1581, 0.1769],
                                    [0.074116896, 0.0992, 0.1131, 0.1377, 0.1562, 0.1747],
                                    [0.073285676, 0.0981, 0.112, 0.1362, 0.1544, 0.1726],
                                    [0.0724723, 0.097, 0.1109, 0.1346, 0.1526, 0.1705],
                                    [0.071672647, 0.0958, 0.1098, 0.133, 0.1508, 0.1685],
                                    [0.070882591, 0.0947, 0.1088, 0.1315, 0.149, 0.1665],
                                    [0.07009801, 0.0936, 0.1078, 0.1299, 0.1472, 0.1645],
                                    [0.06931478, 0.0924, 0.1068, 0.1283, 0.1454, 0.1625],
                                    [0.068528777, 0.0911, 0.1058, 0.1268, 0.1437, 0.1606],
                                    [0.067735878, 0.0899, 0.1049, 0.1251, 0.141, 0.1586],
                                    [0.06693196, 0.0886, 0.104, 0.1235, 0.139, 0.1567],
                                    [0.066112898, 0.0872, 0.103, 0.1218, 0.1375, 0.1547]])
        self.assertEqual(ozone_list, [530, 434, 380, 348, 306, 270])

    def test_sunheight(self):
        mu, atmosphere_mas, hg = sunheight(settings()["station"]["latitude"],
                                           settings()["station"]["longitude"],
                                           datetime.datetime.strptime('20181203 06:43:55', '%Y%m%d %H:%M:%S'),
                                           "+3")
        self.assertEqual(mu, 8.085)
        self.assertEqual(atmosphere_mas, 9.523)
        self.assertEqual(hg, 5.475)


class TestPlotter(unittest.TestCase):
    def test_1(self):
        # print('name')
        self.assertEqual(1, 1)


if __name__ == '__main__':
    unittest.main()
