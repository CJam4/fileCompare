import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import difflib


class TextDiffTool:
    """
    文本对比工具主类
    提供图形化界面，支持左右两侧文本的输入、对比和高亮显示差异
    """

    def __init__(self, root):
        """
        初始化文本对比工具

        Args:
            root: tkinter根窗口对象
        """
        self.root = root
        # 设置窗口标题
        self.root.title("文本对比工具 v1.0")
        # 设置窗口初始大小为1200x800像素
        self.root.geometry("1200x800")
        # 设置窗口最小尺寸，防止用户缩放过小导致界面混乱
        self.root.minsize(800, 600)

        # 依次调用初始化方法：样式配置 -> 创建组件 -> 布局设置
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()

    def setup_styles(self):
        """
        配置差异高亮的颜色方案
        使用十六进制颜色码定义四种状态的颜色
        """
        self.colors = {
            "delete": "#FFB6C1",   # 浅红色：表示左侧有但右侧没有的内容（删除）
            "insert": "#90EE90",   # 浅绿色：表示右侧有但左侧没有的内容（新增）
            "replace": "#FFFACD",  # 浅黄色：表示两侧都有但内容不同的行（修改）
            "equal": "#FFFFFF",    # 白色：表示两侧完全相同的内容
        }

    def create_widgets(self):
        """
        创建所有界面组件
        包括主框架、文本输入框、滚动条、按钮和状态栏等
        """
        # 主容器框架，padding="10"表示四周留出10像素的内边距
        self.main_frame = ttk.Frame(self.root, padding="10")

        # 左侧文本输入区域，使用LabelFrame带标题边框
        self.left_frame = ttk.LabelFrame(self.main_frame, text=" 左侧文本 ", padding="5")
        # 右侧文本输入区域
        self.right_frame = ttk.LabelFrame(self.main_frame, text=" 右侧文本 ", padding="5")

        # 左侧多行文本输入框
        self.left_text = tk.Text(
            self.left_frame,
            wrap=tk.WORD,           # 按单词自动换行
            font=("Consolas", 11),  # 使用等宽字体，便于对齐
            undo=True,              # 启用撤销功能
            maxundo=-1,             # 撤销次数无限制
            padx=5,                 # 水平内边距
            pady=5,                 # 垂直内边距
        )
        # 右侧多行文本输入框，配置与左侧相同
        self.right_text = tk.Text(
            self.right_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            undo=True,
            maxundo=-1,
            padx=5,
            pady=5,
        )

        # 左侧滚动条，与左侧文本框关联
        self.left_scroll = ttk.Scrollbar(self.left_frame, command=self.left_text.yview)
        # 右侧滚动条，与右侧文本框关联
        self.right_scroll = ttk.Scrollbar(self.right_frame, command=self.right_text.yview)

        # 配置文本框的滚动回调，实现双滚动条同步
        self.left_text.config(yscrollcommand=self.sync_scroll_left)
        self.right_text.config(yscrollcommand=self.sync_scroll_right)

        # 按钮容器框架
        self.btn_frame = ttk.Frame(self.main_frame)

        # 对比按钮：点击后执行文本对比
        self.compare_btn = ttk.Button(
            self.btn_frame, text="  对  比  ", command=self.compare_texts
        )
        # 清除按钮：点击后清空所有内容
        self.clear_btn = ttk.Button(
            self.btn_frame, text="  清  除  ", command=self.clear_texts
        )
        # 导入左侧按钮：点击后弹出文件选择对话框，读取文件到左侧文本框
        self.load_left_btn = ttk.Button(
            self.btn_frame, text="导入左侧", command=lambda: self.load_file("left")
        )
        # 导入右侧按钮：点击后弹出文件选择对话框，读取文件到右侧文本框
        self.load_right_btn = ttk.Button(
            self.btn_frame, text="导入右侧", command=lambda: self.load_file("right")
        )

        # 状态栏容器，使用LabelFrame带标题边框
        self.status_frame = ttk.LabelFrame(self.main_frame, text=" 对比结果统计 ", padding="5")
        # 状态标签，用于显示对比统计信息
        self.status_label = ttk.Label(
            self.status_frame,
            text="准备就绪，请输入文本后点击对比",
            font=("Microsoft YaHei", 10),
        )

        # 图例说明容器，用于显示颜色对应的含义
        self.legend_frame = ttk.Frame(self.status_frame)
        # 删除图例（浅红色背景）
        self.legend_delete = tk.Label(
            self.legend_frame, text="  删除  ", bg=self.colors["delete"], relief="solid", bd=1
        )
        # 新增图例（浅绿色背景）
        self.legend_insert = tk.Label(
            self.legend_frame, text="  新增  ", bg=self.colors["insert"], relief="solid", bd=1
        )
        # 修改图例（浅黄色背景）
        self.legend_replace = tk.Label(
            self.legend_frame, text="  修改  ", bg=self.colors["replace"], relief="solid", bd=1
        )
        # 相同图例（白色背景）
        self.legend_equal = tk.Label(
            self.legend_frame, text="  相同  ", bg=self.colors["equal"], relief="solid", bd=1
        )

    def setup_layout(self):
        """
        设置界面组件的布局
        使用grid布局管理器，将组件排列在正确的位置
        """
        # 主框架填充整个窗口
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 配置grid布局的列权重，使两列等宽且可伸缩
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        # 配置第1行（文本框区域）可垂直伸缩
        self.main_frame.rowconfigure(1, weight=1)

        # 按钮栏放在第0行（顶部），跨2列，左对齐
        self.btn_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.load_left_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.load_right_btn.pack(side=tk.LEFT, padx=5)
        self.compare_btn.pack(side=tk.LEFT, padx=(20, 5))
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # 左侧文本框区域放在第1行第0列
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        # 右侧文本框区域放在第1行第1列
        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))

        # 左侧滚动条靠右填充，文本框靠左填充并扩展
        self.left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.left_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 右侧滚动条靠右填充，文本框靠左填充并扩展
        self.right_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 状态栏放在第2行（底部），跨2列，水平填充
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.status_label.pack(side=tk.LEFT, padx=10)

        # 图例靠右排列
        self.legend_frame.pack(side=tk.RIGHT, padx=10)
        self.legend_delete.pack(side=tk.LEFT, padx=2)
        self.legend_insert.pack(side=tk.LEFT, padx=2)
        self.legend_replace.pack(side=tk.LEFT, padx=2)
        self.legend_equal.pack(side=tk.LEFT, padx=2)

    def sync_scroll_left(self, *args):
        """
        左侧滚动条同步回调
        当左侧文本框滚动时，同步滚动右侧文本框

        Args:
            *args: 滚动位置参数 (first, last)
        """
        # 更新左侧滚动条位置
        self.left_scroll.set(*args)
        # 将右侧文本框滚动到相同位置
        self.right_text.yview_moveto(args[0])

    def sync_scroll_right(self, *args):
        """
        右侧滚动条同步回调
        当右侧文本框滚动时，同步滚动左侧文本框

        Args:
            *args: 滚动位置参数 (first, last)
        """
        # 更新右侧滚动条位置
        self.right_scroll.set(*args)
        # 将左侧文本框滚动到相同位置
        self.left_text.yview_moveto(args[0])

    def clear_highlights(self):
        """
        清除所有高亮标记
        在重新对比前调用，确保不会叠加旧的标记
        """
        # 遍历所有标记类型，从文本框中移除
        for tag in ["delete", "insert", "replace", "equal"]:
            self.left_text.tag_remove(tag, "1.0", tk.END)
            self.right_text.tag_remove(tag, "1.0", tk.END)

    def compare_texts(self):
        """
        执行文本对比的核心方法
        使用difflib.SequenceMatcher算法逐行对比，并用颜色标记差异
        """
        # 清除之前的高亮标记
        self.clear_highlights()

        # 获取左侧文本内容，去除末尾换行符
        left_content = self.left_text.get("1.0", tk.END).rstrip("\n")
        # 获取右侧文本内容，去除末尾换行符
        right_content = self.right_text.get("1.0", tk.END).rstrip("\n")

        # 将文本按行分割为列表，空文本则使用空列表
        left_lines = left_content.split("\n") if left_content else []
        right_lines = right_content.split("\n") if right_content else []

        # 如果两侧都为空，提示用户输入内容
        if not left_lines and not right_lines:
            messagebox.showinfo("提示", "两侧文本均为空，请输入内容后再对比")
            return

        # 创建序列匹配器，对比两个文本行列表
        sm = difflib.SequenceMatcher(None, left_lines, right_lines)
        # 获取操作码列表，描述如何将左侧转换为右侧
        opcodes = sm.get_opcodes()

        # 清空两侧文本框，准备重新填入带标记的内容
        self.left_text.delete("1.0", tk.END)
        self.right_text.delete("1.0", tk.END)

        # 初始化统计字典，记录各类差异的数量
        stats = {"equal": 0, "delete": 0, "insert": 0, "replace": 0}

        # 遍历所有操作码，处理每一种差异类型
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                # equal: 两侧内容相同，使用白色背景
                for line in left_lines[i1:i2]:
                    self.left_text.insert(tk.END, line + "\n", "equal")
                    stats["equal"] += 1
                for line in right_lines[j1:j2]:
                    self.right_text.insert(tk.END, line + "\n", "equal")

            elif tag == "delete":
                # delete: 仅左侧有，右侧没有，使用浅红色背景（删除）
                for line in left_lines[i1:i2]:
                    self.left_text.insert(tk.END, line + "\n", "delete")
                    stats["delete"] += 1

            elif tag == "insert":
                # insert: 仅右侧有，左侧没有，使用浅绿色背景（新增）
                for line in right_lines[j1:j2]:
                    self.right_text.insert(tk.END, line + "\n", "insert")
                    stats["insert"] += 1

            elif tag == "replace":
                # replace: 两侧都有但内容不同，使用浅黄色背景（修改）
                # 取两侧行数的最大值，确保两侧行数对齐
                max_lines = max(i2 - i1, j2 - j1)
                for idx in range(max_lines):
                    # 处理左侧行，如果超出范围则插入空行占位
                    if idx < (i2 - i1):
                        self.left_text.insert(tk.END, left_lines[i1 + idx] + "\n", "replace")
                        stats["replace"] += 1
                    else:
                        self.left_text.insert(tk.END, "\n", "replace")

                    # 处理右侧行，如果超出范围则插入空行占位
                    if idx < (j2 - j1):
                        self.right_text.insert(tk.END, right_lines[j1 + idx] + "\n", "replace")
                    else:
                        self.right_text.insert(tk.END, "\n", "replace")

        # 配置所有标记的颜色样式
        self.configure_tags()

        # 计算差异总行数
        total_diff = stats["delete"] + stats["insert"] + stats["replace"]
        # 生成状态栏文本
        status_text = (
            f"相同: {stats['equal']} 行 | "
            f"修改: {stats['replace']} 行 | "
            f"删除: {stats['delete']} 行 | "
            f"新增: {stats['insert']} 行 | "
            f"差异总计: {total_diff} 行"
        )
        # 更新状态栏显示
        self.status_label.config(text=status_text)

    def configure_tags(self):
        """
        配置文本标记的颜色样式
        为四种差异类型设置对应的背景色
        """
        # 配置左侧文本框的标记颜色
        self.left_text.tag_config("delete", background=self.colors["delete"])
        self.left_text.tag_config("insert", background=self.colors["insert"])
        self.left_text.tag_config("replace", background=self.colors["replace"])
        self.left_text.tag_config("equal", background=self.colors["equal"])

        # 配置右侧文本框的标记颜色
        self.right_text.tag_config("delete", background=self.colors["delete"])
        self.right_text.tag_config("insert", background=self.colors["insert"])
        self.right_text.tag_config("replace", background=self.colors["replace"])
        self.right_text.tag_config("equal", background=self.colors["equal"])

    def clear_texts(self):
        """
        清除所有文本内容和高亮标记
        将界面恢复到初始状态
        """
        # 清空左侧文本框
        self.left_text.delete("1.0", tk.END)
        # 清空右侧文本框
        self.right_text.delete("1.0", tk.END)
        # 清除高亮标记
        self.clear_highlights()
        # 重置状态栏文本
        self.status_label.config(text="准备就绪，请输入文本后点击对比")

    def load_file(self, side):
        """
        从文件加载文本到指定侧的文本框

        Args:
            side: 字符串，"left"表示左侧，"right"表示右侧
        """
        # 弹出文件选择对话框
        file_path = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if file_path:
            try:
                # 以UTF-8编码读取文件内容
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # 根据side参数决定写入左侧还是右侧
                if side == "left":
                    self.left_text.delete("1.0", tk.END)
                    self.left_text.insert("1.0", content)
                else:
                    self.right_text.delete("1.0", tk.END)
                    self.right_text.insert("1.0", content)
            except (IOError, OSError, UnicodeDecodeError) as e:
                # 读取失败时显示错误对话框
                messagebox.showerror("错误", f"读取文件失败:\n{str(e)}")


def main():
    """
    程序入口函数
    创建主窗口并启动事件循环
    """
    # 创建tkinter根窗口
    root = tk.Tk()
    # 创建文本对比工具实例
    app = TextDiffTool(root)
    # 进入主事件循环，等待用户交互
    root.mainloop()


# 当脚本直接运行时执行main函数
if __name__ == "__main__":
    main()
