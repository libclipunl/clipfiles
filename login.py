# coding=utf-8
import Tkinter as tk
import ttk
import tkSimpleDialog

# FIXME: Give alternate icon
class LoginForm(tkSimpleDialog.Dialog):
    def __init__(self, parent, creds, status):
        self._creds = creds
        self._status = status
        tkSimpleDialog.Dialog.__init__(self, parent)

    def body(self, master):
        self.result = None

        self.resizable(False, False)
        self.title("Autenticação no CLIP")

        ttk.Label(master, text=self._status).grid(row=0, columnspan=2)

        ttk.Label(master, text="Identificador CLIP:").grid(row=1, sticky=tk.W)
        ttk.Label(master, text="Palavra passe:").grid(row=2, stick=tk.W)
        
        creds = self._creds
        self.save_user = tk.IntVar()
        self.save_pass = tk.IntVar()

        self.e_username = ttk.Entry(master)
        self.e_username.grid(row=1, column=1)
        if "username" in creds.keys():
            self.e_username.delete(0, tk.END)
            self.e_username.insert(0, creds["username"])
            self.save_user.set(1)

        self.e_password = ttk.Entry(master, show="*")
        self.e_password.grid(row=2, column=1)     
        if "password" in creds.keys():
            self.e_password.delete(0, tk.END)
            self.e_password.insert(0, creds["password"])
            self.save_pass.set(1)

                
        c = ttk.Checkbutton(master, text="Guardar identificador", variable=self.save_user)
        c.grid(columnspan=2, sticky=tk.W)

        c = ttk.Checkbutton(master, text="Guardar palavra-passe", variable=self.save_pass)
        c.grid(columnspan=2, sticky=tk.W)

        return self.e_username

    def apply(self):
        self.username = self.e_username.get()
        self.password = self.e_password.get()

        self.result = {
            "username": self.username, 
            "password": self.password,
            "save_user": self.save_user.get(),
            "save_pass": self.save_pass.get()
        }

