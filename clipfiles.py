#!/usr/bin/env python2
# coding=utf-8
import Tkinter as tk
import tkFileDialog
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

    def do_download(self):
        save_to = tkFileDialog.askdirectory()
        if len(save_to) == 0:
            return
        
        self.set_status("A construir lista de ficheiros para download...")

        tree = self._clip_tree
        selection = tree.selection()
        doc_set = set()

        def get_unit_docs(unit):
            self.set_status("A obter lista de documentos para %s..." %
                    (unit.get_name()))

            return set(unit.get_documents())

        def get_year_docs(person, year):
            units = person.get_year(year)
            docs = set()
            for unit in units:
                docs = docs | get_unit_docs(unit)

            return docs

        def get_person_docs(person):
            years = person.get_years()
            docs = set()
            for year in years:
                docs = docs | get_year_docs(person, year)

            return docs

        for item in selection:
            tags = tree.item(item, "tags")

            if "doc" in tags:
                doc = tree.c_docs[item]
                doc_set.add(doc)

            elif "unit" in tags:
                unit = tree.c_units[item]
                doc_set = doc_set | get_unit_docs(unit)

            elif "year" in tags:
                person = tree.c_people[item]
                year = tree.c_years[item]
                doc_set = doc_set | get_year_docs(person, year)
            
            elif "role" in tags:
                person = tree.c_people[item]
                doc_set = doc_set | get_person_docs(person)
        
        for x in doc_set:
            print x.get_url()

        self.set_status("")

    def populate_year(self, item, person, year):
        tree = self._clip_tree

        units = person.get_year(year)
        units = sorted(units, key=lambda u: u.get_name())

        for unit in units:
            child = tree.insert(item, 'end', text=unit.get_name(), tags='unit')
            tree.c_people[child] = person
            tree.c_years[child] = year 
            tree.c_units[child] = unit


    def populate_role(self, item, person):
        tree = self._clip_tree

        years = person.get_years()
        years = sorted(years, reverse = True)

        for year in years:
            child = tree.insert(item, 'end', text=year, tags='year')
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
    app.mainloop()
