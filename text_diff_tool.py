import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import difflib
import chardet


class TextDiffTool:
    """
    文本对比工具主类
    提供图形化界面，支持左右两侧文本的输入、对比和高亮显示差异
    支持编码格式选择、实时转码、自动检测文件编码、自动对比
    """

    # 支持的编码格式列表
    ENCODINGS = ["UTF-8", "GBK", "GB2312", "GB18030", "Big5", "Latin-1"]

    # 自动对比防抖延迟（毫秒）
    AUTO_COMPARE_DELAY = 500

    # 文本长度限制
    MAX_LINES = 10000
    MAX_CHARS = 1000000

    def __init__(self, root):
        """
        初始化文本对比工具

        Args:
            root: tkinter根窗口对象
        """
        self.root = root
        self.root.title("文本对比工具 v1.0.2")
        self.root.geometry("1200x850")
        self.root.minsize(800, 650)

        # 防抖计时器
        self.compare_timer = None
        # 是否暂停自动对比
        self.auto_compare_paused = False

        self.setup_styles()
        self.create_widgets()
        self.setup_layout()
        self.bind_text_changes()

    def setup_styles(self):
        """
        配置差异高亮的颜色方案
        使用十六进制颜色码定义四种状态的颜色
        """
        self.colors = {
            "delete": "#FFB6C1",
            "insert": "#90EE90",
            "replace": "#FFFACD",
            "equal": "#FFFFFF",
        }

    def create_widgets(self):
        """
        创建所有界面组件
        包括主框架、文本输入框、滚动条、按钮、编码选择框和状态栏等
        """
        self.main_frame = ttk.Frame(self.root, padding="10")

        self.left_frame = ttk.LabelFrame(self.main_frame, text=" 左侧文本 ", padding="5")
        self.right_frame = ttk.LabelFrame(self.main_frame, text=" 右侧文本 ", padding="5")

        self.left_text = tk.Text(
            self.left_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            undo=True,
            maxundo=-1,
            padx=5,
            pady=5,
        )
        self.right_text = tk.Text(
            self.right_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            undo=True,
            maxundo=-1,
            padx=5,
            pady=5,
        )

        self.left_scroll = ttk.Scrollbar(self.left_frame, command=self.left_text.yview)
        self.right_scroll = ttk.Scrollbar(self.right_frame, command=self.right_text.yview)

        self.left_text.config(yscrollcommand=self.sync_scroll_left)
        self.right_text.config(yscrollcommand=self.sync_scroll_right)

        # 编码选择框
        self.left_encoding_var = tk.StringVar(value="UTF-8")
        self.right_encoding_var = tk.StringVar(value="UTF-8")

        self.left_encoding_combo = ttk.Combobox(
            self.main_frame,
            textvariable=self.left_encoding_var,
            values=self.ENCODINGS,
            state="readonly",
            width=10,
        )
        self.right_encoding_combo = ttk.Combobox(
            self.main_frame,
            textvariable=self.right_encoding_var,
            values=self.ENCODINGS,
            state="readonly",
            width=10,
        )

        # 绑定编码切换事件
        self.left_encoding_combo.bind("<<ComboboxSelected>>", self.on_left_encoding_changed)
        self.right_encoding_combo.bind("<<ComboboxSelected>>", self.on_right_encoding_changed)

        # 按钮容器框架
        self.btn_frame = ttk.Frame(self.main_frame)

        self.load_left_btn = ttk.Button(
            self.btn_frame, text="导入左侧", command=lambda: self.load_file("left")
        )
        self.load_right_btn = ttk.Button(
            self.btn_frame, text="导入右侧", command=lambda: self.load_file("right")
        )
        self.compare_btn = ttk.Button(
            self.btn_frame, text="  对  比  ", command=self.manual_compare
        )
        self.swap_btn = ttk.Button(
            self.btn_frame, text="  交  换  ", command=self.swap_texts
        )
        self.clear_content_btn = ttk.Button(
            self.btn_frame, text="  清  空  ", command=self.clear_content_only
        )

        self.status_frame = ttk.LabelFrame(self.main_frame, text=" 对比结果统计 ", padding="5")
        self.status_label = ttk.Label(
            self.status_frame,
            text="准备就绪，请输入文本后自动对比",
            font=("Microsoft YaHei", 10),
        )

        self.legend_frame = ttk.Frame(self.status_frame)
        self.legend_delete = tk.Label(
            self.legend_frame, text="  删除  ", bg=self.colors["delete"], relief="flat"
        )
        self.legend_insert = tk.Label(
            self.legend_frame, text="  新增  ", bg=self.colors["insert"], relief="flat"
        )
        self.legend_replace = tk.Label(
            self.legend_frame, text="  修改  ", bg=self.colors["replace"], relief="flat"
        )
        self.legend_equal = tk.Label(
            self.legend_frame, text="  相同  ", bg=self.colors["equal"], relief="flat"
        )

    def setup_layout(self):
        """
        设置界面组件的布局
        使用grid布局管理器，将组件排列在正确的位置
        """
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

        # 按钮栏放在第0行（顶部），跨2列，左对齐，按钮间距统一为5
        self.btn_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.load_left_btn.pack(side=tk.LEFT, padx=5)
        self.load_right_btn.pack(side=tk.LEFT, padx=5)
        self.compare_btn.pack(side=tk.LEFT, padx=5)
        self.swap_btn.pack(side=tk.LEFT, padx=5)
        self.clear_content_btn.pack(side=tk.LEFT, padx=5)

        # 左侧文本框区域放在第1行第0列
        # 左右文本框区域放在第1行，设置统一的最小宽度和高度
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        self.left_frame.config(width=336, height=320)
        self.left_frame.grid_propagate(False)

        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        self.right_frame.config(width=336, height=320)
        self.right_frame.grid_propagate(False)

        self.left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.left_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 编码选择框放在第2行
        self.left_encoding_combo.grid(row=2, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.right_encoding_combo.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=(5, 0))

        # 状态栏放在第3行（底部），跨2列，水平填充
        self.status_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.legend_frame.pack(side=tk.RIGHT, padx=10)
        self.legend_delete.pack(side=tk.LEFT, padx=2)
        self.legend_insert.pack(side=tk.LEFT, padx=2)
        self.legend_replace.pack(side=tk.LEFT, padx=2)
        self.legend_equal.pack(side=tk.LEFT, padx=2)

    def bind_text_changes(self):
        """
        绑定文本框内容变化事件，实现自动对比
        使用 tkinter 的修改标志位来检测文本变化
        """
        # 绑定按键释放事件
        self.left_text.bind("<KeyRelease>", self.on_text_changed)
        self.right_text.bind("<KeyRelease>", self.on_text_changed)
        # 绑定鼠标释放事件（处理粘贴、删除等操作）
        self.left_text.bind("<ButtonRelease-1>", self.on_text_changed)
        self.right_text.bind("<ButtonRelease-1>", self.on_text_changed)
        # 绑定文本修改事件
        self.left_text.bind("<<Modified>>", self.on_modified)
        self.right_text.bind("<<Modified>>", self.on_modified)

    def on_modified(self, event=None):
        """
        处理文本修改事件
        tkinter 的 <<Modified>> 事件在文本内容发生修改时触发
        """
        widget = event.widget
        # 重置修改标志，否则事件不会再次触发
        if widget.edit_modified():
            widget.edit_modified(False)
            self.on_text_changed()

    def on_text_changed(self, event=None):
        """
        文本框内容变化时的回调
        启动防抖计时器，延迟后自动触发对比
        """
        # 取消已有的计时器
        if self.compare_timer is not None:
            self.root.after_cancel(self.compare_timer)

        # 检查是否需要暂停自动对比
        left_content = self.left_text.get("1.0", tk.END)
        right_content = self.right_text.get("1.0", tk.END)
        total_chars = len(left_content) + len(right_content)
        total_lines = left_content.count("\n") + right_content.count("\n")

        if total_chars > self.MAX_CHARS or total_lines > self.MAX_LINES:
            self.auto_compare_paused = True
            self.status_label.config(
                text="自动对比已暂停（文本过长）| 请手动点击对比按钮"
            )
            return

        if self.auto_compare_paused:
            self.auto_compare_paused = False

        # 启动新的防抖计时器
        self.compare_timer = self.root.after(self.AUTO_COMPARE_DELAY, self.auto_compare)

    def auto_compare(self):
        """
        自动执行对比
        在防抖延迟后调用
        """
        try:
            self.compare_texts()
        except MemoryError:
            self.auto_compare_paused = True
            self.status_label.config(
                text="自动对比已暂停（内存占用过大，请减少对比内容）"
            )
            messagebox.showwarning(
                "内存不足",
                "内存占用过大，请减少对比内容。"
            )
        except Exception as e:
            self.status_label.config(text=f"对比出错：{str(e)}")

    def manual_compare(self):
        """
        手动触发对比
        点击对比按钮时调用，无视防抖延迟
        """
        # 取消自动对比计时器
        if self.compare_timer is not None:
            self.root.after_cancel(self.compare_timer)
            self.compare_timer = None

        self.auto_compare_paused = False

        try:
            self.compare_texts()
        except MemoryError:
            self.status_label.config(
                text="自动对比已暂停（内存占用过大，请减少对比内容）"
            )
            messagebox.showwarning(
                "内存不足",
                "内存占用过大，请减少对比内容。"
            )
        except Exception as e:
            self.status_label.config(text=f"对比出错：{str(e)}")

    def sync_scroll_left(self, *args):
        """
        左侧滚动条同步回调
        当左侧文本框滚动时，同步滚动右侧文本框
        """
        self.left_scroll.set(*args)
        self.right_text.yview_moveto(args[0])

    def sync_scroll_right(self, *args):
        """
        右侧滚动条同步回调
        当右侧文本框滚动时，同步滚动左侧文本框
        """
        self.right_scroll.set(*args)
        self.left_text.yview_moveto(args[0])

    def clear_highlights(self):
        """
        清除所有高亮标记
        在重新对比前调用，确保不会叠加旧的标记
        """
        for tag in ["delete", "insert", "replace", "equal"]:
            self.left_text.tag_remove(tag, "1.0", tk.END)
            self.right_text.tag_remove(tag, "1.0", tk.END)

    def on_left_encoding_changed(self, event=None):
        """
        左侧编码选择框变化时的回调
        实时将当前文本按新编码重新解码显示
        """
        self.redecode_text("left")

    def on_right_encoding_changed(self, event=None):
        """
        右侧编码选择框变化时的回调
        实时将当前文本按新编码重新解码显示
        """
        self.redecode_text("right")

    def redecode_text(self, side):
        """
        使用新选择的编码重新解码文本框内容

        Args:
            side: "left" 或 "right"
        """
        if side == "left":
            text_widget = self.left_text
            old_encoding = self.left_encoding_var.get()
        else:
            text_widget = self.right_text
            old_encoding = self.right_encoding_var.get()

        content = text_widget.get("1.0", tk.END).rstrip("\n")
        if not content:
            return

        try:
            bytes_data = content.encode("latin-1", errors="replace")
            new_content = bytes_data.decode(old_encoding, errors="replace")

            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", new_content)
        except (UnicodeDecodeError, UnicodeEncodeError) as e:
            messagebox.showwarning("转码警告", f"编码转换失败：{str(e)}\n已保留原内容。")

    def detect_encoding(self, file_path):
        """
        使用chardet自动检测文件编码

        Args:
            file_path: 文件路径

        Returns:
            检测到的编码名称，如果检测失败返回"UTF-8"
        """
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read()
            result = chardet.detect(raw_data)
            detected = result.get("encoding", "UTF-8")
            confidence = result.get("confidence", 0)

            if detected and confidence > 0.5:
                detected_upper = detected.upper()
                for enc in self.ENCODINGS:
                    if enc.upper() == detected_upper:
                        return enc
                return "UTF-8"
            return "UTF-8"
        except Exception:
            return "UTF-8"

    def compare_texts(self):
        """
        执行文本对比的核心方法
        使用difflib.SequenceMatcher算法逐行对比，并用颜色标记差异
        """
        self.clear_highlights()

        left_content = self.left_text.get("1.0", tk.END).rstrip("\n")
        right_content = self.right_text.get("1.0", tk.END).rstrip("\n")

        left_lines = left_content.split("\n") if left_content else []
        right_lines = right_content.split("\n") if right_content else []

        if not left_lines and not right_lines:
            self.status_label.config(text="请输入文本，自动对比将在 500 毫秒后触发...")
            return

        sm = difflib.SequenceMatcher(None, left_lines, right_lines)
        opcodes = sm.get_opcodes()

        self.left_text.delete("1.0", tk.END)
        self.right_text.delete("1.0", tk.END)

        stats = {"equal": 0, "delete": 0, "insert": 0, "replace": 0}

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                for line in left_lines[i1:i2]:
                    self.left_text.insert(tk.END, line + "\n", "equal")
                    stats["equal"] += 1
                for line in right_lines[j1:j2]:
                    self.right_text.insert(tk.END, line + "\n", "equal")

            elif tag == "delete":
                for line in left_lines[i1:i2]:
                    self.left_text.insert(tk.END, line + "\n", "delete")
                    stats["delete"] += 1

            elif tag == "insert":
                for line in right_lines[j1:j2]:
                    self.right_text.insert(tk.END, line + "\n", "insert")
                    stats["insert"] += 1

            elif tag == "replace":
                max_lines = max(i2 - i1, j2 - j1)
                for idx in range(max_lines):
                    if idx < (i2 - i1):
                        self.left_text.insert(tk.END, left_lines[i1 + idx] + "\n", "replace")
                        stats["replace"] += 1
                    else:
                        self.left_text.insert(tk.END, "\n", "replace")

                    if idx < (j2 - j1):
                        self.right_text.insert(tk.END, right_lines[j1 + idx] + "\n", "replace")
                    else:
                        self.right_text.insert(tk.END, "\n", "replace")

        self.configure_tags()

        total_diff = stats["delete"] + stats["insert"] + stats["replace"]
        status_text = (
            f"相同: {stats['equal']} 行 | "
            f"修改: {stats['replace']} 行 | "
            f"删除: {stats['delete']} 行 | "
            f"新增: {stats['insert']} 行 | "
            f"差异总计: {total_diff} 行"
        )
        self.status_label.config(text=status_text)

    def configure_tags(self):
        """
        配置文本标记的颜色样式
        为四种差异类型设置对应的背景色
        """
        self.left_text.tag_config("delete", background=self.colors["delete"])
        self.left_text.tag_config("insert", background=self.colors["insert"])
        self.left_text.tag_config("replace", background=self.colors["replace"])
        self.left_text.tag_config("equal", background=self.colors["equal"])

        self.right_text.tag_config("delete", background=self.colors["delete"])
        self.right_text.tag_config("insert", background=self.colors["insert"])
        self.right_text.tag_config("replace", background=self.colors["replace"])
        self.right_text.tag_config("equal", background=self.colors["equal"])

    def swap_texts(self):
        """
        交换左右两侧文本框的内容和编码格式
        """
        left_content = self.left_text.get("1.0", tk.END)
        right_content = self.right_text.get("1.0", tk.END)
        left_encoding = self.left_encoding_var.get()
        right_encoding = self.right_encoding_var.get()

        self.left_text.delete("1.0", tk.END)
        self.right_text.delete("1.0", tk.END)

        self.left_text.insert("1.0", right_content)
        self.right_text.insert("1.0", left_content)

        self.left_encoding_var.set(right_encoding)
        self.right_encoding_var.set(left_encoding)

        # 交换后触发自动对比
        self.on_text_changed()

    def clear_content_only(self):
        """
        仅清空左右文本框的内容，不清除高亮标记，不改变编码选择
        """
        self.left_text.delete("1.0", tk.END)
        self.right_text.delete("1.0", tk.END)
        self.status_label.config(text="内容已清空，请输入文本后自动对比...")

    def clear_texts(self):
        """
        清除所有文本内容和高亮标记
        将界面恢复到初始状态
        """
        self.left_text.delete("1.0", tk.END)
        self.right_text.delete("1.0", tk.END)
        self.clear_highlights()
        self.status_label.config(text="准备就绪，请输入文本后自动对比...")

    def load_file(self, side):
        """
        从文件加载文本到指定侧的文本框
        自动检测文件编码并设置编码选择框

        Args:
            side: 字符串，"left"表示左侧，"right"表示右侧
        """
        file_path = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if file_path:
            try:
                # 自动检测文件编码
                detected_encoding = self.detect_encoding(file_path)

                # 使用检测到的编码读取文件
                with open(file_path, "r", encoding=detected_encoding) as f:
                    content = f.read()

                if side == "left":
                    self.left_text.delete("1.0", tk.END)
                    self.left_text.insert("1.0", content)
                    self.left_encoding_var.set(detected_encoding)
                else:
                    self.right_text.delete("1.0", tk.END)
                    self.right_text.insert("1.0", content)
                    self.right_encoding_var.set(detected_encoding)

                # 导入后触发自动对比
                self.on_text_changed()

            except (IOError, OSError, UnicodeDecodeError) as e:
                messagebox.showerror("错误", f"读取文件失败:\n{str(e)}")


def main():
    """
    程序入口函数
    创建主窗口并启动事件循环
    """
    root = tk.Tk()
    app = TextDiffTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
