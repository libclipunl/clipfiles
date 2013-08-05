#!/usr/bin/env python2
# coding=utf-8
import Tkinter as tk
import tkFileDialog
import tkMessageBox
import ttk
import json
import sys
import os
import traceback
import threading

import ClipUNL

import login
import download
import log

VERSION="0.0.4"
PORTABLE=False

CREDS_FILE = ".clip_credentials.json"
LOG_FILE = "clip_log.txt"

if not PORTABLE:
    USER_HOME = os.path.expanduser("~")
    CREDS_FILE = os.path.join(USER_HOME, CREDS_FILE)
    LOG_FILE = os.path.join(USER_HOME, LOG_FILE)

ICON_FILE=None
IMAGE_DIR="img"
if sys.platform.startswith("win32"):
    ICON_FILE=os.path.join(IMAGE_DIR, "clip_icon.ico")
if sys.platform.startswith("darwin"):
    ICON_FILE=os.path.join(IMAGE_DIR, "clip_icon.icns") 

IMAGES={
        "download": os.path.join(IMAGE_DIR, "download.ppm"),
        "about": os.path.join(IMAGE_DIR, "about.ppm")
        }
    
DEBUG=False

def load_images(images):
    loaded_images = {}
    for name, image in IMAGES.iteritems():
        try:
            loaded_images[name] = tk.PhotoImage(file=image)
        except:
            # If there's no icon, let's not cry a river about it
            pass

    return loaded_images

class ClipFiles(tk.Tk):
    def __init__(self, logger):
        logger.debug("Initializing clipFiles main window")

        tk.Tk.__init__(self)
        self._images = load_images(IMAGES)

        self.geometry("660x450")
        self.title("CLIP Files v%s" % (VERSION,))
        self.wm_iconbitmap(ICON_FILE)
        self.grid()

        self.clip = ClipUNL.ClipUNL()
        self._create_widgets()
        self._dl_form = None
        
        self.protocol('WM_DELETE_WINDOW', self.close)

        self.logger = logger
        logger.debug("ClipFiles main window initialized")

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

            dl_button = tk.Button(toolbar, text="Download",
                    command=self.do_download,
                    compound=tk.TOP,
                    image = self._images["download"]
                    )
            dl_button.pack(side=tk.LEFT, pady=2)

            dl_button = tk.Button(toolbar, text="Ajuda",
                    command=self.do_about,
                    compound=tk.TOP,
                    image = self._images["about"]
                    )
            dl_button.pack(side=tk.LEFT, pady=2)
        
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
            tree.lock = threading.Lock()
            
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
        logger = self.logger
        logger.debug("Main status set: %s" % (msg,))
        self._status.set(msg)

    def close(self):
        # If the main window gets closed, we don't really
        # care for anything. Abandon ship!
        logger = self.logger
        logger.debug("Close has been called on the main window, \
bailing out")

        dl_form = self._dl_form
        try:
            if not dl_form is None:
                dl_form.cancel()
                logger.debug("Pending downloads have been canceled")
        except:
            logger.error("Could't cancel pending downloads, \
continue destroying anyway...")

        self.destroy()
        logger.debug("Main window has been destroyed, bye bye")


    # TODO: Allow for multiple downloads, or enqueue them
    def do_download(self):
        dl_form = self._dl_form
        logger = self.logger

        if not dl_form is None: 
            if dl_form.is_working():
                logger.log("Tried to start download, while one is \
already running. Will be fixed, don't worry")
                return
            else:
                logger.debug("Closing old download form")
                dl_form.cancel()

        tree = self._clip_tree
        form = download.do_download(self, tree, logger)
        if form is None:
            logger.warn("User failed to select save directory")
            return

        self._dl_form = form
        form.mainloop()

    def do_about(self):
        logger = self.logger
        logger.log("Showing about message box")
        tkMessageBox.showinfo("Acerca de CLIP Files v%s" % (VERSION,), 
                """CLIP Files v%s (C) 2013 David Serrano

Site: https://github.com/libclipunl/clipfiles
E-Mail: appclipfiles@gmail.com

Visite-nos no Facebook: http://fb.com/AppCLIPFiles""" % (VERSION))

    def populate_unit(self, item, person, unit):
        tree = self._clip_tree

#        logger.debug("Populating unit %s (%s)" % (unit.get_name(), unit.get_year()))

        doctypes = unit.get_doctypes()
        doctypes = filter(lambda (k,v): v > 0,
                unit.get_doctypes().iteritems())
        doctypes = sorted(doctypes, 
                key=lambda dt: ClipUNL.DOC_TYPES[dt[0]])

        lock = tree.lock
        for (doctype, count) in doctypes:
            lock.acquire()
            child = tree.insert(item, 'end', 
                    text="%s (%d)" % (ClipUNL.DOC_TYPES[doctype], count),
                    tags='doctype')
            tree.c_people[child] = person
            tree.c_units[child] = unit
            tree.c_doctypes[child] = doctype
            lock.release()

    def populate_year(self, item, person, year):
        tree = self._clip_tree

