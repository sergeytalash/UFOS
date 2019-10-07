import os

def get_zd_count(home, year):
        count = 0
        path = os.path.join(home, "ZEN", year)
        with open(os.path.join(path, "ozone_{}.txt".format(year)), "w") as fw:
            for dir_path, dirs, files in os.walk(path, topdown=True):
                for file in files:
                    if "Z-D" in file or "ZD" in file:
                        with open(os.path.join(dir_path, file), "r") as fr:
                            data = fr.readlines()
                        date, time, hs, ozone = None, None, None, None
                        for line in data:
                            if "time" in line:
                                l = line.split(",")
                                date = l[1].split("=")[-1].strip()
                                time = l[2].split("=")[-1].strip()
                            if " hs" in line:
                                hs = line.split()[0] 
                            if "ozone" in line:
                                ozone = line.split()[0]
                            if "Value" in line:
                                break
                        if all((date, time, hs, ozone)):
                            print(date, time, hs, ozone, file=fw)
                            print(date)

home = os.getcwd()
while True:
    year = input("Введите год: ")
    if year.isdecimal():
        get_zd_count(home, year)
        
        break
    else:
        print("Неверный номер прибора")
input("Готово")
    
