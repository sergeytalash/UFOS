import os
from tkinter import *
from tkinter import ttk
import json
import procedures


class gui:
    def __init__(self, pars, row, col, ignore):
        self.pars = pars
        self.row = row
        self.tree_dot = 0
        self.column = col
        self.max_row = 15
        self.padx = 5
        self.pady = 1
        if ignore:
            self.gui_ignore = ['calibration', 'calibration2', 'channel_names', 'device', 'version']
        else:
            self.gui_ignore = []

    def make_admin_entry(self):
        self.ent = ttk.Entry(root, width=1)
        self.ent.grid(column=1, row=0, sticky='e', padx=self.padx, pady=self.pady)
        self.ent.bind('<Return>', start_with_all_settings)

    def make_labels(self, par):
        for t in par.keys():
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
                ##                t2 = ' ⮡ '+t
                t2 = global_separator + t
            elif self.tree_dot > 1:
                t2 = self.tree_dot * ' ' + t
            ##                t2 = self.tree_dot*global_separator+' ⮡ '+t

            lab = ttk.Label(root, text=t2, font=self.font)
            lab.grid(column=self.column, row=self.row, sticky='w', padx=self.padx, pady=self.pady)
            try:
                par[t].keys()
                self.row += 1
                self.tree_dot += 1
                self.make_labels(par[t])
                self.tree_dot -= 1
            except:
                self.column += 1
                if type(par[t]) == list:
                    t2 = '; '.join([str(i) for i in par[t]])
                else:
                    t2 = par[t]
                ent = ttk.Entry(root)
                ent.insert(0, str(t2))
                ent.grid(column=self.column, row=self.row, sticky='w', padx=self.padx, pady=self.pady)
                self.column -= 1
                self.row += 1

    def retype(self, data_need, type_of_data_to_change):
        typ = type(data_need)
        if typ == int:
            return int(type_of_data_to_change)
        elif typ == list:
            type_of_data_to_change = [i.strip() for i in type_of_data_to_change.split(';')]
            return [self.retype(need, change) for need, change in zip(data_need, type_of_data_to_change)]

        elif typ == float:
            return (float(type_of_data_to_change))
        else:
            return (str(type_of_data_to_change))

    def save_params(self, *event):
        self.new_pars = {}
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
                if fs == 0:
                    self.new_pars[tmp_queue[-1]] = {}
                elif fs == 1:
                    self.new_pars[tmp_queue[-2]][tmp_queue[-1]] = {}
                elif fs == 2:
                    self.new_pars[tmp_queue[-3]][tmp_queue[-2]][tmp_queue[-1]] = {}
                elif fs == 3:
                    self.new_pars[tmp_queue[-4]][tmp_queue[-3]][tmp_queue[-2]][tmp_queue[-1]] = {}
                old_fs = fs
            elif type(i) == ttk.Entry:
                new = i.get()
                if len(tmp_queue) == 1:
                    old = self.pars[tmp_queue[-1]]
                    t = self.retype(old, new)
                    self.new_pars[tmp_queue[-1]] = t

                elif len(tmp_queue) == 2:
                    # print(tmp_queue, tmp_queue[-2], tmp_queue[-1])
                    old = self.pars[tmp_queue[-2]][tmp_queue[-1]]
                    t = self.retype(old, new)
                    self.new_pars[tmp_queue[-2]][tmp_queue[-1]] = t

                elif len(tmp_queue) == 3:
                    old = self.pars[tmp_queue[-3]][tmp_queue[-2]][tmp_queue[-1]]
                    t = self.retype(old, new)
                    self.new_pars[tmp_queue[-3]][tmp_queue[-2]][tmp_queue[-1]] = t

                elif len(tmp_queue) == 4:
                    old = self.pars[tmp_queue[-4]][tmp_queue[-3]][tmp_queue[-2]][tmp_queue[-1]]
                    t = self.retype(old, new)
                    self.new_pars[tmp_queue[-4]][tmp_queue[-3]][tmp_queue[-2]][tmp_queue[-1]] = t
        for key in self.new_pars.keys():
            self.pars[key] = self.new_pars[key]
        self.new_pars = self.pars

        try:
            # aa = json.dumps(self.new_pars,indent='    ',sort_keys=True)
            procedures.Settings.set(os.getcwd(), self.new_pars, common_pars['device']['id'])
            # with open('settings.json','w') as f:
            #     json.dump(self.new_pars,f,indent='    ',sort_keys=True)
            print('New settings are written.')
        except Exception as err:
            print('ERROR! New settings are incorrect! {}'.format(err))

    def make_buttons(self):
        but_save = ttk.Button(root, text='Сохранить', command=self.save_params)
        but_save.grid(column=self.column, row=self.max_row * 2, sticky='we', padx=self.padx, pady=self.pady)


def start_with_all_settings(*event):
    global a
    if a.ent.get() == '9':
        show_settings_for_station = False
        root.geometry('800x600+200+100')
    else:
        show_settings_for_station = True
        root.geometry('300x200+200+100')
    for i in Widget.winfo_children(root):
        i.destroy()
    a = gui(params, 0, 0, show_settings_for_station)
    a.make_labels(params)
    a.make_admin_entry()
    a.make_buttons()


"""============== GUI Structure =============="""
## Отображать только настройки для наблюдателей станции
show_settings_for_station = True
global_separator = ' '

root = Tk()
root.title('УФОС Настройка')
root.geometry('300x200+200+100')
root.resizable(False, False)

common_pars = procedures.Settings.get_common(os.getcwd())
params = procedures.Settings.get_device(os.getcwd(), common_pars['device']['id'])

a = gui(params, 0, 0, show_settings_for_station)
a.make_labels(params)
a.make_admin_entry()
a.make_buttons()

root.mainloop()
