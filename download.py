# coding=utf-8
import Tkinter as tk
import ttk
import tkFileDialog
import threading
import Queue
import os
import urllib2
import time

# 4k ought to be enough for anybody
BLOCK_SIZE=4*1024
DEF_CLIP_DIR="CLIP"

def yield_thread():
    time.sleep(0)


def do_download(parent, tree):
    def_dir = os.path.expanduser("~")

    save_to = tkFileDialog.askdirectory(initialdir=def_dir, 
            title="Escolha onde quer guardar os documentos. Uma pasta de nome %s será criada." % (DEF_CLIP_DIR,), 
            parent=parent)

    if len(save_to) == 0:
        return None

    save_to = os.path.join(save_to, DEF_CLIP_DIR)

    form = DownloadForm(parent, save_to)
    form.get_file_list(tree)
    form.wait_for()

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
        worker = threading.Thread()
        worker = threading.Thread(target=self.run)

        self._worker = worker
        self._worker.started = False

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
        
        set_status = self._status
        if not set_status is None:
            set_status("%s por %s\n(criado em %s)" % (
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
            
            # Give other threads a chance
            yield_thread() 

        out.close()

    def add_docs(self, docs):
        for doc in docs:
            self.add_doc(doc)

    def add_doc(self, doc):
        if doc in self._downloaded:
            return

        print "[Downloader] Document %s added" % (doc.get_name())

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
            print "[Downloader] I am quitted, no need to wait for me..."
            return
        else:
            q = self._queue
            print "[Downloader] Someone is waiting for me. I have %d files in queue." % \
                    (q.qsize(),)

            q.join()
            worker = self._worker

            if worker.started:
                worker.join()

    def run(self):
        print "[Downloader] starting"
        q = self._queue

        while not q.empty():
            doc = q.get()
            self._dl_doc(doc)
            q.task_done()

            if self.has_quit():
                break

        self._recreate_worker()    
        print "[Downloader] quit"

class DownloadForm(tk.Toplevel):
    def __init__(self, parent, save_to):
        tk.Toplevel.__init__(self, parent)
        self.title("Download de Documentos")
        #self.resizable(False, False)

        self._status = tk.StringVar()
        self._progress = tk.IntVar()
        self._dl_status = tk.StringVar()
        self._dl_progress = tk.IntVar()
        self._cancel = False

        self._worker = None
        self._downloader = Downloader(save_to, self.set_dl_status, self.set_dl_progress)
        self._queue = Queue.Queue()

        self._create_widgets()
        self.protocol('WM_DELETE_WINDOW', self.cancel)

    def _create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=1)

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
        print "[CancelButton] Waiting for worker thread to finish its job"
        worker.join()

        self.destroy()

    def wait_for(self):
        worker = self._worker
        while worker.is_alive():
            try:
                self.update()
            except:
                return

        
    def set_status(self, msg):
        self._status.set(msg)
        try:
            self.update()
        except:
            pass

    def set_dl_status(self, msg):
        self._dl_status.set(msg)
        try:
            self.update()
        except:
            pass

    def set_dl_progress(self, progress):
        self._dl_progress.set(progress)

    def get_file_list(self, tree):
        print "[DownloadForm] Creating worker thread"
        self._worker = threading.Thread(target=self._get_file_list,
                args=(tree,))

        print "[DownloadForm] Starting worker thread"
        self._worker.start()

    def _get_file_list(self, tree):
        selection = tree.selection()
        doc_set = set()

        def dl_unit_docs(unit):
            self.set_status("A listar documentos de %s" % (unit.get_name(),))
            downloader = self._downloader

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

        print "[FileList] Loading file list"

        for item in selection:
            tags = tree.item(item, "tags")
            cur = cur + 1

            print "[FileList] Current tags %s" % (str(tags),)

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
                print "[FileList] Downloader quitted earlier"
                break
            
            val = float(cur) / float(total) * 100.0
            self._progress.set(val)

        print "[FileList] Waiting for downloader to finish"
        
        if not downloader.has_quit():
            self.set_status("Listagem dos ficheiros completa")
        downloader.join()
        if not downloader.has_quit():
            self.set_status("Download de documentos completo")

        print "[FileList] File listing done"
