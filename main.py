import asyncio
import csv
import os
import random
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from googletrans import Translator, LANGUAGES
import re
from datetime import datetime


class WordGame(tk.Tk):
    """
    Main GUI application for English-Turkish word translation game.
    Uses Tkinter with ttk for modern styling.
    Passive review mode: displays word and pronunciation (English only), reveals translation on button press.
    Tracks reviewed (known) words via CSV 'learned' flag.
    Manual marking with "I Learned It" button.
    Imports new words from mylist.txt with auto-translation on startup if file exists.
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
        asyncio.run(self._import_from_mylist())  # Import new words if mylist.txt exists
        self.current_word = None
        self.mode = "en_to_tr"  # Default: English to Turkish
        self.known_words = {w["en"] for w in self.words if w["learned"] == 1}

        # UI Setup
        self._setup_ui()

        # Initial word load
        self._load_new_word()

    def _log_error(self, message):
        """
        Log error message to errors.txt with timestamp.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open("errors.txt", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except IOError as e:
            print(f"Failed to log error to file: {e}")

    def _load_words(self):
        """
        Load word list from CSV file.
        Returns list of dicts with 'en', 'tr', 'en_pron', 'tr_pron', 'learned' keys.
        """
        words = []
        try:
            with open("data/words_2000.csv", "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    words.append({
                        "en": row["english"].strip(),
                        "tr": row["turkish"].strip(),
                        "en_pron": row["english_pron"].strip(),
                        "tr_pron": row.get("turkish_pron", "").strip(),
                        "learned": int(row["learned"].strip())
                    })
        except FileNotFoundError:
            error_msg = "data/words_2000.csv not found. Please add the file."
            self._log_error(error_msg)
            messagebox.showerror("Error", error_msg)
            self.quit()
        return words

    async def _import_from_mylist(self):
        """
        Read English words from mylist.txt (one per line), translate to Turkish using googletrans,
        check for duplicates, and append new entries to self.words and CSV with learned=0, en_pron='', tr_pron=''.
        Runs only if mylist.txt exists.
        """
        mylist_path = "mylist.txt"
        if not os.path.exists(mylist_path):
            return

        translator = Translator()
        existing_ens = {w["en"].lower() for w in self.words}

        try:
            with open(mylist_path, "r", encoding="utf-8") as file:
                new_words = []
                for line in file:
                    en_word = line.strip()
                    if not en_word or en_word.lower() in existing_ens:
                        continue  # Skip empty or duplicates
                    try:
                        translation = await translator.translate(en_word, src='en', dest='tr')
                        tr_word = translation.text.strip()
                        new_entry = {
                            "en": en_word,
                            "tr": tr_word,
                            "en_pron": "",
                            "tr_pron": "",
                            "learned": 0
                        }
                        new_words.append(new_entry)
                        existing_ens.add(en_word.lower())
                    except Exception as e:
                        error_msg = f"Translation error for '{en_word}': {e}"
                        self._log_error(error_msg)
                        messagebox.showwarning("Translation Error", f"Could not translate '{en_word}': {e}")
                        continue

            if new_words:
                self.words.extend(new_words)
                self._save_words_to_csv()
                messagebox.showinfo("Import Complete", f"Added {len(new_words)} new words from mylist.txt.")
        except IOError as e:
            error_msg = f"IOError reading mylist.txt: {e}"
            self._log_error(error_msg)
            messagebox.showerror("File Error", f"Could not read mylist.txt: {e}")

    def _save_words_to_csv(self):
        """
        Save words list back to CSV file with learned flags.
        """
        try:
            with open("data/words_2000.csv", "w", newline="", encoding="utf-8") as file:
                fieldnames = ["english", "turkish", "english_pron", "turkish_pron", "learned"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for w in self.words:
                    writer.writerow({
                        "english": w["en"],
                        "turkish": w["tr"],
                        "english_pron": w["en_pron"],
                        "turkish_pron": w.get("tr_pron", ""),
                        "learned": w["learned"]
                    })
        except IOError as e:
            error_msg = f"IOError saving to CSV: {e}"
            self._log_error(error_msg)
            messagebox.showwarning("Warning", "Could not save to CSV.")

    def _setup_ui(self):
        """
        Set up the GUI elements using ttk for modern appearance.
        Passive review: no input, show source word/pron (English only), reveal answer on button.
        Add "I Learned It" button for manual marking.
        Add "Pronunciation" button to fetch/show pronunciation if missing.
        """
        # Main frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="English ↔ Turkish Word Review", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Mode toggle
        self.mode_var = tk.StringVar(value="English to Turkish")
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10))
        ttk.Label(mode_frame, text="Mode:").grid(row=0, column=0, padx=(0, 5))
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, values=["English to Turkish", "Turkish to English"], state="readonly", width=20)
        mode_combo.grid(row=0, column=1)
        mode_combo.bind("<<ComboboxSelected>>", self._toggle_mode)

        # Word display frame
        word_frame = ttk.Frame(main_frame)
        word_frame.grid(row=2, column=0, columnspan=3, pady=(0, 5))
        self.word_label = ttk.Label(word_frame, text="Word will appear here", font=("Arial", 14), foreground="blue")
        self.word_label.grid(row=0, column=0, sticky='w')
        self.pron_button = ttk.Button(word_frame, text="Get Pronunciation", command=self._get_pronunciation)
        self.pron_button.grid(row=0, column=1, padx=(10, 0))

        # Source pronunciation
        self.pron_label = ttk.Label(main_frame, text="", font=("Arial", 12, "italic"), foreground="green")
        self.pron_label.grid(row=3, column=0, columnspan=3, pady=(0, 10))

        # Answer section (initially hidden)
        answer_frame = ttk.Frame(main_frame)
        answer_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        self.answer_label = ttk.Label(answer_frame, text="", font=("Arial", 14), foreground="red")
        self.answer_label.grid(row=0, column=0, columnspan=3)
        self.answer_pron_label = ttk.Label(answer_frame, text="", font=("Arial", 12, "italic"), foreground="green")
        self.answer_pron_label.grid(row=1, column=0, columnspan=3, pady=(0, 5))

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(0, 20))

        self.show_answer_button = ttk.Button(button_frame, text="Show Answer", command=self._show_answer)
        self.show_answer_button.grid(row=0, column=0, padx=(0, 5))

        self.learned_button = ttk.Button(button_frame, text="I Learned It", command=self._mark_learned_and_next, state="disabled")
        self.learned_button.grid(row=0, column=1, padx=(0, 5))

        self.next_button = ttk.Button(button_frame, text="Next Word", command=self._load_new_word, state="disabled")
        self.next_button.grid(row=0, column=2)

        # Progress display
        self.progress_label = ttk.Label(main_frame, text="Known Words: 0 | Remaining: 0", font=("Arial", 10))
        self.progress_label.grid(row=6, column=0, columnspan=3)

        # Quit button
        quit_button = ttk.Button(main_frame, text="Quit", command=self.quit)
        quit_button.grid(row=7, column=0, columnspan=3, pady=(20, 0))

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
        Get list of words not yet learned (learned == 0) for review.
        """
        return [w for w in self.words if w["learned"] == 0]

    def _load_new_word(self):
        """
        Load a random unknown word and display source word/pron.
        No auto-marking; manual via button.
        """
        unknown = self._get_unknown_words()
        if not unknown:
            messagebox.showinfo("Complete!", "You've reviewed all words! Restarting progress.")
            for w in self.words:
                w["learned"] = 0
            self.known_words.clear()
            self._save_words_to_csv()
            unknown = self.words

        self.current_word = random.choice(unknown)
        self._hide_answer()
        self.next_button.config(state="disabled")
        self.learned_button.config(state="disabled")
        self.show_answer_button.config(state="normal")

        # Set pronunciation button state
        source_pron_key = "en_pron" if self.mode == "en_to_tr" else "tr_pron"
        if self.current_word[source_pron_key]:
            self.pron_button.config(text="Pronunciation", state="disabled")
        else:
            self.pron_button.config(text="Get Pronunciation", state="normal")

        if self.mode == "en_to_tr":
            display_text = self.current_word["en"]
            display_pron_text = self.current_word["en_pron"] if self.current_word["en_pron"] else ""
            if display_pron_text:
                display_pron_text = f"Pronunciation: {display_pron_text}"
            answer_text = self.current_word["tr"]
            answer_pron_text = self.current_word["tr_pron"] if self.current_word["tr_pron"] else ""
            if answer_pron_text:
                answer_pron_text = f"Pronunciation: {answer_pron_text}"
        else:
            display_text = self.current_word["tr"]
            display_pron_text = self.current_word["tr_pron"] if self.current_word["tr_pron"] else ""
            if display_pron_text:
                display_pron_text = f"Pronunciation: {display_pron_text}"
            answer_text = self.current_word["en"]
            answer_pron_text = self.current_word["en_pron"] if self.current_word["en_pron"] else ""
            if answer_pron_text:
                answer_pron_text = f"Pronunciation: {answer_pron_text}"

        self.word_label.config(text=display_text)
        self.pron_label.config(text=display_pron_text)
        self.answer_label.config(text=answer_text)
        self.answer_pron_label.config(text=answer_pron_text)

        self._update_progress_display()

    def _get_pronunciation(self):
        """
        Fetch pronunciation for the source word if missing, update CSV, and display.
        """
        if not self.current_word:
            return
        source_pron_key = "en_pron" if self.mode == "en_to_tr" else "tr_pron"
        if self.current_word[source_pron_key]:
            return  # Already have it

        if self.mode == "en_to_tr":
            pron, error = self._fetch_english_pron(self.current_word["en"])
        else:
            pron, error = self._fetch_turkish_pron(self.current_word["tr"])

        if pron:
            self.current_word[source_pron_key] = pron
            self._save_words_to_csv()
            display_pron_text = f"Pronunciation: {pron}"
            self.pron_label.config(text=display_pron_text)
            self.pron_button.config(text="Pronunciation", state="disabled")
            messagebox.showinfo("Pronunciation Added", f"Pronunciation: {pron}")
        else:
            error_msg = error or "Could not fetch pronunciation."
            self._log_error(f"Pronunciation fetch failed: {error_msg}")
            messagebox.showwarning("Failed", error_msg)

    def _fetch_english_pron(self, word):
        """
        Fetch English pronunciation using eng_to_ipa if available, simplify to Turkish-style, and return (pron, error).
        """
        error = None
        try:
            import eng_to_ipa
            ipa = eng_to_ipa.eng_to_ipa(word, accent='american')
            pron = self._simplify_english_pron(ipa)
            return pron, None
        except ImportError as e:
            error = "Please install 'eng-to-ipa' library: pip install eng-to-ipa"
            self._log_error(f"ImportError in _fetch_english_pron for '{word}': {e}")
            return None, error
        except Exception as e:
            error = f"Error fetching pronunciation for '{word}': {str(e)}"
            self._log_error(f"Exception in _fetch_english_pron for '{word}': {e}")
            return None, error

    def _simplify_english_pron(self, ipa):
        """
        Simplify IPA to approximate Turkish-style pronunciation (e.g., 'ˈbɛrli' -> 'be-rli').
        """
        if not ipa:
            return ""
        ipa = ipa.strip('/').lower()

        # Mapping common IPA to approximate Latin/Turkish letters
        mapping = {
            'ɑ': 'a', 'æ': 'e', 'ɒ': 'o', 'ʌ': 'a', 'ə': 'e',
            'ɛ': 'e', 'ɜ': 'er', 'ɪ': 'i', 'i': 'i',
            'ɔ': 'o', 'ʊ': 'u', 'u': 'u',
            'ɡ': 'g', 'ŋ': 'ng', 'ʃ': 'sh', 'ʒ': 'j', 'θ': 't', 'ð': 'd',
            'tʃ': 'ch', 'dʒ': 'j'
        }
        new_ipa = ''
        i = 0
        while i < len(ipa):
            char = ipa[i]
            if i + 1 < len(ipa) and ipa[i:i+2] in mapping:
                new_ipa += mapping[ipa[i:i+2]]
                i += 2
            elif char in mapping:
                new_ipa += mapping[char]
                i += 1
            else:
                new_ipa += char
                i += 1

        # Remove stress marks
        new_ipa = re.sub(r'[ˈˌ]', '', new_ipa)

        # Replace spaces with hyphens
        new_ipa = re.sub(r'\s+', '-', new_ipa)

        # If no hyphen and long enough, add one in the middle
        if '-' not in new_ipa and len(new_ipa) > 3:
            mid = len(new_ipa) // 2
            new_ipa = new_ipa[:mid] + '-' + new_ipa[mid:]

        return new_ipa

    def _fetch_turkish_pron(self, word):
        """
        Generate simple syllabic pronunciation for Turkish word (e.g., 'kitap' -> 'ki-tap').
        """
        if not word:
            return "", None
        if len(word) <= 2:
            return word, None
        parts = [word[i:i+2] for i in range(0, len(word), 2)]
        pron = '-'.join(part for part in parts if part)
        return pron, None

    def _mark_learned_and_next(self):
        """
        Mark current word as learned (set flag=1 in CSV), update known_words, save, then load next.
        """
        if not self.current_word:
            return
        en_word = self.current_word["en"]
        for w in self.words:
            if w["en"] == en_word:
                w["learned"] = 1
                break
        self.known_words.add(en_word)
        self._save_words_to_csv()
        self._load_new_word()

    def _show_answer(self):
        """
        Reveal the translation and its pronunciation (if applicable).
        Enable learned and next buttons.
        """
        self.answer_label.grid(row=0, column=0, columnspan=3)
        if self.answer_pron_label.cget("text"):  # Only show if there's pronunciation
            self.answer_pron_label.grid(row=1, column=0, columnspan=3, pady=(0, 5))
        self.show_answer_button.config(state="disabled")
        self.next_button.config(state="normal")
        self.learned_button.config(state="normal")

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
        remaining_count = len(self._get_unknown_words())
        self.progress_label.config(text=f"Known: {known_count} | Remaining: {remaining_count}")


if __name__ == "__main__":
    app = WordGame()
    app.mainloop()
