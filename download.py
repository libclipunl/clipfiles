# coding=utf-8
import Tkinter as tk
import ttk
import tkFileDialog
import threading
import Queue
import os
import urllib2

BLOCK_SIZE=1024

def get_unit_docs(unit, set_status = None, downloader = None):
    if not set_status is None:
        set_status("A listar documentos de %s" % (unit.get_name(),))
    
    docs = unit.get_documents()

    if not downloader is None:
        if downloader.has_quit():
            return None
        downloader.add_docs(docs)

    return set(docs)

def get_year_docs(person, year, set_status = None, dl = None):
    units = person.get_year(year)
    docs = set()
    for unit in units:
        unit_docs = get_unit_docs(unit, set_status, dl)
        if not unit_docs is None:
            docs = docs | unit_docs
        else:
            return None

    return docs

def get_person_docs(person, set_status = None, dl = None):
    years = person.get_years()
    docs = set()
    for year in years:
        year_docs = get_year_docs(person, year, set_status, dl)
        if not year_docs is None:
            docs = docs | year_docs
        else:
            return None

    return docs

def do_download(parent, tree):
    save_to = tkFileDialog.askdirectory()
    if len(save_to) == 0:
        return None

    form = DownloadForm(parent, save_to)
    form.get_file_list(tree)

    return form

class Downloader(threading.Thread):
    def __init__(self, basedir, label, progress):
        threading.Thread.__init__(self)
        self._queue = Queue.Queue()
        self._basedir = basedir
        self._label = label
        self._progress = progress
        self._quit = False
        self._done = False
        self._downloaded = set()

    def _dl_doc(self, doc):
        unit = doc.get_curricular_unit()
        year = unit.get_year()
        name = unit.get_name()
        url = doc.get_url()

        dl_dir = os.path.join(self._basedir, year, name)
        try:
            os.makedirs(dl_dir)
        except OSError:
            pass
        
        self._label.set("%s por %s\n(criado em %s)" % (
            doc.get_name(),
            doc.get_teacher(),
            doc.get_date()))

        dl_path = os.path.join(dl_dir, doc.get_name())
        try:
            response = urllib2.urlopen(url)
        except Exception:
            return
        
        total_size = response.info().getheader('Content-Length').strip()
        bytes_read = 0
        
        out = open(dl_path, "w")

        while True:
            chunk = response.read(BLOCK_SIZE)
            bytes_read += len(chunk)

            if not chunk or self._quit:
                break

            out.write(chunk)
            self._progress.set(float(bytes_read) / float(total_size) * 100.0)

        out.close()

    def add_docs(self, docs):
        for doc in docs:
            self.add_doc(doc)

    def add_doc(self, doc):
        if doc in self._downloaded:
            return

        self._downloaded.add(doc)
        self._queue.put(doc)
    
    def has_quit(self):
        return self._quit

    def done(self):
        self._done = True

    def quit(self):
        self._quit = True

    def run(self):
        while not self._quit:
            q = self._queue
            if not q.empty():
                doc = self._queue.get()
                self._dl_doc(doc)
            elif self._done:
                self.quit()

class DownloadForm(tk.Toplevel):
    def __init__(self, parent, save_to):
        tk.Toplevel.__init__(self, parent)
        self.title("Download de Documentos")
        self.resizable(False, False)

        self._status = tk.StringVar()
        self._progress = tk.IntVar()
        self._download = tk.StringVar()
        self._dl_progress = tk.IntVar()
        self._cancel = False

        self._worker = None
        self._downloader = Downloader(save_to, self._download, self._dl_progress)
        self._queue = Queue.Queue()

        self._create_widgets()

    def _create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=1)

        label = ttk.Label(frame, text="", textvariable=self._status)
        label.pack(fill=tk.X)

        progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, variable=self._progress)
        progress.pack(fill=tk.X)

        label = ttk.Label(frame, text="", textvariable=self._download)
        label.pack(fill=tk.X)
        
        progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, variable=self._dl_progress)
        progress.pack(fill=tk.X)

        button = ttk.Button(frame, text="Cancelar", command=self.cancel)
        button.pack(side=tk.RIGHT)

    def add_download(self, doc):
        self._queue.put(doc)
    
    # FIXME: Do me properly
    def cancel(self):
        self.set_status("A cancelar... Por favor aguarde")
        self._cancel = True
        self._downloader.quit()
    
    def set_status(self, msg):
        self._status.set(msg)
        self.update()
        pass

    def get_file_list(self, tree):
        self._worker = threading.Thread(target=self._get_file_list,
                args=(tree,))
        self._worker.start()

    def _get_file_list(self, tree):
        selection = tree.selection()
        doc_set = set()

        # FIXME: Calculate total items
        total = len(selection)
        cur = 0

        downloader = self._downloader
        downloader.start()

        for item in selection:
            tags = tree.item(item, "tags")
            cur = cur + 1
            

            if "doc" in tags:
                doc = tree.c_docs[item]
                docs = set()
                docs.add(doc)

            elif "unit" in tags:
                unit = tree.c_units[item]
                docs = get_unit_docs(unit,
                        self.set_status,
                        downloader)

            elif "year" in tags:
                person = tree.c_people[item]
                year = tree.c_years[item]
                docs = get_year_docs(person,
                        year,
                        self.set_status,
                        downloader)
            
            elif "role" in tags:
                person = tree.c_people[item]
                docs = get_person_docs(person,
                        self.set_status,
                        downloader)

            if docs is None:
                break

            val = float(cur) / float(total) * 100.0
            self._progress.set(val)

        self.set_status("Listagem dos ficheiros completa")
        downloader.done()
        downloader.join()
        self.destroy()
