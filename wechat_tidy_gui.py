import re
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

def parse_wechat_log(file_path, output_path=None):
    """
    解析微信导出的聊天记录（三行一组：发送者/时间/内容），
    去除分块标记、去重、按时间排序。
    """
    time_pattern = re.compile(r'^(\d{4}年\d{2}月\d{2}日\s+\d{1,2}:\d{2})$')

    def parse_time(timestamp_str):
        clean = re.sub(r'\s+', ' ', timestamp_str.strip())
        clean = clean.replace('年', '-').replace('月', '-').replace('日', '')
        return datetime.strptime(clean, '%Y-%m-%d %H:%M')

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f if line.strip()]

    records = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('----------【'):
            i += 1
            continue

        if time_pattern.match(line):
            if i - 1 < 0 or i + 1 >= len(lines):
                i += 1
                continue
            sender = lines[i - 1].strip()
            content = lines[i + 1].strip()
            full_line = f"{sender} {line} {content}"
            if full_line not in {r['line'] for r in records}:
                try:
                    dt = parse_time(line)
                    records.append({
                        'line': full_line,
                        'dt': dt,
                        'timestamp': line,
                        'sender': sender,
                        'content': content
                    })
                except Exception:
                    pass
            i += 3
        else:
            i += 1

    records.sort(key=lambda x: x['dt'])

    if output_path is None:
        base = Path(file_path).stem
        output_path = f"{base}_tidy.txt"

    with open(output_path, 'w', encoding='utf-8') as f:
        for rec in records:
            f.write(rec['line'] + '\n')

    return output_path, len(records)

class TidyApp:
    def __init__(self, root):
        self.root = root
        root.title("微信聊天记录整理工具")
        root.geometry("650x420")
        root.resizable(False, False)

        # 文件选择区域
        tk.Label(root, text="选择或输入要整理的原始聊天文件：", font=('Arial', 10, 'bold')).pack(pady=10)

        # 提示用户可以不输入 .txt 后缀
        tk.Label(root, text="💡 可以直接输入文件名（无需输入 .txt 后缀）", fg='blue', font=('Arial', 9)).pack()

        frame = tk.Frame(root)
        frame.pack(pady=5)

        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(frame, textvariable=self.file_path_var, width=50)
        self.file_entry.pack(side=tk.LEFT, padx=5)

        self.browse_btn = tk.Button(frame, text="浏览", command=self.browse_file)
        self.browse_btn.pack(side=tk.LEFT)

        # 整理按钮
        self.process_btn = tk.Button(root, text="开始整理", command=self.process, bg='lightgreen', font=('Arial', 12, 'bold'))
        self.process_btn.pack(pady=10)

        # 日志区域
        self.log_text = scrolledtext.ScrolledText(root, height=15, state='disabled')
        self.log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 底部提示
        tk.Label(root, text="整理后文件保存在原文件同目录，文件名添加 _tidy 后缀", fg='gray', font=('Arial', 9)).pack()

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="选择原始聊天文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.log_message(f"已选择文件：{file_path}")

    def log_message(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()

    def process(self):
        raw_input = self.file_path_var.get().strip()
        if not raw_input:
            messagebox.showwarning("提示", "请先选择或输入要整理的原始文件！")
            return

        # ====== 关键改动：补全 .txt 后缀 ======
        file_path = raw_input
        # 如果输入内容不包含扩展名（即没有点号，或点号在路径分隔符后但无扩展名），则添加 .txt
        # 更稳妥：使用 Path 判断后缀
        p = Path(file_path)
        if p.suffix.lower() != '.txt':
            # 没有 .txt 后缀，自动补全
            file_path = str(p) + '.txt'
            # 但如果用户原本输入的是目录（比如 D:/chat/），则补全后可能不合法，但这会在后面检查时发现

        # 如果文件不存在，尝试在当前目录查找（如果用户只输入了文件名）
        if not Path(file_path).exists():
            # 尝试在当前工作目录下查找
            current_dir = Path.cwd()
            candidate = current_dir / file_path
            if candidate.exists():
                file_path = str(candidate)
            else:
                # 如果还是找不到，报错
                messagebox.showerror("错误", f"文件不存在：{file_path}\n请检查文件是否位于程序所在目录或输入完整路径。")
                return

        self.process_btn.config(state='disabled')
        self.log_message(f"开始整理文件：{file_path}")

        try:
            output_path, count = parse_wechat_log(file_path)
            self.log_message(f"✅ 整理完成！共保留 {count} 条消息")
            self.log_message(f"输出文件：{output_path}")
            messagebox.showinfo("完成", f"整理完成！\n输出文件：{output_path}\n共保留 {count} 条消息。")
        except Exception as e:
            error_msg = f"❌ 整理失败：{str(e)}"
            self.log_message(error_msg)
            messagebox.showerror("错误", error_msg)
        finally:
            self.process_btn.config(state='normal')

def main():
    root = tk.Tk()
    app = TidyApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()