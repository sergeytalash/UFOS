import json

with open("common_settings.json", "r") as fr:
    json_data = json.load(fr)

while True:
    ufos_new_id = input("Введите номер УФОС для дальнейшего использования программой: ")
    if ufos_new_id.isdecimal():
        json_data["device"]["id"] = int(ufos_new_id)
        with open("common_settings.json", "w") as fw:
            json.dump(json_data, fp=fw, indent=2)
        break
    else:
        print("Неверный номер прибора")
input("Готово")
    
