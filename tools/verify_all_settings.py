import json
import os


class Main:
    def __init__(self):
        self.home = os.path.dirname(os.getcwd())

    def get_path_by_num(self, ufos_num=None):
        if ufos_num:
            settings_path = os.path.join(self.home, "Ufos_{}".format(ufos_num), "Settings", "settings.json")
        else:
            settings_path = os.path.join(self.home, "defaults", "settings.json")
        if os.path.exists(settings_path):
            return settings_path

    @staticmethod
    def get_settings_by_path(settings_path):
        with open(settings_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def set_settings_path_by_name(data, settings_path):
        with open(settings_path, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def update_settings(self, ufos_num):
        text = ["", "Updated existing descriptions", "Created new descriptions", "Created new key and descriptions"]
        default_settings = self.get_settings_by_path(self.get_path_by_num())
        ufos_settings = self.get_settings_by_path(self.get_path_by_num(ufos_num=ufos_num))
        upadated_descriptions = {k: 0 for k in default_settings.keys()}
        for key in default_settings.keys():
            if isinstance(default_settings[key], dict) and isinstance(ufos_settings[key], dict):
                if 'description' in ufos_settings[key].keys():
                    if ufos_settings[key]['description'] == default_settings[key]['description']:
                        # Descriptions already exists
                        upadated_descriptions[key] = 0
                        continue
                    else:
                        # Update existing descriptions
                        upadated_descriptions[key] = 1
                else:
                    # Create new descriptions
                    upadated_descriptions[key] = 2

                if key in ufos_settings.keys():
                    if 'description' in default_settings[key].keys():
                        ufos_settings[key]['description'] = default_settings[key]['description']
                else:
                    # Create new key and descriptions
                    ufos_settings[key] = default_settings[key]
                    upadated_descriptions[key] = 3
        self.set_settings_path_by_name(ufos_settings, self.get_path_by_num(ufos_num=ufos_num))
        for key, value in upadated_descriptions.items():
            if value:
                print("{}: {}".format(text[value], key))
        else:
            print('Done')


if __name__ == "__main__":
    a = Main()
    try:
        while True:
            a.update_settings(ufos_num=int(input("Input UFOS id: ")))
    except KeyboardInterrupt:
        exit(0)
