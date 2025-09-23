import csv
import json
import os
import random
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class WordGame(tk.Tk):
    """
    Main GUI application for English-Turkish word translation game.
    Uses Tkinter with ttk for modern styling.
    Passive review mode: displays word and pronunciation (English only), reveals translation on button press.
    Tracks reviewed (known) words.
    """

    def __init__(self):
        super().__init__()
        self.title("English-Turkish Word Game")
        self.geometry("500x450")
        self.resizable(False, False)

        # Style for modern look
        style = ttk.Style()
        style.theme_use("clam")  # Modern theme

        # Load data
        self.words = self._load_words()
        self.progress_file = "storage/progress.json"
        os.makedirs("storage", exist_ok=True)
        self.known_words = self._load_progress()
        self.current_word = None
        self.mode = "en_to_tr"  # Default: English to Turkish

        # UI Setup
        self._setup_ui()

        # Initial word load
        self._load_new_word()

    def _load_words(self):
        """
        Load word list from CSV file.
        Returns list of dicts with 'en', 'tr', 'en_pron' keys.
        """
        words = []
        try:
            with open("data/words_2000.csv", "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    words.append({
                        "en": row["english"].strip(),
                        "tr": row["turkish"].strip(),
                        "en_pron": row["english_pron"].strip()
                    })
        except FileNotFoundError:
            messagebox.showerror("Error", "data/words_2000.csv not found. Please add the file.")
            self.quit()
        return words

    def _load_progress(self):
        """
        Load known words from JSON progress file.
        Returns set of English words that are reviewed/mastered.
        """
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    return set(data)
            except (json.JSONDecodeError, KeyError):
                pass
        return set()

    def _save_progress(self):
        """
        Save known words to JSON progress file.
        """
        try:
            with open(self.progress_file, "w", encoding="utf-8") as file:
                json.dump(list(self.known_words), file, ensure_ascii=False, indent=4)
        except IOError:
            messagebox.showwarning("Warning", "Could not save progress.")

    def _setup_ui(self):
        """
        Set up the GUI elements using ttk for modern appearance.
        Passive review: no input, show source word/pron (English only), reveal answer on button.
        """
        # Main frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="English ↔ Turkish Word Review", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Mode toggle
        self.mode_var = tk.StringVar(value="English to Turkish")
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        ttk.Label(mode_frame, text="Mode:").grid(row=0, column=0, padx=(0, 5))
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, values=["English to Turkish", "Turkish to English"], state="readonly", width=20)
        mode_combo.grid(row=0, column=1)
        mode_combo.bind("<<ComboboxSelected>>", self._toggle_mode)

        # Current word display
        self.word_label = ttk.Label(main_frame, text="Word will appear here", font=("Arial", 14), foreground="blue")
        self.word_label.grid(row=2, column=0, columnspan=2, pady=(0, 5))

        # Source pronunciation (English only)
        self.pron_label = ttk.Label(main_frame, text="", font=("Arial", 12, "italic"), foreground="green")
        self.pron_label.grid(row=3, column=0, columnspan=2, pady=(0, 10))

        # Answer section (initially hidden)
        answer_frame = ttk.Frame(main_frame)
        answer_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        self.answer_label = ttk.Label(answer_frame, text="", font=("Arial", 14), foreground="red")
        self.answer_label.grid(row=0, column=0, columnspan=2)
        self.answer_pron_label = ttk.Label(answer_frame, text="", font=("Arial", 12, "italic"), foreground="green")
        self.answer_pron_label.grid(row=1, column=0, columnspan=2, pady=(0, 5))

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(0, 20))

        self.show_answer_button = ttk.Button(button_frame, text="Show Answer", command=self._show_answer)
        self.show_answer_button.grid(row=0, column=0, padx=(0, 10))

        self.next_button = ttk.Button(button_frame, text="Next Word", command=self._load_new_word, state="disabled")
        self.next_button.grid(row=0, column=1)

        # Progress display
        self.progress_label = ttk.Label(main_frame, text="Known Words: 0 | Remaining: 0", font=("Arial", 10))
        self.progress_label.grid(row=6, column=0, columnspan=2)

        # Quit button
        quit_button = ttk.Button(main_frame, text="Quit", command=self.quit)
        quit_button.grid(row=7, column=0, columnspan=2, pady=(20, 0))

        # Initially hide answer
        self._hide_answer()

    def _toggle_mode(self, event=None):
        """
        Toggle between translation modes.
        """
        if self.mode_var.get() == "English to Turkish":
            self.mode = "en_to_tr"
        else:
            self.mode = "tr_to_en"
        self._load_new_word()

    def _get_unknown_words(self):
        """
        Get list of words not yet known (for review).
        """
        return [w for w in self.words if w["en"] not in self.known_words]

    def _load_new_word(self):
        """
        Load a random unknown word and display source word/pron (English only).
        Mark previous word as known if applicable.
        """
        if self.current_word and self.current_word["en"] not in self.known_words:
            self.known_words.add(self.current_word["en"])
            self._save_progress()

        unknown = self._get_unknown_words()
        if not unknown:
            messagebox.showinfo("Complete!", "You've reviewed all words! Restarting progress.")
            self.known_words.clear()
            self._save_progress()
            unknown = self.words

        self.current_word = random.choice(unknown)
        self._hide_answer()
        self.next_button.config(state="disabled")
        self.show_answer_button.config(state="normal")

        display_pron_text = ""
        answer_pron_text = ""

        if self.mode == "en_to_tr":
            display_text = self.current_word["en"]
            display_pron_text = f"Pronunciation: {self.current_word['en_pron']}"
            answer_text = self.current_word["tr"]
            # No Turkish pron
        else:
            display_text = self.current_word["tr"]
            # No Turkish pron
            answer_text = self.current_word["en"]
            answer_pron_text = f"Pronunciation: {self.current_word['en_pron']}"

        self.word_label.config(text=display_text)
        self.pron_label.config(text=display_pron_text)
        self.answer_label.config(text=answer_text)
        self.answer_pron_label.config(text=answer_pron_text)

        self._update_progress_display()

    def _show_answer(self):
        """
        Reveal the translation and its pronunciation (English only if applicable).
        """
        self.answer_label.grid(row=0, column=0, columnspan=2)
        if self.answer_pron_label.cget("text"):  # Only show if there's English pron
            self.answer_pron_label.grid(row=1, column=0, columnspan=2, pady=(0, 5))
        self.show_answer_button.config(state="disabled")
        self.next_button.config(state="normal")

    def _hide_answer(self):
        """
        Hide the answer labels.
        """
        self.answer_label.grid_remove()
        self.answer_pron_label.grid_remove()
        self.show_answer_button.config(state="normal")

    def _update_progress_display(self):
        """
        Update the known words and remaining display.
        """
        known_count = len(self.known_words)
        total_unknown = len(self._get_unknown_words())
        self.progress_label.config(text=f"Known: {known_count} | Remaining: {total_unknown}")


if __name__ == "__main__":
    app = WordGame()
    app.mainloop()
