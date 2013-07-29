#!/usr/bin/env python2
# coding=utf-8
import Tkinter as tk
import tkFileDialog
import ttk
import json
import sys
import traceback
import os

import ClipUNL

import login
import download

CREDS_FILE=os.path.join(os.path.expanduser("~"), ".clip_credentials.json")

class Catcher: 
    def __init__(self, func, subst, widget):
        self.func = func 
        self.subst = subst
        self.widget = widget
    def __call__(self, *args):
        try:
            if self.subst:
                args = apply(self.subst, args)
            return apply(self.func, args)
        except SystemExit, msg:
            raise SystemExit, msg
        except:
            traceback.print_exc(sys.stdout)
tk.CallWrapper = Catcher

class ClipFiles(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.grid()
        self.title("CLIP Files")
        self.clip = ClipUNL.ClipUNL()
        
        self._create_widgets()

    def _create_widgets(self):

        def build_toolbar():
            def build_filter(parent):
                frame = ttk.Frame(parent)
                frame.pack(side=tk.RIGHT, padx=2)

                label = ttk.Label(frame, text="Filtrar:")
                label.pack(side=tk.LEFT)

                entry = ttk.Entry(frame)
                entry.pack(side=tk.RIGHT)

                return frame

            toolbar = ttk.Frame(self, relief=tk.RAISED)
            toolbar.pack(side=tk.TOP, fill=tk.X)

            dl_button = ttk.Button(toolbar, text="Download",
                    command=self.do_download)
            dl_button.pack(side=tk.LEFT, padx=2, pady=2)
        
            build_filter(toolbar)

            return toolbar

        
        def build_tree():
            frame = ttk.Frame(self)
            frame.pack(fill=tk.BOTH, expand=1)
        
            scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL)
            scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            tree = ttk.Treeview(frame, selectmode="extended", show="tree", yscrollcommand=scroll.set)
            tree.pack(fill=tk.BOTH, expand=1)
            
            scroll["command"] = tree.yview

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

    # FIXME: Do not allow multiple download forms to be opened
    def do_download(self):
        form = download.do_download(self, self._clip_tree)
        if form is None:
            return

        #form.transient(self)
        #form.grab_set()
        #self.wait_window(form)

    def populate_year(self, item, person, year):
        tree = self._clip_tree

        years = person.get_years()
        first_year = sorted(years, reverse = True)[0]

        units = person.get_year(year)
        units = sorted(units, key=lambda u: u.get_name())

        first_person = self.clip.get_people()[0]

        for unit in units:
            child = tree.insert(item, 'end', text=unit.get_name(), tags='unit')
            if year == first_year and person == first_person:
                tree.see(child)
            tree.c_people[child] = person
            tree.c_years[child] = year 
            tree.c_units[child] = unit

    def populate_role(self, item, person):
        tree = self._clip_tree

        years = person.get_years()
        years = sorted(years, reverse = True)

        for year in years:
            child = tree.insert(item, 'end', text=year, tags='year')
            tree.see(child)
            tree.c_people[child] = person
            tree.c_years[child] = year 
            self.populate_year(child, person, year)

    def populate_tree(self):
        try:
            self.set_status("A carregar dados... Por favor aguarde")
            people = self.clip.get_people()
           
            # Show all roles
            tree = self._clip_tree
            map(tree.delete, tree.get_children())

            tree.c_people = {}
            tree.c_years = {}
            tree.c_units = {}
            tree.c_docs = {}

            for p in people:
                child = tree.insert('', 'end', text=p.get_role(),
                    tags='role')

                tree.c_people[child] = p
                self.populate_role(child, p)

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
        self.clip.login(
            unicode(credentials["username"]),
            unicode(credentials["password"])
        )

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
    try:
        app.mainloop()
    except Exception as e:
        print e
