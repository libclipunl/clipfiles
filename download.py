# coding=utf-8
import Tkinter as tk
import ttk
import tkFileDialog
import threading
import Queue
import os
import urllib
import urllib2
import sys
import subprocess
import ClipUNL

# FIXME: Create better icon for downloading files
ICON_FILE=None
if sys.platform.startswith("win32"):
    ICON_FILE=os.path.join("img", "clip_icon.ico")
if sys.platform.startswith("darwin"):
    ICON_FILE=os.path.join("img", "clip_icon.icns") 

# 4k ought to be enough for anybody
BLOCK_SIZE=4*1024
DEF_CLIP_DIR="CLIP"

def do_download(parent, tree, logger):
    def_dir = os.path.expanduser("~")
    logger.debug("Download process is starting")

    lock = tree.lock
    lock.acquire()
    selection = tree.selection()
    lock.release()

    if len(selection) == 0:
        return None

    save_to = tkFileDialog.askdirectory(initialdir=def_dir, 
            title="Escolha onde quer guardar os documentos. Uma pasta de nome %s será criada." % (DEF_CLIP_DIR,), 
            parent=parent)

    if len(save_to) == 0:
        return None

    save_to = os.path.join(save_to, DEF_CLIP_DIR)

    form = DownloadForm(parent, tree, save_to, logger)
    form.get_file_list(tree)
   
    logger.log("Download started")

    return form

class Downloader():
    def __init__(self, basedir, status, progress, logger):
        self._queue = Queue.Queue()
        self._basedir = basedir
        self._status = status
        self._progress = progress
        self._logger = logger

        self._quit = False

        self._downloaded = set()
        self._finished = set()
        self._error = set()
        
        self._recreate_worker()

    def _recreate_worker(self):
        worker = threading.Thread(target=self.run)

        self._worker = worker
        self._worker.started = False

    def _dl_doc(self, doc):
        logger = self._logger

        unit = doc.get_curricular_unit()
        year = unit.get_year()

        # Ugly fix: some names (Pesquisa e Otimização comes to mind) have an extra
        # space just to mess stuff up
        # FIXME: maybe fix this on the ClipUNL class?
        name = unit.get_name().rstrip()
        doctype_desc = doc.get_doctype_desc()

        url = doc.get_url()

        doc_name = doc.get_name()
        
        sub_dir = os.path.join(year, name, doctype_desc)
        dl_dir = os.path.join(self._basedir, sub_dir)
        try:
            os.makedirs(dl_dir)
        except OSError:
            pass
        
        set_status = self._status
        if not set_status is None:
            set_status("%s por %s\n(criado em %s)" % (
                doc_name,
                doc.get_teacher(),
                doc.get_date()))

        dl_path = os.path.join(dl_dir, doc_name)
        try:
            response = urllib2.urlopen(url)
            logger.log("Downloading %s (%s)" % (doc_name, url))
            total_size = response.info().getheader('Content-Length').strip()
        except Exception as e:
            logger.error("[%s] %s (%s)" % (doc_name, url, str(e)))
            self._error.add(doc)
            return
        
        bytes_read = 0
        out = open(dl_path, "wb")

        while True:
            chunk = response.read(BLOCK_SIZE)
            bytes_read += len(chunk)

            if not chunk or self.has_quit():
                break

            out.write(chunk)
            set_progress = self._progress
            if not set_progress is None:
                set_progress(float(bytes_read) / float(total_size) * 100.0)
            
        response.close()
        out.close()
        self._finished.add(doc)

    def add_docs(self, docs):
        for doc in docs:
            self.add_doc(doc)

    def add_doc(self, doc):
        logger = self._logger

        if doc in self._downloaded:
            logger.warn("Document %s has already been downloaded" % (doc.get_name()))
            return

        logger.debug("[Downloader] Document %s added" % (doc.get_name()))

        self._downloaded.add(doc)
        self._queue.put(doc)

        worker = self._worker
        if not worker.started:
            worker.started = True
            worker.start()

    def get_finished(self):
        return self._finished

    def get_addded(self):
        return self._downloaded

    def get_errors(self):
        return self._error
    
    def has_quit(self):
        return self._quit

    def quit(self, allok=False):
        logger = self._logger
        logger.debug("Asked to quit...")

        set_status = self._status
        q = self._queue

        # Empty queue so we don't get stuck on it
        while not q.empty():
            q.get_nowait()
            q.task_done()
        
        if not set_status is None and not allok:
            set_status("A cancelar todos os downloads pendentes...")

        self._quit = True

    def join(self):
        logger = self._logger

        if self.has_quit():
            logger.debug("I am quitted, no need to wait for me...")
            return
        else:
            q = self._queue
            logger.debug("Someone is waiting for me. I have %d files in queue." % \
                    (q.qsize(),))

            q.join()
            worker = self._worker

            if worker.started:
                worker.join()

    def run(self):
        logger = self._logger

        logger.debug("Starting downloader")
        q = self._queue

        while not q.empty():
            doc = q.get()
            self._dl_doc(doc)
            q.task_done()

            if self.has_quit():
                break

        self._recreate_worker()    
        logger.debug("Downloader is idle")

