#!/usr/bin/env python2
# coding=utf-8
import Tkinter as tk
import tkFileDialog
import ttk
import json
import sys
import os
import traceback
import threading

import ClipUNL

import login
import download

VERSION="0.0.3"

CREDS_FILE=os.path.join(os.path.expanduser("~"), ".clip_credentials.json")

ICON_FILE=None
if sys.platform.startswith("win32"):
    ICON_FILE=os.path.join("img", "clip_icon.ico")
if sys.platform.startswith("darwin"):
    ICON_FILE=os.path.join("img", "clip_icon.icns") 
    
DEBUG=False

def dbg(msg):
    if DEBUG: print msg

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
        self.geometry("660x450")
        self.title("CLIP Files")
        self.wm_iconbitmap(ICON_FILE)
        self.grid()

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
        
            # TODO: re-enable build_filter when it is done
            #build_filter(toolbar)

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
        pass

    def do_download(self):
        form = download.do_download(self, self._clip_tree)
        if form is None:
            return

        form.mainloop()

    def populate_unit(self, item, person, unit):
        tree = self._clip_tree

        doctypes = unit.get_doctypes()
        doctypes = filter(lambda (k,v): v > 0,
                unit.get_doctypes().iteritems())
        doctypes = sorted(doctypes, 
                key=lambda dt: ClipUNL.DOC_TYPES[dt[0]])

        for (doctype, count) in doctypes:
            child = tree.insert(item, 'end', 
                    text=ClipUNL.DOC_TYPES[doctype],
                    tags='doctype')
            tree.c_people[child] = person
            tree.c_units[child] = unit
            tree.c_doctypes[child] = doctype

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

            self.populate_unit(child, person, unit)

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
            def do_populate(clip, tree, people):

                try:
                    for p in people:
                        child = tree.insert('', 'end',
                                text=p.get_role(),
                                tags='role')

                        tree.c_people[child] = p
                        self.populate_role(child, p)

                    app.set_status("""Seleccione que conteúdos deseja guardar. \
Prima CTRL+clique para seleccionar mais que um item.""")
                except tk.TclError:
                    # If there's a TclError, most likely we're
                    # quitting
                    return
            
            clip = self.clip
            people = clip.get_people()
            self.set_status("A carregar dados... Por favor aguarde")
           
            tree = self._clip_tree
            map(tree.delete, tree.get_children())

            tree.c_people = {}
            tree.c_years = {}
            tree.c_units = {}
            tree.c_doctypes = {}
            tree.c_docs = {}
                
            thread = threading.Thread(target=do_populate,
                    args=(clip, tree, people))
            thread.start()

            return True

        except ClipUNL.ClipUNLException:
            if not self.do_auth(None):
                sys.exit(0)
            return False
        

    def do_auth(self, msg):
        self.set_status("A obter credenciais do CLIP")
        credentials = self.get_credentials(msg)
        if credentials is None:
            try:
                self.destroy()
            except tk.TclError:
                pass

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

        try:
            creds_f = open(CREDS_FILE, "w")
            json.dump(to_save, creds_f)
            creds_f.close()
        except IOError:
            pass

        return creds

    def ask_for_credentials(self, creds, status):
        dialog = login.LoginForm(self, creds, status)
        return dialog.result

if __name__ == "__main__":
    # Check if only asking for version
    if len(sys.argv) > 1:
        if sys.argv[1] == "-v":
            print VERSION
            sys.exit(0)

    def populate_tree(app):
        while not (app.populate_tree()):
            pass

    
    app = ClipFiles()
    populate_tree(app)

    try:
        app.mainloop()
    except Exception as e:
        print e