#        logger.debug("Populating year %s" % (year,))

        years = person.get_years()
        first_year = sorted(years, reverse = True)[0]

        units = person.get_year(year)
        units = sorted(units, key=lambda u: u.get_name())

        first_person = self.clip.get_people()[0]

        lock = tree.lock
        for unit in units:
            lock.acquire()
            child = tree.insert(item, 'end', text=unit.get_name(), tags='unit')
            if year == first_year and person == first_person:
                tree.see(child)
            tree.c_people[child] = person
            tree.c_years[child] = year 
            tree.c_units[child] = unit
            unit.tree_item = child
            lock.release()

    def populate_role(self, item, person):
        tree = self._clip_tree

#        logger.debug("Populating person %s" % (person.get_role()))

        years = person.get_years()
        years = sorted(years, reverse = True)

        lock = tree.lock
        for year in years:
            lock.acquire()
            child = tree.insert(item, 'end', text=year, tags='year')
            tree.see(child)
            tree.c_people[child] = person
            tree.c_years[child] = year 
            lock.release()

            self.populate_year(child, person, year)

    def populate_tree(self):
        logger = self.logger
        logger.log("Starting tree populate thread")
        try:
            def do_populate(clip, tree, people):

                try:
                    lock = tree.lock
                    for p in people:
                        lock.acquire()
                        child = tree.insert('', 'end',
                                text=p.get_role(),
                                tags='role')

                        tree.c_people[child] = p
                        lock.release()

                        self.populate_role(child, p)

                    app.set_status("""Seleccione que conteúdos deseja guardar. \
Prima CTRL+clique para seleccionar mais que um item.""")

                    for p in people:
                        years = p.get_years()
                        for year in years:
                            units = p.get_year(year)
                            for unit in units:
                                try:
                                    child = unit.tree_item
                                    self.populate_unit(child, p, unit) 
                                except AttributeError:
                                    # For some reason a unit may be without tree_item
                                    # If that is the case, let it be and move on...
                                    pass

                except ClipUNL.NetworkError as error:
                    self._show_network_error(error)

                except tk.TclError:
                    # If there's a TclError, most likely we're
                    # quitting (on Windows at least)
                    logger.debug("A TclError happened. Most likely, the main window is being destroyed")
                    return

                except RuntimeError:
                    # Error happened? Better quit!
                    # (Same thing as above, but on Linux a least...)
                    logger.debug("A RuntimeError happened. Most likely, the main window is being destroyed")
                    return
            
            clip = self.clip
            self.set_status("A carregar dados... Por favor aguarde")

            logger.log("Getting role list from CLIP")
            people = clip.get_people()
           
            tree = self._clip_tree
            map(tree.delete, tree.get_children())

            lock = tree.lock

            lock.acquire()
            tree.c_people = {}
            tree.c_years = {}
            tree.c_units = {}
            tree.c_doctypes = {}
            tree.c_docs = {}
            lock.release()
                
            logger.log("Launching tree populate thread")
            thread = threading.Thread(target=do_populate,
                    args=(clip, tree, people))
            thread.start()

            return True

        except ClipUNL.NotLoggedIn:
            logger.debug("User is not logged in. Asking for credencials")
            if not self.do_auth(None):
                logger.log("User gave up on authenticating. Quitting the hard way.")
                sys.exit(0)
                
            return False

        except ClipUNL.NetworkError as error:
            self._show_network_error(error)

        except ClipUNL.ClipUNLException:
            logger.error("A ClipUNLException occurred. Don't know what to do, bailing out!")
            self.destroy()
            return False

    def _show_network_error(self, error):
        logger.error("NetworkError exception: %s" % str(error))
        tkMessageBox.showerror("Erro de Rede", "Houve um erro no acesso \
à rede. Verifique se está conectado à Internet, e se consegue aceder ao CLIP.")

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
        logger.log("Logging in with CLIP credentials")

        try:
            self.clip.login(
                unicode(credentials["username"]),
                unicode(credentials["password"])
            )
        except ClipUNL.NetworkError as error:
            logger.error("NetworkError exception: %s" % str(error))
            self._show_network_error()

        if (self.clip.is_logged_in()):
            self.set_status("Sessão iniciada com sucesso")
            logger.log("Logged in to CLIP")
        else:
            self.set_status("Não foi possível iniciar sessão no CLIP")
            logger.warn("Wrong username or password")
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

        logger.debug("User supplied login information, continuing...")
        
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

    logger = log.Logger(sys.stdout, True, True, True)
    def populate_tree(app):
        while not (app.populate_tree()):
            pass

    logger.log("CLIP Files v%s starting" % (VERSION,))

    logger.debug("Creating main window")
    app = ClipFiles(logger)
    logger.debug("Main window created")

    
    logger.debug("Starting tree view population")
    populate_tree(app)
    logger.debug("Tree view is being populated")

    try:
        app.mainloop()
        logger.log("Quitted cleanly, where it should")

    except Exception as e:
        logger.error("Exception occurred on the window's main loop")

    logger.log("Goodbye!")
    sys.exit(0)

