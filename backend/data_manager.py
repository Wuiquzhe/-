#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Markdown文件管理模块"""

import os
import json
import yaml
from datetime import datetime
from .utils import (
    ensure_dir_exists,
    read_file,
    write_file,
    extract_front_matter,
    generate_markdown_with_front_matter,
    sanitize_filename,
    get_current_date
)


class DataManager:
    """Markdown文件数据管理类"""
    
    def __init__(self, base_dir):
        """初始化数据管理器
        
        Args:
            base_dir: 数据存储的基础目录
        """
        self.base_dir = os.path.join(base_dir, "data")
        ensure_dir_exists(self.base_dir)
        
        # 创建分类目录
        self.categories_dir = os.path.join(self.base_dir, "categories")
        ensure_dir_exists(self.categories_dir)
        
        # 创建状态目录
        self.status_dirs = {
            "todo": os.path.join(self.base_dir, "todo"),
            "in_progress": os.path.join(self.base_dir, "in_progress"),
            "completed": os.path.join(self.base_dir, "completed")
        }
        for dir_path in self.status_dirs.values():
            ensure_dir_exists(dir_path)
        
        # 创建每天的任务目录结构
        self.daily_dir = os.path.join(self.base_dir, "daily")
        ensure_dir_exists(self.daily_dir)
    
    def get_current_date(self):
        """获取当前日期，格式：YYYY-MM-DD
        
        Returns:
            当前日期字符串
        """
        return get_current_date()
    
    def get_task_file_path(self, task_id, status="todo"):
        """获取任务文件的路径
        
        Args:
            task_id: 任务ID
            status: 任务状态
        
        Returns:
            任务文件的绝对路径
        """
        status_dir = self.status_dirs.get(status, self.status_dirs["todo"])
        return os.path.join(status_dir, f"{task_id}.md")
    
    def get_daily_file_path(self, date=None):
        """获取指定日期的每日任务文件路径
        
        Args:
            date: 日期，格式为YYYY-MM-DD，默认为当天
        
        Returns:
            每日任务文件的绝对路径
        """
        if date is None:
            date = get_current_date()
        return os.path.join(self.daily_dir, f"{date}.md")
    
    def get_category_file_path(self, category_name):
        """获取分类文件的路径
        
        Args:
            category_name: 分类名称
        
        Returns:
            分类文件的绝对路径
        """
        sanitized_name = sanitize_filename(category_name)
        return os.path.join(self.categories_dir, f"{sanitized_name}.json")
    
    def create_task(self, task_data):
        """创建新任务或更新现有任务
        
        Args:
            task_data: 任务数据字典
        
        Returns:
            创建或更新成功的任务ID
        """
        # 使用传入的任务ID，如果没有则生成新的
        task_id = task_data.get("id")
        if not task_id:
            # 生成任务ID（使用时间戳+随机数）
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            task_id = f"task_{timestamp}"
            task_data["id"] = task_id
        
        # 设置默认值
        task_data.setdefault("created_at", get_current_date())
        task_data.setdefault("updated_at", get_current_date())
        task_data.setdefault("status", "todo")
        task_data.setdefault("priority", "medium")
        task_data.setdefault("progress_records", [])
        
        # 提取front matter和内容
        front_matter = task_data.copy()
        content = front_matter.pop("content", "")
        progress_records = front_matter.pop("progress_records", [])
        
        # 生成Markdown内容
        if content:
            content = f"# {front_matter.get('title', '')}\n\n## 任务描述\n{content}\n"
        else:
            content = f"# {front_matter.get('title', '')}\n\n## 任务描述\n（暂无描述）\n"
        
        # 添加进度记录
        if progress_records:
            content += "\n## 进展记录\n"
            for record in progress_records:
                status = "x" if record.get("completed", False) else " "
                date = record.get("date", get_current_date())
                content += f"- [{status}] {date}：{record.get('content', '')}\n"
        
        # 保存到文件
        markdown_content = generate_markdown_with_front_matter(front_matter, content)
        file_path = self.get_task_file_path(task_id, task_data["status"])
        write_file(file_path, markdown_content)
        
        # 如果有分类，更新分类信息
        if "category" in task_data:
            self.update_category_tasks(task_data["category"], task_id, "add")
        
        # 添加到今日任务（如果没有指定日期或日期为今天）
        if not task_data.get("date") or task_data["date"] == get_current_date():
            self.add_to_daily_tasks(task_id, task_data["title"])
        
        return task_id
    
    def read_task(self, task_id):
        """读取任务内容
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务数据字典，如果任务不存在则返回None
        """
        # 尝试在各个状态目录中查找任务文件
        for status in self.status_dirs:
            file_path = self.get_task_file_path(task_id, status)
            if os.path.exists(file_path):
                content = read_file(file_path)
                front_matter, markdown_content = extract_front_matter(content)
                
                # 解析进展记录
                progress_records = []
                progress_section = False
                for line in markdown_content.split('\n'):
                    if line.startswith("## 进展记录"):
                        progress_section = True
                    elif progress_section and line.startswith("- ["):
                        status_match = line[3]
                        date_content = line[6:].split("：", 1)
                        if len(date_content) >= 2:
                            date = date_content[0].strip()
                            content_text = date_content[1].strip()
                            progress_records.append({
                                "date": date,
                                "content": content_text,
                                "completed": status_match == "x"
                            })
                
                # 提取任务描述
                description = ""
                desc_section = False
                for line in markdown_content.split('\n'):
                    if line.startswith("## 任务描述"):
                        desc_section = True
                    elif desc_section and not line.startswith("## ") and line.strip():
                        description += line.strip() + "\n"
                
                front_matter["content"] = description.strip()
                front_matter["progress_records"] = progress_records
                front_matter["status"] = status  # 更新状态为当前所在目录
                
                return front_matter
        
        return None
    
    def update_task(self, task_id, update_data):
        """更新任务信息
        
        Args:
            task_id: 任务ID
            update_data: 更新的任务数据
        
        Returns:
            是否更新成功
        """
        # 先读取当前任务信息
        task_data = self.read_task(task_id)
        if not task_data:
            return False
        
        # 更新分类信息（如果分类发生变化）
        old_category = task_data.get("category")
        new_category = update_data.get("category")
        if old_category and old_category != new_category:
            self.update_category_tasks(old_category, task_id, "remove")
        if new_category and new_category != old_category:
            self.update_category_tasks(new_category, task_id, "add")
        
        # 更新状态（如果状态发生变化）
        old_status = task_data.get("status")
        new_status = update_data.get("status", old_status)
        
        # 合并更新数据
        task_data.update(update_data)
        task_data["updated_at"] = get_current_date()
        
        # 如果状态发生变化，需要移动文件
        if old_status != new_status:
            # 删除旧文件
            old_file_path = self.get_task_file_path(task_id, old_status)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        
        # 重新创建任务文件
        self.create_task(task_data)
        return True
    
    def delete_task(self, task_id):
        """删除任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否删除成功
        """
        # 先读取任务信息以获取分类
        task_data = self.read_task(task_id)
        if task_data:
            # 从分类中移除
            if "category" in task_data:
                self.update_category_tasks(task_data["category"], task_id, "remove")
            
            # 从每日任务中移除
            self.remove_from_daily_tasks(task_id)
            
            # 删除任务文件
            for status in self.status_dirs:
                file_path = self.get_task_file_path(task_id, status)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
        
        return False
    
    def list_tasks(self, status=None, category=None, date=None):
        """列出符合条件的任务
        
        Args:
            status: 任务状态过滤
            category: 分类过滤
            date: 日期过滤
        
        Returns:
            任务列表
        """
        tasks = []
        
        # 确定要搜索的目录
        search_dirs = []
        if status and status in self.status_dirs:
            search_dirs.append(self.status_dirs[status])
        else:
            search_dirs = list(self.status_dirs.values())
        
        # 搜索所有匹配的任务文件
        for dir_path in search_dirs:
            for filename in os.listdir(dir_path):
                if filename.endswith(".md"):
                    task_id = filename[:-3]
                    task_data = self.read_task(task_id)
                    
                    # 应用过滤条件
                    if task_data:
                        if category and task_data.get("category") != category:
                            continue
                        if date and task_data.get("date") != date:
                            continue
                        
                        tasks.append(task_data)
        
        # 按更新时间排序（最新的在前）
        tasks.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return tasks
    
    def add_progress_record(self, task_id, content):
        """添加任务进展记录
        
        Args:
            task_id: 任务ID
            content: 进展内容
        
        Returns:
            是否添加成功
        """
        task_data = self.read_task(task_id)
        if not task_data:
            return False
        
        # 添加新的进展记录
        progress_records = task_data.get("progress_records", [])
        progress_records.append({
            "date": get_current_date(),
            "content": content,
            "completed": False
        })
        
        # 更新任务（只传递需要更新的字段）
        return self.update_task(task_id, {"progress_records": progress_records})
    
    def update_category_tasks(self, category_name, task_id, action="add"):
        """更新分类中的任务列表
        
        Args:
            category_name: 分类名称
            task_id: 任务ID
            action: 操作类型（add/remove）
        """
        file_path = self.get_category_file_path(category_name)
        
        # 读取现有分类数据
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                category_data = json.load(f)
        else:
            category_data = {"name": category_name, "tasks": []}
        
        # 更新任务列表
        if action == "add" and task_id not in category_data["tasks"]:
            category_data["tasks"].append(task_id)
        elif action == "remove" and task_id in category_data["tasks"]:
            category_data["tasks"].remove(task_id)
        
        # 保存更新后的数据
        ensure_dir_exists(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(category_data, f, ensure_ascii=False, indent=2)
    
    def list_categories(self):
        """列出所有分类
        
        Returns:
            分类列表
        """
        categories = []
        for filename in os.listdir(self.categories_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.categories_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    category_data = json.load(f)
                    categories.append(category_data)
        
        return categories
    
    def add_to_daily_tasks(self, task_id, task_title, date=None):
        """添加任务到每日任务列表
        
        Args:
            task_id: 任务ID
            task_title: 任务标题
            date: 日期，默认为当天
        """
        file_path = self.get_daily_file_path(date)
        
        # 读取现有每日任务
        if os.path.exists(file_path):
            content = read_file(file_path)
            front_matter, markdown_content = extract_front_matter(content)
        else:
            front_matter = {"date": date or get_current_date()}
            markdown_content = ""
        
        # 检查任务是否已存在
        if task_id not in markdown_content:
            # 添加任务到列表
            if not markdown_content.strip():
                markdown_content = "# 今日任务\n\n## 待办任务\n"
            
            # 查找待办任务部分
            todo_section_start = markdown_content.find("## 待办任务")
            if todo_section_start != -1:
                # 找到待办任务部分，在其后添加新任务
                lines = markdown_content[todo_section_start:].split('\n')
                # 找到第一个非标题行的位置
                insert_pos = 1
                while insert_pos < len(lines) and lines[insert_pos].strip():
                    insert_pos += 1
                lines.insert(insert_pos, f"- [{task_id}] {task_title}")
                new_content = markdown_content[:todo_section_start] + '\n'.join(lines)
            else:
                # 没有待办任务部分，添加新的
                new_content = markdown_content + "\n## 待办任务\n" + f"- [{task_id}] {task_title}\n"
            
            # 保存更新后的内容
            markdown_content = generate_markdown_with_front_matter(front_matter, new_content)
            write_file(file_path, markdown_content)
    
    def remove_from_daily_tasks(self, task_id, date=None):
        """从每日任务列表中移除任务
        
        Args:
            task_id: 任务ID
            date: 日期，默认为当天
        """
        file_path = self.get_daily_file_path(date)
        
        if os.path.exists(file_path):
            content = read_file(file_path)
            front_matter, markdown_content = extract_front_matter(content)
            
            # 查找并移除包含任务ID的行
            lines = markdown_content.split('\n')
            new_lines = [line for line in lines if f"[{task_id}]" not in line]
            new_content = '\n'.join(new_lines)
            
            # 保存更新后的内容
            markdown_content = generate_markdown_with_front_matter(front_matter, new_content)
            write_file(file_path, markdown_content)
    
    def get_daily_tasks(self, date=None):
        """获取指定日期的每日任务
        
        Args:
            date: 日期，默认为当天
        
        Returns:
            每日任务列表
        """
        file_path = self.get_daily_file_path(date)
        tasks = []
        
        if os.path.exists(file_path):
            content = read_file(file_path)
            _, markdown_content = extract_front_matter(content)
            
            # 查找待办任务部分
            todo_section_start = markdown_content.find("## 待办任务")
            if todo_section_start != -1:
                todo_content = markdown_content[todo_section_start:]
                # 查找下一个标题行
                next_section_start = todo_content.find("## ", 6)  # 从"## 待办任务"之后开始查找
                if next_section_start != -1:
                    todo_content = todo_content[:next_section_start]
                
                # 解析任务列表
                for line in todo_content.split('\n'):
                    if line.startswith("- ["):
                        # 提取任务ID和标题
                        id_start = line.find("[") + 1
                        id_end = line.find("]")
                        if id_start < id_end:
                            task_id = line[id_start:id_end]
                            task_title = line[id_end + 2:].strip()  # 跳过"] "
                            tasks.append({"id": task_id, "title": task_title})
        
        return tasks