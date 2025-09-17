#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工具函数模块"""

import os
import re
import json
import yaml
from datetime import datetime, timedelta


def ensure_dir_exists(dir_path):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def get_current_timestamp():
    """获取当前时间戳，格式为YYYY-MM-DD HH:MM:SS"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_date():
    """获取当前日期，格式为YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")


def parse_date(date_str):
    """解析日期字符串，返回datetime对象"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def format_date(dt):
    """将datetime对象格式化为YYYY-MM-DD格式的字符串"""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    return str(dt)


def read_file(file_path):
    """读取文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(file_path, content):
    """写入内容到文件"""
    ensure_dir_exists(os.path.dirname(file_path))
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def append_file(file_path, content):
    """追加内容到文件"""
    ensure_dir_exists(os.path.dirname(file_path))
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(content)


def load_json(file_path):
    """加载JSON文件"""
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(file_path, data):
    """保存数据为JSON文件"""
    ensure_dir_exists(os.path.dirname(file_path))
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_yaml(file_path):
    """加载YAML文件"""
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_yaml(file_path, data):
    """保存数据为YAML文件"""
    ensure_dir_exists(os.path.dirname(file_path))
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


def extract_front_matter(markdown_content):
    """从Markdown内容中提取YAML front matter"""
    pattern = r'^---\s*$(.*?)^---\s*$(.*)'
    match = re.search(pattern, markdown_content, re.MULTILINE | re.DOTALL)
    if match:
        front_matter_str = match.group(1)
        content = match.group(2).strip()
        try:
            front_matter = yaml.safe_load(front_matter_str)
            return front_matter or {}, content
        except yaml.YAMLError:
            return {}, markdown_content
    return {}, markdown_content


def generate_markdown_with_front_matter(front_matter, content):
    """生成带有YAML front matter的Markdown内容"""
    front_matter_str = yaml.dump(front_matter, allow_unicode=True, default_flow_style=False)
    return f"---\n{front_matter_str}---\n\n{content}"


def sanitize_filename(filename):
    """清理文件名，移除不合法字符"""
    # 替换不合法字符为下划线
    return re.sub(r'[\\/:*?\"<>|]', '_', filename)


def get_time_diff_str(time1, time2):
    """计算两个时间的差值并返回友好的字符串表示"""
    if isinstance(time1, str):
        time1 = parse_date(time1)
    if isinstance(time2, str):
        time2 = parse_date(time2)
    
    if not time1 or not time2:
        return "未知时间"
    
    diff = abs(time1 - time2)
    days = diff.days
    seconds = diff.seconds
    
    if days > 0:
        return f"{days}天前"
    elif seconds >= 3600:
        hours = seconds // 3600
        return f"{hours}小时前"
    elif seconds >= 60:
        minutes = seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"