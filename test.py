import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import fitz  # PyMuPDF

class FileManagerPDFPreview:
	def __init__(self, root):
		self.root = root
		self.root.title("ファイル操作＆PDFプレビュー")
		self.root.geometry("900x600")
		self.selected_folder = tk.StringVar()
		self.img_tk = None
		self.pdf_doc = None
		self.current_pdf_page = 0

		self.create_widgets()

	def create_widgets(self):
		# フォルダ選択
		top = tk.Frame(self.root); top.pack(fill=tk.X, padx=10, pady=5)
		tk.Label(top, text="フォルダ:").pack(side=tk.LEFT)
		tk.Entry(top, textvariable=self.selected_folder, width=60).pack(side=tk.LEFT, padx=5)
		tk.Button(top, text="選択", command=self.select_folder).pack(side=tk.LEFT)

		# メイン領域
		main = tk.Frame(self.root); main.pack(fill=tk.BOTH, expand=True, padx=10)
		self.file_list = tk.Listbox(main, selectmode=tk.SINGLE, width=30)
		self.file_list.pack(side=tk.LEFT, fill=tk.Y)
		self.file_list.bind('<<ListboxSelect>>', self.preview_file)

		# プレビュー＆スクロール
		pc = tk.Frame(main); pc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
		self.preview_text = tk.Text(pc, wrap=tk.WORD)
		self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		self.preview_text.config(state=tk.DISABLED)
		scroll = tk.Scrollbar(pc, command=self.preview_text.yview)
		scroll.pack(side=tk.RIGHT, fill=tk.Y)
		self.preview_text.config(yscrollcommand=scroll.set)

		# ページ切替ボタン
		self.page_frame = tk.Frame(self.root)
		self.page_frame.pack(pady=5)
		self.prev_btn = tk.Button(self.page_frame, text="<< 前のページ", command=self.prev_page, state=tk.DISABLED)
		self.next_btn = tk.Button(self.page_frame, text="次のページ >>", command=self.next_page, state=tk.DISABLED)
		self.prev_btn.grid(row=0, column=0, padx=5)
		self.next_btn.grid(row=0, column=1, padx=5)

		# 操作ボタン
		ops = tk.Frame(self.root); ops.pack(pady=10)
		tk.Button(ops, text="コピー", command=self.copy_file).grid(row=0, column=0, padx=5)
		tk.Button(ops, text="移動", command=self.move_file).grid(row=0, column=1, padx=5)
		tk.Button(ops, text="削除", command=self.delete_file).grid(row=0, column=2, padx=5)
		tk.Button(ops, text="リネーム", command=self.rename_file).grid(row=0, column=3, padx=5)

	def select_folder(self):
		folder = filedialog.askdirectory()
		if folder:
			self.selected_folder.set(folder)
			self.load_files()

	def load_files(self):
		self.file_list.delete(0, tk.END)
		for f in os.listdir(self.selected_folder.get()):
			path = os.path.join(self.selected_folder.get(), f)
			if os.path.isfile(path):
				self.file_list.insert(tk.END, f)
		self.clear_preview()

	def clear_preview(self):
		self.preview_text.config(state=tk.NORMAL); self.preview_text.delete(1.0, tk.END); self.preview_text.config(state=tk.DISABLED)
		self.img_tk = None; self.pdf_doc = None
		self.prev_btn.config(state=tk.DISABLED); self.next_btn.config(state=tk.DISABLED)

	def get_selected(self):
		sel = self.file_list.curselection()
		return None if not sel else os.path.join(self.selected_folder.get(), self.file_list.get(sel[0]))

	def preview_file(self, _=None):
		path = self.get_selected()
		if not path: return
		ext = os.path.splitext(path)[1].lower()
		self.clear_preview()

		if ext in [".png", ".jpg", ".jpeg", ".gif"]:
			self.show_image(path)
		elif ext in [".txt", ".jsp", ".html", ".css", ".js", ".py"]:
			self.show_text(path)
		elif ext == ".pdf":
			self.show_pdf(path, 0)
		else:
			self.show_text(None, "[プレビュー未対応ファイルです]")


	def show_image(self, path):
		img = Image.open(path); img.thumbnail((500, 500))
		self.img_tk = ImageTk.PhotoImage(img)
		self.preview_text.config(state=tk.NORMAL)
		self.preview_text.image_create(tk.END, image=self.img_tk)
		self.preview_text.config(state=tk.DISABLED)

	def show_text(self, path=None, override=None):
		text = override or ""
		if path:
			try:
				with open(path, "r", encoding="utf-8") as f:
					text = f.read()
			except Exception as e:
				text = f"[読み込み失敗]\n{e}"
		self.preview_text.config(state=tk.NORMAL); self.preview_text.insert(tk.END, text); self.preview_text.config(state=tk.DISABLED)

	def show_pdf(self, path, page_num):
		try:
			self.pdf_doc = fitz.open(path)
			self.current_pdf_page = page_num
		except Exception as e:
			self.show_text(None, f"[PDF読み込み失敗]\n{e}")
			return
		self.render_pdf_page()

	def render_pdf_page(self):
		if not self.pdf_doc: return
		page = self.pdf_doc.load_page(self.current_pdf_page)
		zoom = 2  # 高解像度サムネイル
		mat = fitz.Matrix(zoom, zoom)
		pix = page.get_pixmap(matrix=mat)
		img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
		img.thumbnail((600, 600))
		self.img_tk = ImageTk.PhotoImage(img)
		self.preview_text.config(state=tk.NORMAL); self.preview_text.delete(1.0, tk.END)
		self.preview_text.image_create(tk.END, image=self.img_tk); self.preview_text.config(state=tk.DISABLED)
		# ページボタン状態
		self.prev_btn.config(state=tk.NORMAL if self.current_pdf_page > 0 else tk.DISABLED)
		self.next_btn.config(state=tk.NORMAL if self.current_pdf_page < self.pdf_doc.page_count - 1 else tk.DISABLED)

	def prev_page(self):
		if self.current_pdf_page > 0:
			self.current_pdf_page -= 1; self.render_pdf_page()

	def next_page(self):
		if self.pdf_doc and self.current_pdf_page < self.pdf_doc.page_count - 1:
			self.current_pdf_page += 1; self.render_pdf_page()

	# 以下のファイル操作関数は省略（コピー・移動・削除・リネーム）は以前のバージョンと同じ

	def copy_file(self):
		src = self.get_selected(); 
		if not src: return
		dst = filedialog.asksaveasfilename(initialfile=os.path.basename(src))
		if dst:
			try: shutil.copy2(src, dst); messagebox.showinfo("コピー完了","コピーしました。")
			except Exception as e: messagebox.showerror("コピー失敗", str(e))

	def move_file(self):
		src = self.get_selected(); 
		if not src: return
		dst = filedialog.asksaveasfilename(initialfile=os.path.basename(src))
		if dst:
			try: shutil.move(src, dst); self.load_files(); messagebox.showinfo("移動完了","移動しました。")
			except Exception as e: messagebox.showerror("移動失敗", str(e))

	def delete_file(self):
		src = self.get_selected()
		if not src: return
		if messagebox.askyesno("確認", f"{os.path.basename(src)} を削除しますか？"):
			try: os.remove(src); self.load_files(); messagebox.showinfo("削除完了","削除しました。")
			except Exception as e: messagebox.showerror("削除失敗", str(e))

	def rename_file(self):
		src = self.get_selected()
		if not src: return
		new = filedialog.asksaveasfilename(initialfile=os.path.basename(src))
		if new:
			try: os.rename(src, new); self.load_files(); messagebox.showinfo("リネーム完了","名前を変更しました。")
			except Exception as e: messagebox.showerror("リネーム失敗", str(e))


if __name__ == "__main__":
	root = tk.Tk()
	app = FileManagerPDFPreview(root)
	root.mainloop()
