# coding=utf-8
import Tkinter as tk
import ttk
import tkFileDialog
import threading
import Queue
import os
import urllib2
import sys

# FIXME: Create better icon for downloading files
ICON_FILE=None
if sys.platform.startswith("win32"):
    ICON_FILE=os.path.join("img", "clip_icon.ico")
if sys.platform.startswith("darwin"):
    ICON_FILE=os.path.join("img", "clip_icon.icns") 

# 4k ought to be enough for anybody
BLOCK_SIZE=4*1024
DEF_CLIP_DIR="CLIP"
DEBUG=False

def dbg(msg):
    if DEBUG: print msg

def do_download(parent, tree):
    def_dir = os.path.expanduser("~")

    save_to = tkFileDialog.askdirectory(initialdir=def_dir, 
            title="Escolha onde quer guardar os documentos. Uma pasta de nome %s será criada." % (DEF_CLIP_DIR,), 
            parent=parent)

    if len(save_to) == 0:
        return None

    save_to = os.path.join(save_to, DEF_CLIP_DIR)

    form = DownloadForm(parent, tree, save_to)
    form.get_file_list(tree)

    return form

class Downloader():
    def __init__(self, basedir, status, progress):
        self._queue = Queue.Queue()
        self._basedir = basedir
        self._status = status
        self._progress = progress
        self._quit = False
        self._downloaded = set()
        
        self._recreate_worker()

    def _recreate_worker(self):
        worker = threading.Thread(target=self.run)

        self._worker = worker
        self._worker.started = False

    def _dl_doc(self, doc):
        unit = doc.get_curricular_unit()
        year = unit.get_year()

        # Ugly fix: some names (Pesquisa e Otimização comes to mind) have an extra
        # space just to mess stuff up
        # FIXME: maybe fix this on the ClipUNL class?
        name = unit.get_name().rstrip()
        url = doc.get_url()
        
        dl_dir = os.path.join(self._basedir, year, name)
        try:
            os.makedirs(dl_dir)
        except OSError:
            pass
        
        set_status = self._status
        if not set_status is None:
            set_status("%s por %s\n(criado em %s)" % (
                doc.get_name(),
                doc.get_teacher(),
                doc.get_date()))

        dl_path = os.path.join(dl_dir, doc.get_name())
        dbg("Saving to %s (file: %s)" % (dl_dir, doc.get_name()))
        try:
            response = urllib2.urlopen(url)
        except Exception:
            return
        
        total_size = response.info().getheader('Content-Length').strip()
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
            
        out.close()

    def add_docs(self, docs):
        for doc in docs:
            self.add_doc(doc)

    def add_doc(self, doc):
        if doc in self._downloaded:
            return

        dbg("[Downloader] Document %s added" % (doc.get_name()))

        self._downloaded.add(doc)
        self._queue.put(doc)

        worker = self._worker
        if not worker.started:
            worker.started = True
            worker.start()
    
    def has_quit(self):
        return self._quit

    def quit(self):
        set_status = self._status
        q = self._queue

        # Empty queue so we don't get stuck on it
        while not q.empty():
            q.get()
            q.task_done()
        
        if not set_status is None:
            set_status("A cancelar todos os downloads pendentes...")

        self._quit = True

    def join(self):
        if self.has_quit():
            dbg("[Downloader] I am quitted, no need to wait for me...")
            return
        else:
            q = self._queue
            dbg("[Downloader] Someone is waiting for me. I have %d files in queue." % \
                    (q.qsize(),))

            q.join()
            worker = self._worker

            if worker.started:
                worker.join()

    def run(self):
        dbg("[Downloader] starting")
        q = self._queue

        while not q.empty():
            doc = q.get()
            self._dl_doc(doc)
            q.task_done()

            if self.has_quit():
                break

        self._recreate_worker()    
        dbg("[Downloader] quit")

