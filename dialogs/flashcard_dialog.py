import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os
import random
from dialogs.flashcard_configuration_dialog import FlashcardConfigurationDialog

class FlashcardDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master.root)
        self.title("Flashcards")
        self.geometry("500x300")
        self.master_app = master
        self.flashcards = []
        self.current_card_index = 0
        self.showing_word = True

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- File Selection ---
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=5)
        ttk.Label(file_frame, text="File:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_var = tk.StringVar()
        self.file_combo = ttk.Combobox(file_frame, textvariable=self.file_var, state="readonly")
        self.file_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.file_combo.bind("<<ComboboxSelected>>", self.load_flashcards)

        # --- Flashcard Display ---
        self.card_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=2, padding="10")
        self.card_text = tk.Text(self.card_frame, font=("Helvetica", 18), wrap=tk.WORD, state=tk.DISABLED)
        self.card_text.pack(expand=True, fill=tk.BOTH)
        self.card_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.card_frame.bind("<Button-1>", self.flip_card)
        self.card_text.tag_config("meaning", foreground="blue")
        self.card_text.tag_config("example", foreground="green")

        # --- Controls ---
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X)
        self.prev_button = ttk.Button(control_frame, text="Previous", command=self.prev_card)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        self.next_button = ttk.Button(control_frame, text="Next", command=self.next_card)
        self.next_button.pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Delay (s):").pack(side=tk.LEFT, padx=(10, 5))
        self.delay_var = tk.StringVar(value="2")
        self.delay_entry = ttk.Entry(control_frame, textvariable=self.delay_var, width=5)
        self.delay_entry.pack(side=tk.LEFT)

        self.auto_play_button = ttk.Button(control_frame, text="Auto Play", command=self.toggle_auto_play)
        self.auto_play_button.pack(side=tk.RIGHT, padx=5)
        self.is_auto_playing = False

        self.configure_button = ttk.Button(control_frame, text="Configure", command=self.open_configuration_dialog)
        self.configure_button.pack(side=tk.RIGHT, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", self.on_close)

        self.load_ini_files()

    def load_ini_files(self):
        flashcard_dir = "flashcards"
        if not os.path.exists(flashcard_dir):
            os.makedirs(flashcard_dir)
            with open(os.path.join(flashcard_dir, "default.ini"), "w") as f:
                f.write("[Hello]\n")
                f.write("meaning_1 = A common greeting.\n")
                f.write("example_1 = 'Hello, world!' is a classic programming example.\n")
                f.write("meaning_2 = An expression of surprise.\n")
                f.write("example_2 = Hello! What are you doing here?\n")

        ini_files = [f for f in os.listdir(flashcard_dir) if f.endswith(".ini")]
        self.file_combo["values"] = ini_files
        if "default.ini" in ini_files:
            self.file_var.set("default.ini")
            self.load_flashcards()

    def load_flashcards(self, event=None):
        filename = self.file_var.get()
        if not filename:
            return

        config = configparser.ConfigParser()
        config.read(os.path.join("flashcards", filename))

        self.flashcards = []
        for section in config.sections():
            word = section
            meanings = []
            examples = []
            for key, value in config.items(section):
                if key.startswith('meaning'):
                    meanings.append(value)
                elif key.startswith('example'):
                    examples.append(value)
            self.flashcards.append({"word": word, "meanings": meanings, "examples": examples})

        random.shuffle(self.flashcards)
        self.current_card_index = 0
        self.display_card()

    def display_card(self):
        self.card_text.config(state=tk.NORMAL)
        self.card_text.delete("1.0", tk.END)
        if not self.flashcards:
            return

        card = self.flashcards[self.current_card_index]
        if self.showing_word:
            self.card_text.insert(tk.END, card["word"])
        else:
            for i, meaning in enumerate(card["meanings"]):
                self.card_text.insert(tk.END, f"Meaning {i+1}: {meaning}\n", "meaning")
            self.card_text.insert(tk.END, "\n")
            for i, example in enumerate(card["examples"]):
                self.card_text.insert(tk.END, f"Example {i+1}: {example}\n", "example")
        self.card_text.config(state=tk.DISABLED)

    def flip_card(self, event=None):
        self.showing_word = not self.showing_word
        self.display_card()

    def next_card(self):
        if self.current_card_index < len(self.flashcards) - 1:
            self.current_card_index += 1
            self.showing_word = True
            self.display_card()

    def prev_card(self):
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.showing_word = True
            self.display_card()

    def toggle_auto_play(self):
        self.is_auto_playing = not self.is_auto_playing
        if self.is_auto_playing:
            self.auto_play_button.config(text="Stop")
            self.auto_play()
        else:
            self.auto_play_button.config(text="Auto Play")

    def auto_play(self):
        if not self.is_auto_playing:
            return

        self.flip_card()
        try:
            delay = int(self.delay_var.get()) * 1000
        except ValueError:
            delay = 2000

        if self.showing_word: # After flipping back to word, move to next
            self.after(delay, self.next_card_and_continue)
        else: # After showing meaning, wait and then flip back
            self.after(delay, self.auto_play)

    def next_card_and_continue(self):
        if self.is_auto_playing:
            self.next_card()
            self.after(500, self.auto_play) # Short delay before showing the new word's meaning

    def open_configuration_dialog(self):
        config_dialog = FlashcardConfigurationDialog(self)
        self.wait_window(config_dialog)
        self.load_ini_files()

    def on_close(self, event=None):
        self.is_auto_playing = False
        self.destroy()