class DownloadForm(tk.Toplevel):
    def __init__(self, parent, tree, save_to, logger):
        tk.Toplevel.__init__(self, parent)
        self.title("Download de Documentos")
        #self.resizable(False, False)
        self.geometry("600x150")
        self.wm_iconbitmap(ICON_FILE)

        self._cancel_text = tk.StringVar()
        self._cancel_text.set("Cancelar")
        self._status = tk.StringVar()
        self._file_status = tk.StringVar()
        self._progress = tk.IntVar()
        self._dl_status = tk.StringVar()
        self._dl_progress = tk.IntVar()
        self._cancel = False
        self._save_to = save_to
        self._logger = logger

        logger.debug("Creating worker thread")
        self._worker = threading.Thread(target=self._get_file_list,
                args=(tree,))

        logger.debug("Creating downloader object")
        self._downloader = Downloader(save_to, self.set_dl_status,
                self.set_dl_progress, logger)
        self._queue = Queue.Queue()

        self._create_widgets()
        self.protocol('WM_DELETE_WINDOW', self.cancel)

    def _create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        label = ttk.Label(frame, text="", textvariable=self._status)
        label.pack(fill=tk.X)

        label = ttk.Label(frame, text="", textvariable=self._file_status)
        label.pack(fill=tk.X)

        progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, variable=self._progress)
        progress.pack(fill=tk.X)

        label = ttk.Label(frame, text="", textvariable=self._dl_status)
        label.pack(fill=tk.X)
        
        progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, variable=self._dl_progress)
        progress.pack(fill=tk.X)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        button = ttk.Button(button_frame, text="Cancelar", command=self.cancel, 
                textvariable=self._cancel_text)
        button.pack(side=tk.RIGHT, padx=3)

        button = ttk.Button(button_frame, text="Abrir Pasta", command=self.open_folder)
        button.pack(side=tk.RIGHT, padx=3)

    def open_folder(self):
        # We gotta do this platform specific...
        save_to = self._save_to
        try:
            if sys.platform == "win32":
                os.startfile(save_to)
                #subprocess.Popen(['start', save_to])
            elif sys.platform == "darwin":
                subprocess.Popen(['open', save_to])
            else:
                # In BSD and Linux this should work, right?
                # If there's no xdg-open, well, we're doomed
                subprocess.Popen(['xdg-open', save_to])
                
        except:
            # If this doesn't work, let's rely on user instinct ;)
            # He/She will probably click the button again until it works...
            pass
    
    def cancel(self):
        # We've already done the cancelation dance... Why repeat it?
        if self._cancel:
            return

        logger = self._logger

        self.set_status("A cancelar... Por favor aguarde")
        self._cancel = True

        worker = self._worker
        downloader = self._downloader

        downloader.quit()
        logger.debug("Waiting for worker thread to finish its job")
        worker.join()
        logger.debug("Worker thread is done")

        self.destroy()

    def set_status(self, msg):
        self._status.set(msg)

    def set_progress(self, progress):
        self._progress.set(progress)

    def set_dl_status(self, msg):
        self._dl_status.set(msg)

    def set_dl_progress(self, progress):
        self.update_progress()
        self._dl_progress.set(progress)

    def is_working(self):
        downloader = self._downloader
        return not downloader.has_quit()

    def get_file_list(self, tree):
        logger = self._logger
        worker = self._worker

        logger.debug("Starting worker thread")
        worker.start()

    def update_progress(self):
        downloader = self._downloader

        finished = len(downloader.get_finished())
        added = len(downloader.get_addded())
        errors = len(downloader.get_errors())

        error_str = ""
        if errors > 0:
            error_str = "(%d ficheiros não descarregados)" % (errors,)

        self._file_status.set("Descarregados %d de %d ficheiros %s" % (finished, added, error_str))

        if added > 0:
            val = float(finished + errors) / float(added) * 100.0
        else:
            val = 0

        self.set_progress(val)
        

    def _get_file_list(self, tree):
        logger = self._logger

        def dl_unit_docs(unit, doctype=None):
            name = unit.get_name()
            logger.debug("Getting %s document list" % (name,))
            self.set_status("A listar documentos de %s" % (name,))
            downloader = self._downloader

            doctypes = None
            if doctype is None:
                logger.debug("Getting doctypes for %s" % (name,))
                doctypes = unit.get_doctypes()
                doctypes = filter(lambda (k,v): v > 0,
                        unit.get_doctypes().iteritems())

            else:
                # I put zero just because. It doesn't get used
                doctypes = [(doctype, 0)]

            all_docs = set()
            for (doctype_, count) in doctypes:
                docs = unit.get_documents(doctype_)

                if downloader.has_quit():
                    return None
                downloader.add_docs(docs)

                all_docs = all_docs | set(docs)


            #self.update_progress()
            return set(all_docs)

        def dl_year_docs(person, year):
            units = person.get_year(year)
            docs = set()
            for unit in units:
                unit_docs = dl_unit_docs(unit)
                if not unit_docs is None:
                    docs = docs | unit_docs
                else:
                    return None

            return docs

        def dl_person_docs(person):
            years = person.get_years()
            docs = set()
            for year in years:
                year_docs = dl_year_docs(person, year)
                if not year_docs is None:
                    docs = docs | year_docs
                else:
                    return None

            return docs
        
        # A reduce would work here, but meh...
        def ancestor_selected(tree, item, selection):
            parent = tree.parent(item)
            if parent in selection:
                return True

            while parent != '':
                parent = tree.parent(parent)
                if parent in selection:
                    return True
            
            return False

        try:
            doc_set = set()

            downloader = self._downloader

            logger.log("Loading file list")
            
            lock = tree.lock

            lock.acquire()
            selection = tree.selection()
            lock.release()

            for item in selection:

                lock.acquire()
                tags = tree.item(item, "tags")
                anc_sel =  ancestor_selected(tree, item, selection)
                lock.release()

                if anc_sel:
                    continue

                if "doc" in tags:
                    lock.acquire()
                    doc = tree.c_docs[item]
                    lock.release()

                    downloader.add_download(doc)

                elif "doctype" in tags:
                    lock.acquire()
                    unit = tree.c_units[item]
                    doctype = tree.c_doctypes[item]
                    lock.release()

                    dl_unit_docs(unit, doctype)

                elif "unit" in tags:
                    lock.acquire()
                    unit = tree.c_units[item]
                    lock.release()

                    dl_unit_docs(unit)

                elif "year" in tags:
                    lock.acquire()
                    person = tree.c_people[item]
                    year = tree.c_years[item]
                    lock.release()

                    dl_year_docs(person, year)
                
                elif "role" in tags:
                    lock.acquire()
                    person = tree.c_people[item]
                    lock.release()

                    dl_person_docs(person)

                if downloader.has_quit():
                    logger.debug("Downloader quitted earlier")
                    break

                self.update_progress()
                

        except tk.TclError:
            logger.error("A tcl error happened...")

        except ClipUNL.NetworkError as error:
            downloader.quit()
            logger.error("Network error: %s" % (error,))
            self.set_status("Erro na rede. Verifique se consegue aceder ao CLIP.")


        logger.debug("Waiting for downloader to finish")
        
        if not downloader.has_quit():
            self.set_status("Listagem dos ficheiros completa")

        downloader.join()

        if not downloader.has_quit():
            self.set_status("Download de documentos completo")
            self._cancel_text.set("Fechar")
            self.update_progress()
            downloader.quit(True)

        logger.log("File listing thread done")
