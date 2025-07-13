import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar

class CalendarDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master.root)
        self.title("Calendar")
        self.geometry("400x300")
        self.master_app = master

        self.calendar = Calendar(self, selectmode="day")
        self.calendar.pack(pady=20, fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", self.on_close)

    def on_close(self, event=None):
        self.destroy()
