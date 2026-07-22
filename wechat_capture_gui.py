import pyautogui
import pyperclip
import time
import ctypes
from datetime import datetime
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# ========== 全局停止标志 ==========
stop_flag = False
user3 = ctypes.WinDLL("user32", use_last_error=True)
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_BACK = 0x08

def global_key_listener():
    global stop_flag
    while not stop_flag:
        left_ctrl = (user3.GetAsyncKeyState(VK_LCONTROL) & 0x8000) != 0
        right_ctrl = (user3.GetAsyncKeyState(VK_RCONTROL) & 0x8000) != 0
        backspace = (user3.GetAsyncKeyState(VK_BACK) & 0x8000) != 0
        if (left_ctrl or right_ctrl) and backspace:
            stop_flag = True
            print("\n🛑 【Ctrl + Backspace】全局停止热键触发,程序即将终止！")
            break
        time.sleep(0.02)

def get_clip_text():
    return pyperclip.paste().strip()

def capture_one_round(round_num, params):
    global stop_flag
    if stop_flag:
        return None

    START_X, START_Y = params['start_x'], params['start_y']
    END_X, END_Y = params['end_x'], params['end_y']
    DRAG_DURATION = params['drag_duration']
    MOVE_START_DURATION = params['move_start_duration']
    WAIT_AFTER_DRAG = params['wait_after_drag']
    COPY_BTN_X, COPY_BTN_Y = params['copy_btn_x'], params['copy_btn_y']
    WAIT_AFTER_COPY = params['wait_after_copy']

    pyautogui.moveTo(START_X, START_Y, duration=MOVE_START_DURATION)
    time.sleep(0.1)
    if stop_flag:
        return None

    pyautogui.mouseDown()
    pyautogui.moveTo(END_X, END_Y, duration=DRAG_DURATION)
    time.sleep(WAIT_AFTER_DRAG)
    pyautogui.mouseUp()

    if stop_flag:
        return None

    pyautogui.click(COPY_BTN_X, COPY_BTN_Y)
    time.sleep(WAIT_AFTER_COPY)
    if stop_flag:
        return None

    content = get_clip_text()
    if not content:
        print(f"【第{round_num}轮】无消息，跳过本轮")
        return ""

    block = f"\n----------【第{round_num}轮消息块】----------\n{content}"
    print(f"【第{round_num}轮】抓取完成，行数：{len(content.splitlines())}")
    return block

def run_capture(params, log_callback, finish_callback):
    global stop_flag
    stop_flag = False
    now = datetime.now()
    SAVE_FILE = f"wechat_{now.strftime('%Y%m%d_%H%M%S')}.txt"

    # 启动后台按键监听
    listener_thread = threading.Thread(target=global_key_listener, daemon=True)
    listener_thread.start()

    round_count = 1
    while True:
        if stop_flag:
            break
        block_data = capture_one_round(round_count, params)
        if stop_flag:
            break
        if block_data:
            with open(SAVE_FILE, "a", encoding="utf-8") as f:
                f.write(block_data)
        # 滚动
        pyautogui.scroll(params['scroll_step'])
        time.sleep(params['wait_after_scroll'])
        round_count += 1

    log_callback(f"\n✅ 抓取任务结束！保存文件：{os.path.abspath(SAVE_FILE)}")
    finish_callback()

def start_gui():
    root = tk.Tk()
    root.title("微信聊天抓取工具 - 参数设置")
    root.geometry("500x620")
    root.resizable(False, False)

    # 默认参数
    defaults = {
        'start_x': 315, 'start_y': 930,
        'end_x': 1000, 'end_y': 55,
        'copy_btn_x': 1055, 'copy_btn_y': 1000,
        'drag_duration': 1.8,
        'move_start_duration': 0.5,
        'wait_after_drag': 3.0,
        'wait_after_copy': 1.5,
        'wait_after_scroll': 3.5,
        'scroll_step': 900
    }

    # 变量
    vars_dict = {}
    for key, val in defaults.items():
        vars_dict[key] = tk.DoubleVar(value=val) if isinstance(val, float) else tk.IntVar(value=val)

    # 创建输入行
    row = 0
    tk.Label(root, text="请根据你的屏幕和微信窗口位置调整以下参数：", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, pady=10)
    row += 1

    labels = [
        ("拖拽起点 X", "start_x"), ("拖拽起点 Y", "start_y"),
        ("拖拽终点 X", "end_x"), ("拖拽终点 Y", "end_y"),
        ("复制按钮 X", "copy_btn_x"), ("复制按钮 Y", "copy_btn_y"),
        ("拖拽耗时(秒)", "drag_duration"), ("移动耗时(秒)", "move_start_duration"),
        ("拖拽后等待(秒)", "wait_after_drag"), ("复制后等待(秒)", "wait_after_copy"),
        ("滚动后等待(秒)", "wait_after_scroll"), ("每次滚动像素", "scroll_step")
    ]

    for label_text, key in labels:
        tk.Label(root, text=label_text + ":").grid(row=row, column=0, sticky='e', padx=5, pady=3)
        entry = tk.Entry(root, textvariable=vars_dict[key], width=12)
        entry.grid(row=row, column=1, sticky='w', padx=5, pady=3)
        row += 1

    # 日志显示区域
    log_text = tk.Text(root, height=10, width=60, state='disabled')
    log_text.grid(row=row, column=0, columnspan=2, padx=10, pady=10)

    def log_message(msg):
        log_text.config(state='normal')
        log_text.insert(tk.END, msg + "\n")
        log_text.see(tk.END)
        log_text.config(state='disabled')
        root.update()

    def on_finish():
        start_btn.config(state='normal')

    def on_start():
        # 禁用开始按钮，避免重复点击
        start_btn.config(state='disabled')
        # 倒计时 5 秒
        countdown = 5
        log_message("⏳ 准备开始抓取，请将鼠标移至微信聊天窗口...")
        log_message(f"⏳ 倒计时 {countdown} 秒...")

        def countdown_step(remaining):
            if remaining > 0:
                log_message(f"⏳ 剩余 {remaining} 秒...")
                root.after(1000, countdown_step, remaining - 1)
            else:
                log_message("⏳ 倒计时结束,开始执行抓取!同时按CTRL+backspace结束执行")
                # 收集参数
                params = {key: vars_dict[key].get() for key in defaults}
                # 启动抓取线程
                threading.Thread(target=run_capture, args=(params, log_message, on_finish), daemon=True).start()

        # 开始倒计时
        countdown_step(countdown)

    start_btn = tk.Button(root, text="开始抓取", command=on_start, bg='lightblue', font=('Arial', 12, 'bold'))
    start_btn.grid(row=row+1, column=0, columnspan=2, pady=10)

    # 底部提示
    tk.Label(root, text="🛑 全局停止热键:Ctrl + Backspace(任意窗口）", fg='red').grid(row=row+2, column=0, columnspan=2, pady=5)

    root.mainloop()

if __name__ == "__main__":
    pyautogui.FAILSAFE = False
    start_gui()