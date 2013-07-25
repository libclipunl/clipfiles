# coding=utf-8
import Tkinter as tk
import tkFileDialog

DEFAULT_DIR="ClipFiles"

class Application(tk.Frame):
    
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid(sticky=tk.N+tk.S+tk.E+tk.W)
        self._create_widgets()

    def _create_login_frame(self):        
        login_frame = tk.Frame(self)
        login_frame.grid()
                
        tk.Label(login_frame, text="Identificador CLIP").grid(column=0, row=0, sticky=tk.W)
        
        self._username_entry = tk.Entry(login_frame)
        self._username_entry.grid(column=1, row=0)
        
        tk.Label(login_frame, text="Palavra passe").grid(column=0, row=1, sticky=tk.W)
        
        self._password_entry = tk.Entry(login_frame, show="*")
        self._password_entry.grid(column=1, row=1)     
                
        self._saveuser_check = tk.Checkbutton(login_frame, text="Guardar identificador")
        self._saveuser_check.grid(columnspan=2, sticky=tk.W)
        
        self._saveuser_check = tk.Checkbutton(login_frame, text="Guardar palavra-passe")
        self._saveuser_check.grid(columnspan=2, sticky=tk.W)

        return login_frame
    
    def _create_browse_frame(self):
        browse_frame = tk.Frame(self)
        browse_frame.grid(columnspan=2)
        
        self._dir_entry = tk.Entry(browse_frame, text=DEFAULT_DIR)
        self._dir_entry.grid(row=0, columnspan=4, column=0, sticky=tk.W)
        tk.Button(browse_frame, text="Procurar", command=self._ask_dir).grid(row=0, column=9, columnspan=1, sticky=tk.E)
        
        return browse_frame
    
    def _create_widgets(self):
        self._create_login_frame()
        self._create_browse_frame()
                
        tk.Button(self, text="Iniciar Sessão", command=self._do_login).grid(columnspan=12)

    def _do_login(self):
        pass
    
    def _ask_dir(self):
        save_dir = tkFileDialog.askdirectory()
        if len(save_dir) > 0:
            entry = self._dir_entry
            entry.delete(0, tk.END)
            entry.insert(0, save_dir)
    
def main():
    app = Application()
    app.master.title("Clip Files")
    app.mainloop()
    
if __name__ == "__main__":
    main()