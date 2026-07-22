import pyautogui
import pyperclip
import time
import ctypes
from datetime import datetime
import os
import threading

# ========== 启动5秒倒计时，预留手动调整窗口纠错时间 ==========
print("脚本即将启动，倒计时 5 秒，可调整页面/终止程序纠错！")
# 5 4 3 2 1 完整倒计时
for i in range(5, 0, -1):
    print(f"剩余 {i} 秒")
    time.sleep(1)
print("倒计时结束，开始执行鼠标操作！")

# ========== 全套抓取参数（单行注释，优化防重复、防漏消息） ==========
# 拖拽起点X像素坐标
START_X = 315
# 拖拽起点Y像素坐标
START_Y = 930
# 拖拽终点X像素坐标
END_X = 1000
# 拖拽终点Y像素坐标，数值越小选区越高，框住更多底部消息
END_Y = 55
# 拖拽滑动全程持续时长，放缓滑动避免界面跳帧漏内容
DRAG_DURATION = 1.8
# 拖拽动作启动前鼠标移动耗时
MOVE_START_DURATION = 0.5
# 拖拽完成后停留等待，等待选中聊天完整渲染
WAIT_AFTER_DRAG = 3
# 复制按钮横坐标像素
COPY_BTN_X = 1055
# 复制按钮纵坐标像素
COPY_BTN_Y = 1000
# 点击复制后等待文本完整加载读取
WAIT_AFTER_COPY = 1.5
# 保存文件完成后缓冲等待
WAIT_AFTER_SAVE = 1.5
# 单次滚动距离放大，减少两轮聊天重叠，解决大量重复内容
SCROLL_STEP = 900
# 新增关键参数：滚动结束后等待微信加载完整历史消息，杜绝断层漏消息
WAIT_AFTER_SCROLL = 3.5

# =================================================================
# Windows 全局按键监听配置（Ctrl + Backspace 任意窗口停止）
# =================================================================
user3 = ctypes.WinDLL("user32", use_last_error=True)
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_BACK = 0x08
stop_flag = False

def global_key_listener():
    """后台独立线程实时监听全局停止快捷键 Ctrl + Backspace"""
    global stop_flag
    while not stop_flag:
        left_ctrl = (user3.GetAsyncKeyState(VK_LCONTROL) & 0x8000) != 0
        right_ctrl = (user3.GetAsyncKeyState(VK_RCONTROL) & 0x8000) != 0
        backspace = (user3.GetAsyncKeyState(VK_BACK) & 0x8000) != 0
        if (left_ctrl or right_ctrl) and backspace:
            stop_flag = True
            print("\n🛑 【Ctrl + Backspace】全局停止热键触发，程序即将终止！")
            break
        time.sleep(0.02)

def get_clip_text():
    """读取剪贴板文本并去除首尾空白"""
    return pyperclip.paste().strip()

def capture_one_round(round_num):
    """单轮拖拽复制抓取逻辑"""
    global stop_flag
    if stop_flag:
        return None

    # 0.5秒移动到拖拽起点
    pyautogui.moveTo(START_X, START_Y, duration=MOVE_START_DURATION)
    time.sleep(0.1)
    if stop_flag:
        return None

    # 按住左键，拖拽到终点
    pyautogui.mouseDown()
    pyautogui.moveTo(END_X, END_Y, duration=DRAG_DURATION)
    # 拖拽完成停留3秒再松开
    time.sleep(WAIT_AFTER_DRAG)
    pyautogui.mouseUp()

    if stop_flag:
        return None

    # 点击复制按钮
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

def main():
    global stop_flag
    # 生成时间戳独立文本文件
    now = datetime.now()
    SAVE_FILE = f"wechat_{now.strftime('%Y%m%d_%H%M%S')}.txt"

    print("=" * 60)
    print("微信聊天批量抓取工具")
    print("🔴 全局停止热键：Ctrl + Backspace（任意窗口直接生效）")
    print("🔴 备用停止：PowerShell窗口按 Ctrl + C")
    print("=" * 60)
    print(f"输出文件路径：{os.path.abspath(SAVE_FILE)}")

    # 启动后台按键监听线程
    listener_thread = threading.Thread(target=global_key_listener, daemon=True)
    listener_thread.start()

    round_count = 1
    while True:
        if stop_flag:
            break

        block_data = capture_one_round(round_count)
        if stop_flag:
            break

        if block_data:
            with open(SAVE_FILE, "a", encoding="utf-8") as f:
                f.write(block_data)

        # 页面滚动，先等待足够加载时间再进行下一轮抓取（修复漏消息核心逻辑）
        pyautogui.scroll(SCROLL_STEP)
        time.sleep(WAIT_AFTER_SCROLL)
        round_count += 1

    print(f"\n✅ 抓取任务正常结束！保存文件：{os.path.abspath(SAVE_FILE)}")

if __name__ == "__main__":
    pyautogui.FAILSAFE = False
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n🛑 终端 Ctrl+C 手动停止，已保存当前全部内容")
    except Exception as err:
        print(f"\n⚠️ 程序异常中断，已保存已抓取数据")
        print(f"错误详情：{err}")