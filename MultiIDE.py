# MultiIDE.py
import tkinter as tk
from tkinter import scrolledtext, ttk, Listbox, filedialog
from pygments.lexer import RegexLexer
from pygments.token import Keyword, Operator, Name, Number, Text, String, Comment
from MultiOP import execute

# --- Кастомный лексер для подсветки синтаксиса ---
class MultiOpLexer(RegexLexer):
    name = 'MultiOp'
    aliases = ['multiop']
    filenames = ['*.mo']

    tokens = {
        'root': [
            (r'let|print|and|or|not|if|while|def', Keyword),
            (r'\+|-|\*|/|<|>|=|==|,', Operator),
            (r'[a-zA-Z_][a-zA-Z0-9_]*', Name),
            (r'\d+', Number),
            (r'"[^"]*"', String),
            (r'\#.*', Comment),  # Простой паттерн для комментариев
            (r'\s+', Text),
            (r'\(|\)', Operator),
        ]
    }

# --- Графический интерфейс ---
class MultiOpIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("MultiOp IDE")

        # Текстовый редактор
        self.editor = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
        self.editor.pack(padx=10, pady=5)
        self.editor.bind('<KeyRelease>', self.on_key_release)

        # Кнопки
        frame = ttk.Frame(root)
        frame.pack(pady=5)
        ttk.Button(frame, text="Run", command=self.run_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=5)

        # Область вывода
        self.output = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=10)
        self.output.pack(padx=10, pady=5)

        # Инициализация
        self.last_text = ""
        self.variables = set()
        self.suggestion_box = None
        self.suggestions = []

        # Привязка событий для автодополнения
        self.editor.bind('<Return>', self.apply_suggestion)
        self.editor.bind('<Tab>', self.apply_suggestion)
        self.editor.bind('<Escape>', self.hide_suggestions)
        self.editor.bind('<Button-1>', self.hide_suggestions)

    def on_key_release(self, event):
        self.highlight_syntax()
        self.show_suggestions()

    def highlight_syntax(self):
        current_text = self.editor.get("1.0", tk.END).rstrip()
        if current_text == self.last_text:
            return

        cursor_pos = self.editor.index(tk.INSERT)
        for tag in self.editor.tag_names():
            self.editor.tag_remove(tag, "1.0", tk.END)

        lexer = MultiOpLexer()
        start_index = "1.0"
        for token, content in lexer.get_tokens(current_text):
            end_index = f"{start_index}+{len(content)}c"
            if token == Keyword:
                self.editor.tag_add('keyword', start_index, end_index)
            elif token == Operator:
                self.editor.tag_add('operator', start_index, end_index)
            elif token == Number:
                self.editor.tag_add('number', start_index, end_index)
            elif token == Name:
                self.editor.tag_add('name', start_index, end_index)
                if content not in {'let', 'print', 'and', 'or', 'not', 'if', 'while', 'def'}:
                    self.variables.add(content)
            elif token == String:
                self.editor.tag_add('string', start_index, end_index)
            elif token == Comment:
                self.editor.tag_add('comment', start_index, end_index)
            start_index = end_index

        self.editor.tag_config('keyword', foreground='blue')
        self.editor.tag_config('operator', foreground='red')
        self.editor.tag_config('number', foreground='green')
        self.editor.tag_config('name', foreground='purple')
        self.editor.tag_config('string', foreground='orange')
        self.editor.tag_config('comment', foreground='gray')

        self.editor.mark_set(tk.INSERT, cursor_pos)
        self.last_text = current_text

    def show_suggestions(self):
        self.hide_suggestions()

        cursor_pos = self.editor.index(tk.INSERT)
        line, col = map(int, cursor_pos.split('.'))
        text = self.editor.get(f"{line}.0", f"{line}.{col}")
        last_word = text.split()[-1] if text.split() else ""

        if not last_word or last_word.isspace():
            return

        self.suggestions = [w for w in {'let', 'print', 'and', 'or', 'not', 'if', 'while', 'def'} | self.variables if w.startswith(last_word)]
        if not self.suggestions:
            return

        cursor_bbox = self.editor.bbox(cursor_pos)
        if not cursor_bbox:
            return
        x, y, _, _ = cursor_bbox
        x += self.editor.winfo_x()
        y += self.editor.winfo_y() + 20

        self.suggestion_box = Listbox(self.root, height=min(5, len(self.suggestions)))
        self.suggestion_box.place(x=x, y=y)
        for suggestion in self.suggestions:
            self.suggestion_box.insert(tk.END, suggestion)
        self.suggestion_box.select_set(0)

    def apply_suggestion(self, event):
        if self.suggestion_box and self.suggestions:
            selected_index = self.suggestion_box.curselection()
            if selected_index:
                suggestion = self.suggestions[selected_index[0]]
                cursor_pos = self.editor.index(tk.INSERT)
                line, col = map(int, cursor_pos.split('.'))
                text = self.editor.get(f"{line}.0", f"{line}.{col}")
                last_word = text.split()[-1] if text.split() else ""
                self.editor.delete(f"{line}.{col-len(last_word)}", cursor_pos)
                self.editor.insert(cursor_pos, suggestion)
                self.hide_suggestions()
            return "break"

        if event.keysym == 'Return':
            self.editor.insert(tk.INSERT, '\n')
            self.hide_suggestions()
        return "break"

    def hide_suggestions(self, event=None):
        if self.suggestion_box:
            self.suggestion_box.destroy()
            self.suggestion_box = None

    def run_code(self):
        code = self.editor.get("1.0", tk.END)
        result = execute(code)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, result)

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".mo", filetypes=[("MultiOp Files", "*.mo"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.editor.get("1.0", tk.END))

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("MultiOp Files", "*.mo"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.editor.delete("1.0", tk.END)
                self.editor.insert(tk.END, f.read())
            self.highlight_syntax()  # Принудительно обновляем подсветку

# Запуск приложения
root = tk.Tk()
app = MultiOpIDE(root)
root.mainloop()