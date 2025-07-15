import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os

class FlashcardConfigurationDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Configure Flashcards")
        self.geometry("600x400")
        self.master_dialog = master

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- File Management ---
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=5)
        ttk.Label(file_frame, text="File:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_var = tk.StringVar()
        self.file_combo = ttk.Combobox(file_frame, textvariable=self.file_var, state="readonly")
        self.file_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.file_combo.bind("<<ComboboxSelected>>", self.load_cards_from_selected_file)

        self.new_file_button = ttk.Button(file_frame, text="New File", command=self.new_file)
        self.new_file_button.pack(side=tk.LEFT, padx=5)
        self.delete_file_button = ttk.Button(file_frame, text="Delete File", command=self.delete_file)
        self.delete_file_button.pack(side=tk.LEFT, padx=5)

        # --- Card Management ---
        card_frame = ttk.Frame(main_frame)
        card_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.card_listbox = tk.Listbox(card_frame)
        self.card_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.card_listbox.bind("<Double-Button-1>", self.edit_card)

        card_button_frame = ttk.Frame(card_frame)
        card_button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.new_card_button = ttk.Button(card_button_frame, text="New Card", command=self.new_card)
        self.new_card_button.pack(pady=2)
        self.edit_card_button = ttk.Button(card_button_frame, text="Edit Card", command=self.edit_card)
        self.edit_card_button.pack(pady=2)
        self.delete_card_button = ttk.Button(card_button_frame, text="Delete Card", command=self.delete_card)
        self.delete_card_button.pack(pady=2)

        self.load_ini_files()

    def load_ini_files(self):
        flashcard_dir = "flashcards"
        ini_files = [f for f in os.listdir(flashcard_dir) if f.endswith(".ini")]
        self.file_combo["values"] = ini_files
        if ini_files:
            self.file_var.set(ini_files[0])
            self.load_cards_from_selected_file()

    def load_cards_from_selected_file(self, event=None):
        filename = self.file_var.get()
        if not filename:
            return

        config = configparser.ConfigParser()
        config.read(os.path.join("flashcards", filename))

        self.card_listbox.delete(0, tk.END)
        for section in config.sections():
            self.card_listbox.insert(tk.END, section)

    def new_file(self):
        filename = tk.simpledialog.askstring("New File", "Enter new file name (without .ini extension):")
        if filename:
            filepath = os.path.join("flashcards", f"{filename}.ini")
            if not os.path.exists(filepath):
                with open(filepath, "w") as f:
                    f.write("")
                self.load_ini_files()
                self.file_var.set(f"{filename}.ini")
                self.load_cards_from_selected_file()
            else:
                messagebox.showerror("Error", "File already exists.")

    def delete_file(self):
        filename = self.file_var.get()
        if filename and messagebox.askyesno("Delete File", f"Are you sure you want to delete {filename}?"):
            os.remove(os.path.join("flashcards", filename))
            self.load_ini_files()
            self.card_listbox.delete(0, tk.END)

    def new_card(self):
        self.edit_card(new_card=True)

    def edit_card(self, event=None, new_card=False):
        filename = self.file_var.get()
        if not filename:
            messagebox.showerror("Error", "No file selected.")
            return

        selected_indices = self.card_listbox.curselection()
        if not new_card and not selected_indices:
            messagebox.showerror("Error", "No card selected.")
            return

        card_word = ""
        card_meanings = []
        card_examples = []

        if not new_card:
            card_word = self.card_listbox.get(selected_indices[0])
            config = configparser.ConfigParser()
            config.read(os.path.join("flashcards", filename))
            for key, value in config.items(card_word):
                if key.startswith('meaning'):
                    card_meanings.append(value)
                elif key.startswith('example'):
                    card_examples.append(value)

        dialog = CardEditorDialog(self, card_word, card_meanings, card_examples, new_card)
        self.wait_window(dialog)

        if dialog.saved:
            config = configparser.ConfigParser()
            config.read(os.path.join("flashcards", filename))

            if not new_card and dialog.original_word != dialog.word:
                config.remove_section(dialog.original_word)

            if not config.has_section(dialog.word):
                config.add_section(dialog.word)

            for i, meaning in enumerate(dialog.meanings):
                config.set(dialog.word, f'meaning_{i+1}', meaning)
            for i, example in enumerate(dialog.examples):
                config.set(dialog.word, f'example_{i+1}', example)

            with open(os.path.join("flashcards", filename), 'w') as configfile:
                config.write(configfile)

            self.load_cards_from_selected_file()

    def delete_card(self):
        filename = self.file_var.get()
        if not filename:
            messagebox.showerror("Error", "No file selected.")
            return

        selected_indices = self.card_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "No card selected.")
            return

        card_word = self.card_listbox.get(selected_indices[0])
        if messagebox.askyesno("Delete Card", f"Are you sure you want to delete the card '{card_word}'?"):
            config = configparser.ConfigParser()
            config.read(os.path.join("flashcards", filename))
            config.remove_section(card_word)
            with open(os.path.join("flashcards", filename), 'w') as configfile:
                config.write(configfile)
            self.load_cards_from_selected_file()

