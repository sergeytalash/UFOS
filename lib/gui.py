import gc
from tkinter import TclError
from lib.core import *
from tkinter import *
from tkinter import ttk, Menu


def canvs_destroy(canvas):
    while len(canvas) > 0:
        try:
            canv, fig = canvas.pop()
            canv.get_tk_widget().destroy()
        except TclError:
            pass
    gc.collect()


def show_error_in_separate_window(reason="", human_text="", fixit=None):
    try:
        reason = str(reason).split()
        line = ""
        out = human_text
        if human_text:
            out += '\n'
        for word in reason:
            line += word + ' '
            if len(line) < 60 and reason[-1] != word:
                continue
            out += line + '\n'
            line = ""
        err_root = Tk()
        err_root.title('Ошибка')
        err_root.resizable(False, False)
        text = ttk.Label(err_root, text=out)
        button = ttk.Button(err_root, text="Закрыть", command=lambda: err_root.destroy())
        text.grid(row=0, column=0, padx=5, pady=5)
        button.grid(row=1, column=0, padx=5, pady=5)
        err_root.mainloop()
    except Exception as err:
        print(err)


class HoverInfo(Menu):
    def __init__(self, parent, text, command=None):
        self._command = command
        Menu.__init__(self, parent, tearoff=0)
        if not isinstance(text, str):
            raise TypeError('Trying to initialise a Hover Menu with a non string type: ' + text.__class__.__name__)
        toktext = text.split('\n')
        for t in toktext:
            self.add_command(label=t)
        self._displayed = False
        self.master.bind("<Enter>", self.Display)
        self.master.bind("<Leave>", self.Remove)

    def __del__(self):
        try:
            self.master.unbind("<Enter>")
            self.master.unbind("<Leave>")
        except:
            pass

    def Display(self, event):
        if not self._displayed:
            self._displayed = True
            self.post(event.x_root + 20, event.y_root - 10)
        if self._command:
            self.master.unbind_all("<Return>")
            self.master.bind_all("<Return>", self.Click)

    def Remove(self, event):
        if self._displayed:
            self._displayed = False
            self.unpost()
        if self._command:
            self.unbind_all("<Return>")

    def Click(self, event):
        self._command()

if __name__ == "__main__":
    pass
