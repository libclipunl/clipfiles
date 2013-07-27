#!/usr/bin/env python2
# coding=utf-8
import Tkinter as tk
import ttk
import login
import json
import ClipUNL
import sys

CREDS_FILE="credentials.json"

class ClipFiles(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.grid()
        self.title("CLIP Files")
        self.clip = ClipUNL.ClipUNL()
        
        self._create_widgets()

    def _create_widgets(self):
        def build_toolbar():
            toolbar = ttk.Frame(self, relief=tk.RAISED)
            toolbar.pack(side=tk.TOP, fill=tk.X)

            dl_button = ttk.Button(toolbar, text="Download",
                    command=self.do_download)
            dl_button.pack(side=tk.LEFT, padx=2, pady=2)

            return toolbar
        
        def build_tree():
            tree = ttk.Treeview(self, selectmode="extended")
            tree.pack(fill=tk.BOTH, expand=1)

            return tree

        def status_bar():
            self._status = tk.StringVar()
            label = ttk.Label(self, relief=tk.SUNKEN,
                    textvariable=self._status)
            label.pack(side=tk.BOTTOM, fill=tk.X)

            return label

        build_toolbar()
        self._clip_tree = build_tree()
        status_bar()

    def set_status(self, msg):
        self._status.set(msg)
        self.update()
        pass

    def do_download(self):
        pass

    def populate_tree(self):
        try:
            self.set_status("A carregar dados... Por favor aguarde")
            people = self.clip.get_people()
           
            # Show all roles
            for p in people:
                self._clip_tree.insert('', 'end', text = p.get_role())

            self.set_status("")
            return True

        except ClipUNL.ClipUNLException:
            if not self.do_auth(None):
                sys.exit(0)
            return False
        

    def do_auth(self, msg):
        self.set_status("A obter credenciais de CLIP")
        credentials = self.get_credentials(msg)
        if credentials is None:
            self.destroy()
            return False
        
        self.set_status("A iniciar sessão no CLIP")
        self.clip.login(credentials["username"],
                credentials["password"])

        if (self.clip.is_logged_in()):
            self.set_status("Sessão iniciada com sucesso")
        else:
            self.set_status("Não foi possível iniciar sessão no CLIP")
        return True

    def get_credentials(self, msg):
        creds = {}
        try:
            creds_f = open(CREDS_FILE, "r")
            creds = json.load(creds_f)
            creds_f.close()
        except IOError:
            pass

        result = self.ask_for_credentials(creds, msg)
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

        return creds

    def ask_for_credentials(self, creds, status):
        dialog = login.LoginForm(self, creds, status)
        return dialog.result

if __name__ == "__main__":
    app = ClipFiles()
    while not (app.populate_tree()): pass
    app.mainloop()