class CardEditorDialog(tk.Toplevel):
    def __init__(self, master, word, meanings, examples, new_card):
        super().__init__(master)
        self.title("Edit Card" if not new_card else "New Card")
        self.geometry("500x400")

        self.original_word = word
        self.word = word
        self.meanings = meanings
        self.examples = examples
        self.saved = False

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Word:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.word_entry = ttk.Entry(main_frame, width=50)
        self.word_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=2)
        self.word_entry.insert(0, word)

        # --- Meanings ---
        ttk.Label(main_frame, text="Meanings:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.meaning_listbox = tk.Listbox(main_frame, height=5)
        self.meaning_listbox.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        for meaning in meanings:
            self.meaning_listbox.insert(tk.END, meaning)

        meaning_button_frame = ttk.Frame(main_frame)
        meaning_button_frame.grid(row=1, column=2, sticky=tk.N)
        ttk.Button(meaning_button_frame, text="Add", command=self.add_meaning).pack()
        ttk.Button(meaning_button_frame, text="Edit", command=self.edit_meaning).pack()
        ttk.Button(meaning_button_frame, text="Delete", command=self.delete_meaning).pack()

        # --- Examples ---
        ttk.Label(main_frame, text="Examples:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.example_listbox = tk.Listbox(main_frame, height=5)
        self.example_listbox.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        for example in examples:
            self.example_listbox.insert(tk.END, example)

        example_button_frame = ttk.Frame(main_frame)
        example_button_frame.grid(row=2, column=2, sticky=tk.N)
        ttk.Button(example_button_frame, text="Add", command=self.add_example).pack()
        ttk.Button(example_button_frame, text="Edit", command=self.edit_example).pack()
        ttk.Button(example_button_frame, text="Delete", command=self.delete_example).pack()

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)

        self.save_button = ttk.Button(button_frame, text="Save", command=self.save)
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

    def add_meaning(self):
        meaning = tk.simpledialog.askstring("Add Meaning", "Enter new meaning:")
        if meaning:
            self.meaning_listbox.insert(tk.END, meaning)

    def edit_meaning(self):
        selected_indices = self.meaning_listbox.curselection()
        if selected_indices:
            original_meaning = self.meaning_listbox.get(selected_indices[0])
            new_meaning = tk.simpledialog.askstring("Edit Meaning", "Enter new meaning:", initialvalue=original_meaning)
            if new_meaning:
                self.meaning_listbox.delete(selected_indices[0])
                self.meaning_listbox.insert(selected_indices[0], new_meaning)

    def delete_meaning(self):
        selected_indices = self.meaning_listbox.curselection()
        if selected_indices:
            self.meaning_listbox.delete(selected_indices[0])

    def add_example(self):
        example = tk.simpledialog.askstring("Add Example", "Enter new example:")
        if example:
            self.example_listbox.insert(tk.END, example)

    def edit_example(self):
        selected_indices = self.example_listbox.curselection()
        if selected_indices:
            original_example = self.example_listbox.get(selected_indices[0])
            new_example = tk.simpledialog.askstring("Edit Example", "Enter new example:", initialvalue=original_example)
            if new_example:
                self.example_listbox.delete(selected_indices[0])
                self.example_listbox.insert(selected_indices[0], new_example)

    def delete_example(self):
        selected_indices = self.example_listbox.curselection()
        if selected_indices:
            self.example_listbox.delete(selected_indices[0])

    def save(self):
        self.word = self.word_entry.get()
        self.meanings = list(self.meaning_listbox.get(0, tk.END))
        self.examples = list(self.example_listbox.get(0, tk.END))
        self.saved = True
        self.destroy()
