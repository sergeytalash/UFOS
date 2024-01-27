from lib import com
from time import sleep
# from datetime import datetime
import numpy as np
from openpyxl import Workbook

# ========================== 1 ========================================
data = {}
for i in range(3):
    _, _, _, _, _ = com.UfosDataToCom(
        50, 1, 'Z', 'S', False).device_ask()
    spectr_Z, _, _, _, _ = com.UfosDataToCom(
        4000, 1, 'Z', 'S', False).device_ask()
    _, _, _, _, _ = com.UfosDataToCom(
        50, 1, 'D', 'S', False).device_ask()
    spectr_D, _, _, _, _ = com.UfosDataToCom(4000, 1, 'D', 'S', False).device_ask()
    spectr_ZD = np.array(spectr_Z) - np.array(spectr_D)
    data.setdefault(str(i), {}).setdefault('Z', []).extend(spectr_Z)
    data.setdefault(str(i), {}).setdefault('D', []).extend(spectr_D)
    data.setdefault(str(i), {}).setdefault('ZD', []).extend(spectr_ZD)

    # input("Finger...")
    # sleep(2)
_, _, _, _, _ = com.UfosDataToCom(50, 1, 'D', 'S', False).device_ask()

d_3_times = {}
for i in range(3):
    spectr_D, _, _, _, _ = com.UfosDataToCom(4000, 1, 'D', 'S', False).device_ask()
    d_3_times.setdefault(str(i), {}).setdefault('D', []).extend(spectr_D)

new_data = []
for k, v in data.items():
    for chan, column in v.items():
        new_data.append([f"{chan}_{k}"] + column)
for k, v in d_3_times.items():
    for chan, column in v.items():
        new_data.append([f"{chan}_{k}"] + column)
wb = Workbook()
ws = wb.active

for i in new_data:
    ws.append(i)
wb.save("spectr6.xlsx")

# ========================== 2 ========================================
# data = []
# for i in range(1):
#     print('Measuring Z')
#     spectr_Z, _, _, _, _ = com.UfosDataToCom(50, 1, 'Z', 'S', False).device_ask()
#
#     spectr_Z1, _, _, _, _ = com.UfosDataToCom(4000, 1, 'Z', 'S', False).device_ask()
#     data.append(["Z1_1"] + spectr_Z1)
#     spectr_Z2, _, _, _, _ = com.UfosDataToCom(4000, 1, 'Z', 'S', False).device_ask()
#     data.append(["Z1_2"] + spectr_Z2)
#     spectr_Z3, _, _, _, _ = com.UfosDataToCom(4000, 1, 'Z', 'S', False).device_ask()
#     data.append(["Z1_3"] + spectr_Z3)
#
#     print('Measuring D')
#     spectr_D, _, _, _, _ = com.UfosDataToCom(50, 1, 'D', 'S', False).device_ask()
#
#     spectr_D1, _, _, _, _ = com.UfosDataToCom(4000, 1, 'D', 'S', False).device_ask()
#     data.append(["D1"] + spectr_D1)
#     spectr_D2, _, _, _, _ = com.UfosDataToCom(4000, 1, 'D', 'S', False).device_ask()
#     data.append(["D2"] + spectr_D2)
#     spectr_D3, _, _, _, _ = com.UfosDataToCom(4000, 1, 'D', 'S', False).device_ask()
#     data.append(["D3"] + spectr_D3)
#
#     print('Measuring Z')
#     spectr_Z, _, _, _, _ = com.UfosDataToCom(50, 1, 'Z', 'S', False).device_ask()
#
#     spectr_Z1, _, _, _, _ = com.UfosDataToCom(4000, 1, 'Z', 'S', False).device_ask()
#     data.append(["Z2_1"] + spectr_Z1)
#     spectr_Z2, _, _, _, _ = com.UfosDataToCom(4000, 1, 'Z', 'S', False).device_ask()
#     data.append(["Z2_2"] + spectr_Z2)
#     spectr_Z3, _, _, _, _ = com.UfosDataToCom(4000, 1, 'Z', 'S', False).device_ask()
#     data.append(["Z2_3"] + spectr_Z3)
#
#
# wb = Workbook()
# ws = wb.active
#
# for i in data:
#     ws.append(i)
# wb.save("spectr3.xlsx")
