import os
import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class TxtPreviewApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Memoble")
        self.root.geometry("1000x600")

        self.font = ("MS Gothic", 10)
        self.left_visible = True

        self.paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.paned_window.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        self.left_frame = tk.Frame(self.paned_window, width=250)
        self.paned_window.add(self.left_frame)

        self.folder_btn = tk.Button(self.left_frame, text="フォルダ選択", command=self.choose_folder)
        self.folder_btn.pack(padx=10, pady=10)

        listbox_frame = tk.Frame(self.left_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.file_listbox = tk.Listbox(listbox_frame, font=self.font)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        list_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox.config(yscrollcommand=list_scrollbar.set)
        self.file_listbox.bind("<<ListboxSelect>>", self.preview_file)

        self.right_frame = tk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame)

        button_frame = tk.Frame(self.right_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        self.edit_mode = False
        self.edit_button = tk.Button(button_frame, text="編集モード", command=self.toggle_edit_mode)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(button_frame, text="保存", command=self.save_file, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.toggle_folder_btn = tk.Button(button_frame, text="フォルダ表示切替", command=self.toggle_folder_view)
        self.toggle_folder_btn.pack(side=tk.RIGHT, padx=5)

        text_frame = tk.Frame(self.right_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_scrollbar = tk.Scrollbar(text_frame)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_area = tk.Text(
            text_frame,
            wrap=tk.NONE,
            yscrollcommand=text_scrollbar.set,
            state=tk.DISABLED,
            font=self.font,
            undo=True,
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        text_scrollbar.config(command=self.text_area.yview)

        self.set_tab_stops()

        self.text_area.bind("<Tab>", self.insert_tab)
        self.text_area.bind("<Up>", self.navigate_file_up)
        self.text_area.bind("<Down>", self.navigate_file_down)

        self.current_folder = None
        self.current_file_path = None
        self.txt_files = []

    def set_tab_stops(self):
        font_obj = tkfont.Font(font=self.font)
        tab_width_px = int(font_obj.measure(" ") * 4)  # ピクセル幅は整数に丸める
        stops = tuple(tab_width_px * i for i in range(1, 21))  # 最大20タブ分
        self.text_area.config(tabs=stops)

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder = folder
            self.update_file_list()

    def update_file_list(self):
        self.txt_files = [f for f in os.listdir(self.current_folder) if f.lower().endswith(".txt")]
        self.file_listbox.delete(0, tk.END)
        for file in self.txt_files:
            self.file_listbox.insert(tk.END, file)
        self.text_area.config(state=tk.DISABLED)
        self.text_area.delete(1.0, tk.END)
        self.current_file_path = None
        self.exit_edit_mode()

    def preview_file(self, event):
        if self.edit_mode:
            if not self.confirm_discard_changes():
                return
            self.exit_edit_mode()

        selection = self.file_listbox.curselection()
        if selection:
            file_name = self.txt_files[selection[0]]
            file_path = os.path.join(self.current_folder, file_name)
            self.current_file_path = file_path
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_area.config(state=tk.NORMAL)
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, content)
                self.text_area.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("エラー", f"ファイルの読み込み中にエラーが発生しました:\n{e}")

    def toggle_edit_mode(self):
        if not self.current_file_path:
            messagebox.showinfo("情報", "ファイルを選択してください。")
            return

        if not self.edit_mode:
            self.edit_mode = True
            self.text_area.config(state=tk.NORMAL)
            self.edit_button.config(text="編集終了")
            self.save_button.config(state=tk.NORMAL)
            self.text_area.bind("<Control-z>", self.undo_action)
            self.text_area.unbind("<Up>")
            self.text_area.unbind("<Down>")
        else:
            if self.confirm_discard_changes():
                self.exit_edit_mode()
                self.preview_file(None)

    def exit_edit_mode(self):
        self.edit_mode = False
        self.text_area.config(state=tk.DISABLED)
        self.edit_button.config(text="編集モード")
        self.save_button.config(state=tk.DISABLED)
        self.text_area.unbind("<Control-z>")
        self.text_area.bind("<Up>", self.navigate_file_up)
        self.text_area.bind("<Down>", self.navigate_file_down)

    def undo_action(self, event):
        try:
            self.text_area.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def save_file(self):
        if not self.current_file_path:
            return
        try:
            content = self.text_area.get(1.0, tk.END)
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(content.rstrip())
            messagebox.showinfo("保存完了", "ファイルを保存しました。")
            self.exit_edit_mode()
        except Exception as e:
            messagebox.showerror("保存エラー", f"保存中にエラーが発生しました:\n{e}")

    def confirm_discard_changes(self):
        return messagebox.askyesno("編集内容の破棄", "編集内容を破棄してもよろしいですか？")

    def toggle_folder_view(self):
        if self.left_visible:
            self.paned_window.forget(self.left_frame)
            self.left_visible = False
        else:
            self.paned_window.add(self.left_frame, before=self.right_frame)
            self.left_visible = True

    def insert_tab(self, event):
        self.text_area.insert(tk.INSERT, "\t")
        return "break"

    def navigate_file_up(self, event):
        if self.edit_mode:
            return
        selection = self.file_listbox.curselection()
        if selection and selection[0] > 0:
            new_index = selection[0] - 1
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(new_index)
            self.file_listbox.activate(new_index)
            self.file_listbox.see(new_index)
            self.preview_file(None)
        return "break"

    def navigate_file_down(self, event):
        if self.edit_mode:
            return
        selection = self.file_listbox.curselection()
        if selection and selection[0] < len(self.txt_files) - 1:
            new_index = selection[0] + 1
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(new_index)
            self.file_listbox.activate(new_index)
            self.file_listbox.see(new_index)
            self.preview_file(None)
        return "break"

if __name__ == "__main__":
    root = tk.Tk()

    icon_path = resource_path("resources/Memoble_icon.ico")
    try:
        root.iconbitmap(icon_path)
    except Exception as e:
        print(f"アイコンの設定に失敗: {e}")

    app = TxtPreviewApp(root)
    root.mainloop()
