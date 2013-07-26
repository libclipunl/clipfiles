#!/usr/bin/env python2
# coding=utf-8
import Tkinter as tk
import ttk
import login
import json

CREDS_FILE="credentials.json"

class ClipFiles(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.grid()
        self.title("CLIP Files")

    def do_auth(self):
        credentials = self.get_credentials()
        if credentials == None:
            self.destroy()

    def get_credentials(self):
        creds = {}
        try:
            creds_f = open(CREDS_FILE, "r")
            creds = json.load(creds_f)
            creds_f.close()
        except IOError:
            pass

        result = self.ask_for_credentials(creds)
        if result is None:
            return None
        
        creds["username"] = result["username"]
        creds["password"] = result["password"]

        to_save = {}
        if result["save_pass"] == 1:
            to_save["username"] = creds["username"]
            to_save["password"] = creds["password"]
        elif result["save_user"] == 1:
            to_save["username"] = creds["username"]
        else:
            to_save = {}

        creds_f = open(CREDS_FILE, "w")
        json.dump(to_save, creds_f)
        creds_f.close()

          

    def ask_for_credentials(self, creds):
        dialog = login.LoginForm(self, creds)
        return dialog.result


if __name__ == "__main__":
    app = ClipFiles()
    app.do_auth()
    app.mainloop()
