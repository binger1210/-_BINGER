import re
from datetime import datetime
from pathlib import Path

def parse_wechat_log(file_path, output_path=None):
    """
    解析微信导出的聊天记录（三行一组：发送者/时间/内容），
    去除分块标记、去重、按时间排序。
    """
    # 时间戳正则
    time_pattern = re.compile(r'^(\d{4}年\d{2}月\d{2}日\s+\d{1,2}:\d{2})$')

    def parse_time(timestamp_str):
        # 清理多余空格，替换中文日期分隔符
        clean = re.sub(r'\s+', ' ', timestamp_str.strip())
        clean = clean.replace('年', '-').replace('月', '-').replace('日', '')
        return datetime.strptime(clean, '%Y-%m-%d %H:%M')

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f if line.strip()]  # 去除空行

    records = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # 跳过分块标题
        if line.startswith('----------【'):
            i += 1
            continue

        # 检查当前行是否为时间戳
        if time_pattern.match(line):
            # 该行是时间戳，则前一行是发送者，后一行是内容
            if i - 1 < 0 or i + 1 >= len(lines):
                print(f'警告：时间戳 {line} 附近缺少发送者或内容，跳过')
                i += 1
                continue
            sender = lines[i - 1].strip()
            content = lines[i + 1].strip()
            # 组合成完整记录
            full_line = f"{sender} {line} {content}"
            # 去重检查（基于组合后整行）
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
                except Exception as e:
                    print(f'时间解析失败：{line}，错误：{e}')
            i += 3  # 跳过已处理的三行
        else:
            # 非时间戳行，可能是异常格式，跳过
            print(f'警告：无法识别的行（非时间戳）：{line[:30]}...')
            i += 1

    # 按时间排序
    records.sort(key=lambda x: x['dt'])

    # 输出
    if output_path is None:
        base = Path(file_path).stem
        output_path = f"{base}_tidy.txt"

    with open(output_path, 'w', encoding='utf-8') as f:
        for rec in records:
            f.write(rec['line'] + '\n')

    print(f'处理完成，共保留 {len(records)} 条消息，已写入：{output_path}')
    return output_path

if __name__ == '__main__':
    # 替换为您的文件路径
    input_file = 'wechat_20260722_144705.txt'
    parse_wechat_log(input_file)