class DownloadForm(tk.Toplevel):
    def __init__(self, parent, tree, save_to):
        tk.Toplevel.__init__(self, parent)
        self.title("Download de Documentos")
        #self.resizable(False, False)
        self.geometry("600x130")
        self.wm_iconbitmap(ICON_FILE)

        self._status = tk.StringVar()
        self._progress = tk.IntVar()
        self._dl_status = tk.StringVar()
        self._dl_progress = tk.IntVar()
        self._cancel = False

        dbg("[DownloadForm] Creating worker thread")
        self._worker = threading.Thread(target=self._get_file_list,
                args=(tree,))

        dbg("[DownloadForm] Creating downloader object")
        self._downloader = Downloader(save_to, self.set_dl_status, self.set_dl_progress)
        self._queue = Queue.Queue()

        self._create_widgets()
        self.protocol('WM_DELETE_WINDOW', self.cancel)

    def _create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        label = ttk.Label(frame, text="", textvariable=self._status)
        label.pack(fill=tk.X)

        progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, variable=self._progress)
        progress.pack(fill=tk.X)

        label = ttk.Label(frame, text="", textvariable=self._dl_status)
        label.pack(fill=tk.X)
        
        progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, variable=self._dl_progress)
        progress.pack(fill=tk.X)

        button = ttk.Button(frame, text="Cancelar", command=self.cancel)
        button.pack(side=tk.BOTTOM)

    def add_download(self, doc):
        self._queue.put(doc)
    
    def cancel(self):
        self.set_status("A cancelar... Por favor aguarde")
        self._cancel = True

        worker = self._worker
        downloader = self._downloader

        downloader.quit()
        dbg("[CancelButton] Waiting for worker thread to finish its job")
        worker.join()

        self.destroy()

    def set_status(self, msg):
        self._status.set(msg)

    def set_progress(self, progress):
        self._progress.set(progress)

    def set_dl_status(self, msg):
        self._dl_status.set(msg)

    def set_dl_progress(self, progress):
        self._dl_progress.set(progress)

    def is_working(self):
        downloader = self._downloader
        worker = self._worker

        return not (worker.is_alive() or downloader.has_quit())

    def get_file_list(self, tree):
        dbg("[DownloadForm] Starting worker thread")
        self._worker.start()

    def _get_file_list(self, tree):
        selection = tree.selection()
        doc_set = set()

        def dl_unit_docs(unit):
            name = unit.get_name()
            dbg("[FileList] Getting %s document list" % (name,))
            self.set_status("A listar documentos de %s" % (name,))
            downloader = self._downloader

            dbg("[FileList] Getting doctypes for %s" % (name,))
            doc_types = unit.get_doctypes()

            all_docs = set()
            for doc_type, count in doc_types.iteritems():
                if count > 0:
                    docs = unit.get_documents(doc_type)

                    if downloader.has_quit():
                        return None
                    downloader.add_docs(docs)

                    all_docs = all_docs | set(docs)

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

        # FIXME: Calculate total items
        total = len(selection)
        cur = 0

        downloader = self._downloader

        dbg("[FileList] Loading file list")

        for item in selection:
            tags = tree.item(item, "tags")
            cur = cur + 1

            dbg("[FileList] Current item %s %s" % (tree.item(item, "text"), str(tags),))

            if "doc" in tags:
                doc = tree.c_docs[item]
                downloader.add_download(doc)

            elif "unit" in tags:
                unit = tree.c_units[item]
                dl_unit_docs(unit)

            elif "year" in tags:
                person = tree.c_people[item]
                year = tree.c_years[item]
                dl_year_docs(person, year)
            
            elif "role" in tags:
                person = tree.c_people[item]
                dl_person_docs(person)

            if downloader.has_quit():
                dbg("[FileList] Downloader quitted earlier")
                break
            
            val = float(cur) / float(total) * 100.0
            self.set_progress(val)

        dbg("[FileList] Waiting for downloader to finish")
        
        if not downloader.has_quit():
            self.set_status("Listagem dos ficheiros completa")
        downloader.join()
        if not downloader.has_quit():
            self.set_status("Download de documentos completo")

        downloader.quit()
        dbg("[FileList] File listing done")
