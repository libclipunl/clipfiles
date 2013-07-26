#!/usr/bin/env python2
# coding=utf-8
import Tkinter as tk
import ttk
import login

class ClipFiles(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.grid()
        self.title("CLIP Files")

    def do_auth(self):
        credentials = self.get_credentials()
        print credentials

    def get_credentials(self):
        # TODO: load credentials from storage, if there are any
        return self.ask_for_credentials()

    def ask_for_credentials(self):
        dialog = login.LoginForm(self)
        return dialog.result


if __name__ == "__main__":
    app = ClipFiles()
    app.do_auth()
    app.mainloop()
