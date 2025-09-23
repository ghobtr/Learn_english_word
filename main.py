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
    Tracks user progress in known words.
    """

    def __init__(self):
        super().__init__()
        self.title("English-Turkish Word Game")
        self.geometry("500x400")
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
        self.score = 0
        self.correct_streak = {}  # Track consecutive corrects per word

        # UI Setup
        self._setup_ui()

        # Initial word load
        self._load_new_word()

    def _load_words(self):
        """
        Load word list from CSV file.
        Returns list of dicts with 'en' and 'tr' keys.
        """
        words = []
        try:
            with open("data/words_2000.csv", "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    words.append({"en": row["english"].strip(), "tr": row["turkish"].strip()})
        except FileNotFoundError:
            messagebox.showerror("Error", "data/words_2000.csv not found. Please add the file.")
            self.quit()
        return words

    def _load_progress(self):
        """
        Load known words from JSON progress file.
        Returns set of English words that are mastered.
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
        """
        # Main frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="English ↔ Turkish Word Game", font=("Arial", 16, "bold"))
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
        self.word_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))

        # Instruction
        instr_label = ttk.Label(main_frame, text="Enter the translation:", font=("Arial", 10))
        instr_label.grid(row=3, column=0, columnspan=2, pady=(0, 5))

        # Input entry
        self.answer_entry = ttk.Entry(main_frame, font=("Arial", 12), width=30)
        self.answer_entry.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        self.answer_entry.bind("<Return>", lambda event: self._check_answer())

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(0, 20))

        self.check_button = ttk.Button(button_frame, text="Check Answer", command=self._check_answer)
        self.check_button.grid(row=0, column=0, padx=(0, 10))

        self.next_button = ttk.Button(button_frame, text="Next Word", command=self._load_new_word, state="disabled")
        self.next_button.grid(row=0, column=1)

        # Score and progress
        self.score_label = ttk.Label(main_frame, text="Score: 0 | Known Words: 0", font=("Arial", 10))
        self.score_label.grid(row=6, column=0, columnspan=2)

        # Quit button
        quit_button = ttk.Button(main_frame, text="Quit", command=self.quit)
        quit_button.grid(row=7, column=0, columnspan=2, pady=(20, 0))

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
        Get list of words not yet known (for practice).
        """
        return [w for w in self.words if w["en"] not in self.known_words]

    def _load_new_word(self):
        """
        Load a random unknown word and display it.
        """
        unknown = self._get_unknown_words()
        if not unknown:
            messagebox.showinfo("Complete!", "You've mastered all words! Restarting progress.")
            self.known_words.clear()
            unknown = self.words

        self.current_word = random.choice(unknown)
        self.answer_entry.delete(0, tk.END)
        self.next_button.config(state="disabled")
        self.check_button.config(state="normal")

        if self.mode == "en_to_tr":
            display_text = self.current_word["en"]
            expected = self.current_word["tr"].lower()
        else:
            display_text = self.current_word["tr"]
            expected = self.current_word["en"].lower()

        self.word_label.config(text=display_text)
        self.correct_streak[self.current_word["en"]] = self.correct_streak.get(self.current_word["en"], 0)

        self._update_score_display()

    def _check_answer(self):
        """
        Check user's answer against expected translation.
        Provide feedback and update progress.
        """
        if not self.current_word:
            return

        user_answer = self.answer_entry.get().strip().lower()
        if self.mode == "en_to_tr":
            expected = self.current_word["tr"].lower()
            correct_feedback = f"Correct! Turkish: {self.current_word['tr']}"
        else:
            expected = self.current_word["en"].lower()
            correct_feedback = f"Correct! English: {self.current_word['en']}"

        if user_answer == expected:
            self.score += 1
            self.correct_streak[self.current_word["en"]] += 1
            if self.correct_streak[self.current_word["en"]] >= 3:
                self.known_words.add(self.current_word["en"])
                self._save_progress()
                messagebox.showinfo("Correct!", f"{correct_feedback}\nWord mastered!")
            else:
                messagebox.showinfo("Correct!", correct_feedback)
        else:
            self.correct_streak[self.current_word["en"]] = 0
            wrong_feedback = f"Wrong! The {self.mode.replace('_', ' ')} is: {expected.title()}"
            messagebox.showerror("Incorrect", wrong_feedback)
            self.score = max(0, self.score - 1)  # Penalty for wrong

        self.answer_entry.delete(0, tk.END)
        self.check_button.config(state="disabled")
        self.next_button.config(state="normal")
        self._update_score_display()

    def _update_score_display(self):
        """
        Update the score and known words display.
        """
        known_count = len(self.known_words)
        total_unknown = len(self._get_unknown_words())
        self.score_label.config(text=f"Score: {self.score} | Known: {known_count} | Remaining: {total_unknown}")


if __name__ == "__main__":
    app = WordGame()
    app.mainloop()
