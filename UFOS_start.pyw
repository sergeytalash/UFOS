# Version: 2.0
# Modified: 13.08.2021
# Author: Sergey Talash
"""
Script opens settings.json configuration file and fills out the GUI form.
Turns all values back to json and saves the file when the button is pressed
"""
from tkinter import *
from tkinter import ttk

from lib import core
from lib import gui


class Gui:
    def __init__(self, pars, row, col, ignore):
        self.pars = pars
        self.row = row
        self.tree_dot = 0
        self.column = col
        self.max_row = 15
        self.padding_x = 5
        self.padding_y = 1
        self.ent = ttk.Entry(root, width=1)
        self.font = 'Arial 9'
        self.new_pars = {}
        self.selected_keys = []
        if ignore:
            self.gui_ignore = ['calibration', 'calibration2', 'channel_names', 'device', 'version']
        else:
            self.gui_ignore = []
        self.default_pars = core.get_default_settings()

    def make_admin_entry(self):
        self.ent.grid(column=1, row=0, sticky='e', padx=self.padding_x, pady=self.padding_y)
        self.ent.bind('<Return>', start_with_all_settings)

    def make_labels(self, par, selected_key=None):
        if selected_key:
            if "description" in par.keys():
                self.selected_keys = [selected_key, "description"]
        for t in par.keys():
            if t == "description":
                continue
            t2 = t
            if t in self.gui_ignore:
                continue
            if t in self.pars.keys():
                self.font = 'Arial 9 bold'
                if self.row > self.max_row:
                    self.row = 0
                    self.column += 2
            else:
                self.font = 'Arial 9'
            if self.tree_dot == 0:
                t2 = t
            if self.tree_dot == 1:
                t2 = global_separator + t
            elif self.tree_dot > 1:
                t2 = self.tree_dot * ' ' + t
            lab = ttk.Label(root, text=t2, font=self.font)
            lab.grid(column=self.column, row=self.row, sticky='w', padx=self.padding_x, pady=self.padding_y)
            self.selected_keys.append(t)
            try:
                par[t].keys()
                self.row += 1
                self.tree_dot += 1
                self.make_labels(par[t], t)
                self.tree_dot -= 1
            except AttributeError:
                self.column += 1
                if type(par[t]) == list:
                    t2 = '; '.join([str(i) for i in par[t]])
                else:
                    t2 = par[t]
                ent = ttk.Entry(root)
                ent.insert(0, str(t2))
                ent.grid(column=self.column, row=self.row, sticky='w', padx=self.padding_x, pady=self.padding_y)
                self.column -= 1
                self.row += 1
                description = self.pars
                for i in self.selected_keys:
                    if i in description.keys():
                        description = description[i]
                    if not isinstance(description, dict):
                        try:
                            gui.HoverInfo(lab, description)
                        except:
                            # Are there any missing descriptions in settings?
                            pass

            if self.selected_keys[-1] != "description":
                self.selected_keys.pop()

    def retype(self, default_value, new_value):
        if isinstance(default_value, (int, float)):
            return type(default_value)(new_value)
        if isinstance(default_value, list):
            new_value = [i.strip() for i in new_value.split(';')]
            return [self.retype(need_t, new_v) for need_t, new_v in zip(default_value, new_value)]
        else:
            return str(new_value)

    def save_params(self, *event):
        tmp_queue = []
        old_fs = 0
        for i in Widget.winfo_children(root):
            if self.ent is i:
                continue
            if type(i) == ttk.Label:
                t = str(Widget.cget(i, 'text'))
                fs = t.count(global_separator)
                if tmp_queue:
                    for k in range(old_fs - fs + 1):
                        tmp_queue.pop()
                tmp_queue.append(t.strip())
                position = ''.join(["['{}']".format(item) for item in tmp_queue])
                # Inserting all keys and values from default settings
                exec("self.new_pars{0} = self.default_pars{0}".format(position))
                old_fs = fs
            elif type(i) == ttk.Entry:
                position = ''.join(["['{}']".format(item) for item in tmp_queue])
                # Inserting values from GUI
                exec("self.new_pars{0} = self.retype(self.default_pars{0}, '{1}')".format(position, i.get()))
        for key in self.new_pars.keys():
            if isinstance(self.pars[key], str):
                self.pars[key] = self.new_pars[key]
            elif isinstance(self.pars[key], dict):
                self.pars[key] = self.new_pars[key]
        self.new_pars = self.pars

        try:
            core.update_settings(self.new_pars)
            print('UFOS {}: New settings have been written successfully.'.format(core.get_device_id()))
        except Exception as err:
            print('ERROR! New settings are incorrect! {}'.format(err))

    def make_buttons(self):
        but_save = ttk.Button(root, text='Сохранить', command=self.save_params)
        but_save.grid(column=1, row=0, sticky='w', padx=self.padding_x, pady=self.padding_y)


def start_with_all_settings(*event):
    global GUI
    global show_settings_for_station
    if GUI.ent.get() == '9':
        show_settings_for_station = False
        root.geometry('+200+10')
    else:
        show_settings_for_station = True
        root.geometry('+200+10')
    for i in Widget.winfo_children(root):
        i.destroy()
    GUI = Gui(params, 0, 0, show_settings_for_station)
    GUI.make_labels(params)
    GUI.make_admin_entry()
    GUI.make_buttons()


if __name__ == "__main__":
    """============== GUI Structure =============="""

    # Отображать только настройки для наблюдателей станции
    show_settings_for_station = True
    global_separator = ' '

    root = Tk()
    root.title('УФОС Настройка')
    root.geometry('+200+10')
    root.resizable(True, True)

    params = core.get_settings()

    GUI = Gui(params, 0, 0, show_settings_for_station)
    GUI.make_labels(params)
    GUI.make_admin_entry()
    GUI.make_buttons()

    root.mainloop()
