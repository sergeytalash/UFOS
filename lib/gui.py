import gc
import tkinter
from tkinter import Menu
from tkinter import ttk


def canvs_destroy(canvas):
    while len(canvas) > 0:
        try:
            canv, fig = canvas.pop()
            canv.get_tk_widget().destroy()
        except tkinter.TclError:
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
        err_root = tkinter.Tk()
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
        self.master.bind("<Enter>", self.display)
        self.master.bind("<Leave>", self.remove)

    def __del__(self):
        try:
            self.master.unbind("<Enter>")
            self.master.unbind("<Leave>")
        except:
            pass

    def display(self, event):
        if not self._displayed:
            self._displayed = True
            self.post(event.x_root + 20, event.y_root - 10)
        if self._command:
            self.master.unbind_all("<Return>")
            self.master.bind_all("<Return>", self.click)

    def remove(self, event):
        if self._displayed:
            self._displayed = False
            self.unpost()
        if self._command:
            self.unbind_all("<Return>")

    def click(self, event):
        self._command()


def update_geometry(root):
    plotx, ploty = root.winfo_screenwidth() / 1.5, root.winfo_screenheight() / 1.5
    return plotx, ploty


if __name__ == "__main__":
    pass
