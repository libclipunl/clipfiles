# coding=utf-8
import Tkinter as tk
import ttk
import tkSimpleDialog

class LoginForm(tkSimpleDialog.Dialog):

    def body(self, master):
        self.resizable(False, False)
        self.title("Autenticação no CLIP")

        ttk.Label(master, text="Identificador CLIP:").grid(row=0, sticky=tk.W)
        ttk.Label(master, text="Palavra passe:").grid(row=1, stick=tk.W)
        
        self.e_username = ttk.Entry(master)
        self.e_username.grid(row=0, column=1)
        self.e_password = ttk.Entry(master, show="*")
        self.e_password.grid(row=1, column=1)     

        self.save_user = tk.IntVar()
        self.save_pass = tk.IntVar()
                
        c = ttk.Checkbutton(master, text="Guardar identificador", variable=self.save_user)
        c.grid(columnspan=2, sticky=tk.W)

        c = ttk.Checkbutton(master, text="Guardar palavra-passe", variable=self.save_pass)
        c.grid(columnspan=2, sticky=tk.W)

        return self.e_username

    def apply(self):
        self.user_name = self.e_username.get()
        self.password = self.e_password.get()

        self.result = (self.user_name, self.password,
                self.save_user.get(), self.save_pass.get())

