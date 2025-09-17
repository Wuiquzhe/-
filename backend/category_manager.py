#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分类管理模块"""

import os
import json
from .utils import ensure_dir_exists, sanitize_filename
from .data_manager import DataManager


class CategoryManager:
    """任务分类管理类"""
    
    def __init__(self, base_dir):
        """初始化分类管理器
        
        Args:
            base_dir: 数据存储的基础目录
        """
        self.data_manager = DataManager(base_dir)
        self.categories_dir = os.path.join(base_dir, "data", "categories")
        ensure_dir_exists(self.categories_dir)
    
    def create_category(self, name, description="", color="#4CAF50", icon=None):
        """创建新分类
        
        Args:
            name: 分类名称
            description: 分类描述
            color: 分类颜色（十六进制）
            icon: 分类图标
        
        Returns:
            是否创建成功
        """
        # 检查分类是否已存在
        if self.category_exists(name):
            return False
        
        # 净化分类名称用于文件名
        sanitized_name = sanitize_filename(name)
        file_path = os.path.join(self.categories_dir, f"{sanitized_name}.json")
        
        # 创建分类数据
        category_data = {
            "name": name,
            "description": description,
            "color": color,
            "icon": icon,
            "tasks": [],
            "created_at": self.data_manager.get_current_date()
        }
        
        # 保存分类数据
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(category_data, f, ensure_ascii=False, indent=2)
        
        return True
    
    def get_category(self, name):
        """获取分类信息
        
        Args:
            name: 分类名称
        
        Returns:
            分类数据字典，如果分类不存在则返回None
        """
        # 尝试直接通过名称查找
        sanitized_name = sanitize_filename(name)
        file_path = os.path.join(self.categories_dir, f"{sanitized_name}.json")
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 如果没找到，尝试遍历所有分类文件查找名称匹配的
        for filename in os.listdir(self.categories_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.categories_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    category_data = json.load(f)
                    if category_data.get("name") == name:
                        return category_data
        
        return None
    
    def update_category(self, old_name, new_name=None, description=None, 
                       color=None, icon=None):
        """更新分类信息
        
        Args:
            old_name: 原分类名称
            new_name: 新分类名称
            description: 新的分类描述
            color: 新的分类颜色
            icon: 新的分类图标
        
        Returns:
            是否更新成功
        """
        # 获取当前分类信息
        category_data = self.get_category(old_name)
        if not category_data:
            return False
        
        # 检查新名称是否已被使用（如果更改名称）
        if new_name and new_name != old_name and self.category_exists(new_name):
            return False
        
        # 更新分类信息
        if new_name:
            category_data["name"] = new_name
        if description is not None:
            category_data["description"] = description
        if color is not None:
            category_data["color"] = color
        if icon is not None:
            category_data["icon"] = icon
        
        category_data["updated_at"] = self.data_manager.get_current_date()
        
        # 如果更改了名称，需要更新文件名
        if new_name and new_name != old_name:
            # 删除旧文件
            old_sanitized = sanitize_filename(old_name)
            old_file_path = os.path.join(self.categories_dir, f"{old_sanitized}.json")
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
            
            # 保存新文件
            new_sanitized = sanitize_filename(new_name)
            new_file_path = os.path.join(self.categories_dir, f"{new_sanitized}.json")
            
            with open(new_file_path, 'w', encoding='utf-8') as f:
                json.dump(category_data, f, ensure_ascii=False, indent=2)
            
            # 更新分类中所有任务的分类信息
            for task_id in category_data.get("tasks", []):
                task = self.data_manager.read_task(task_id)
                if task:
                    self.data_manager.update_task(task_id, {"category": new_name})
        else:
            # 只更新内容，不更改文件名
            sanitized_name = sanitize_filename(old_name)
            file_path = os.path.join(self.categories_dir, f"{sanitized_name}.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(category_data, f, ensure_ascii=False, indent=2)
        
        return True
    
    def delete_category(self, name):
        """删除分类
        
        Args:
            name: 分类名称
        
        Returns:
            是否删除成功
        """
        # 获取分类信息
        category_data = self.get_category(name)
        if not category_data:
            return False
        
        # 获取分类下的所有任务
        tasks = category_data.get("tasks", [])
        
        # 移除所有任务的分类信息
        for task_id in tasks:
            task = self.data_manager.read_task(task_id)
            if task:
                self.data_manager.update_task(task_id, {"category": ""})
        
        # 删除分类文件
        sanitized_name = sanitize_filename(name)
        file_path = os.path.join(self.categories_dir, f"{sanitized_name}.json")
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        
        return False
    
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
        
        # 按名称排序
        categories.sort(key=lambda x: x.get("name", ""))
        
        return categories
    
    def category_exists(self, name):
        """检查分类是否存在
        
        Args:
            name: 分类名称
        
        Returns:
            分类是否存在
        """
        return self.get_category(name) is not None
    
    def add_task_to_category(self, category_name, task_id):
        """添加任务到分类
        
        Args:
            category_name: 分类名称
            task_id: 任务ID
        
        Returns:
            是否添加成功
        """
        # 检查分类是否存在
        category_data = self.get_category(category_name)
        if not category_data:
            return False
        
        # 检查任务是否已存在于分类中
        tasks = category_data.get("tasks", [])
        if task_id in tasks:
            return True  # 已经在分类中，无需操作
        
        # 添加任务到分类
        tasks.append(task_id)
        category_data["tasks"] = tasks
        
        # 保存更新后的分类信息
        sanitized_name = sanitize_filename(category_name)
        file_path = os.path.join(self.categories_dir, f"{sanitized_name}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(category_data, f, ensure_ascii=False, indent=2)
        
        # 同时更新任务的分类信息
        task = self.data_manager.read_task(task_id)
        if task:
            self.data_manager.update_task(task_id, category=category_name)
        
        return True
    
    def remove_task_from_category(self, category_name, task_id):
        """从分类中移除任务
        
        Args:
            category_name: 分类名称
            task_id: 任务ID
        
        Returns:
            是否移除成功
        """
        # 检查分类是否存在
        category_data = self.get_category(category_name)
        if not category_data:
            return False
        
        # 检查任务是否在分类中
        tasks = category_data.get("tasks", [])
        if task_id not in tasks:
            return True  # 不在分类中，无需操作
        
        # 从分类中移除任务
        tasks.remove(task_id)
        category_data["tasks"] = tasks
        
        # 保存更新后的分类信息
        sanitized_name = sanitize_filename(category_name)
        file_path = os.path.join(self.categories_dir, f"{sanitized_name}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(category_data, f, ensure_ascii=False, indent=2)
        
        # 如果任务没有其他分类，清空任务的分类信息
        task = self.data_manager.read_task(task_id)
        if task and task.get("category") == category_name:
            self.data_manager.update_task(task_id, category="")
        
        return True
    
    def get_category_tasks(self, category_name):
        """获取分类下的所有任务
        
        Args:
            category_name: 分类名称
        
        Returns:
            任务列表
        """
        category_data = self.get_category(category_name)
        if not category_data:
            return []
        
        tasks = []
        for task_id in category_data.get("tasks", []):
            task = self.data_manager.read_task(task_id)
            if task:
                tasks.append(task)
        
        # 按更新时间排序（最新的在前）
        tasks.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return tasks
    
    def get_category_stats(self):
        """获取分类统计信息
        
        Returns:
            分类统计信息字典
        """
        categories = self.list_categories()
        stats = {}
        
        for category in categories:
            category_name = category.get("name", "")
            task_count = len(category.get("tasks", []))
            
            stats[category_name] = {
                "task_count": task_count,
                "color": category.get("color", "#4CAF50"),
                "icon": category.get("icon")
            }
        
        return stats
    
    def rename_category(self, old_name, new_name):
        """重命名分类
        
        Args:
            old_name: 原分类名称
            new_name: 新分类名称
        
        Returns:
            是否重命名成功
        """
        return self.update_category(old_name, new_name=new_name)
    
    def set_category_color(self, name, color):
        """设置分类颜色
        
        Args:
            name: 分类名称
            color: 分类颜色（十六进制）
        
        Returns:
            是否设置成功
        """
        return self.update_category(name, color=color)
    
    def set_category_icon(self, name, icon):
        """设置分类图标
        
        Args:
            name: 分类名称
            icon: 分类图标
        
        Returns:
            是否设置成功
        """
        return self.update_category(name, icon=icon)