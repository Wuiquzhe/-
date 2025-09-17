#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""任务管理模块"""

from datetime import datetime, timedelta
from .data_manager import DataManager
from .utils import get_current_date


class TaskManager:
    """任务管理类"""
    
    def __init__(self, base_dir):
        """初始化任务管理器
        
        Args:
            base_dir: 数据存储的基础目录
        """
        self.data_manager = DataManager(base_dir)
    
    def create_task(self, title, description="", category="", status="todo", 
                   priority="medium", due_date=None, tags=None, reminder=None):
        """创建新任务
        
        Args:
            title: 任务标题
            description: 任务描述
            category: 任务分类
            status: 任务状态（todo/in_progress/completed）
            priority: 优先级（high/medium/low）
            due_date: 截止日期
            tags: 标签列表
            reminder: 提醒时间
        
        Returns:
            创建成功的任务ID
        """
        task_data = {
            "title": title,
            "content": description,
            "category": category,
            "status": status,
            "priority": priority,
            "due_date": due_date,
            "tags": tags or [],
            "reminder": reminder,
            "progress_records": []
        }
        
        return self.data_manager.create_task(task_data)
    
    def get_task(self, task_id):
        """获取任务详情
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务数据字典，如果任务不存在则返回None
        """
        return self.data_manager.read_task(task_id)
    
    def update_task(self, task_id, **kwargs):
        """更新任务信息
        
        Args:
            task_id: 任务ID
            **kwargs: 要更新的任务属性
        
        Returns:
            是否更新成功
        """
        # 不要过滤None值，因为某些字段可能需要显式设置为None
        update_data = kwargs.copy()
        return self.data_manager.update_task(task_id, update_data)
    
    def delete_task(self, task_id):
        """删除任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否删除成功
        """
        return self.data_manager.delete_task(task_id)
    
    def list_tasks(self, status=None, category=None, date=None, priority=None, 
                  due_soon=False, overdue=False, search_text=""):
        """列出符合条件的任务
        
        Args:
            status: 任务状态过滤
            category: 分类过滤
            date: 日期过滤
            priority: 优先级过滤
            due_soon: 是否只显示即将到期的任务（24小时内）
            overdue: 是否只显示已过期的任务
            search_text: 搜索文本
        
        Returns:
            任务列表
        """
        # 先获取基本过滤条件的任务列表
        tasks = self.data_manager.list_tasks(status=status, category=category, date=date)
        
        # 应用额外的过滤条件
        filtered_tasks = []
        today = datetime.now().date()
        
        for task in tasks:
            # 优先级过滤
            if priority and task.get("priority") != priority:
                continue
            
            # 搜索文本过滤
            if search_text:
                search_lower = search_text.lower()
                title_match = search_lower in task.get("title", "").lower()
                desc_match = search_lower in task.get("content", "").lower()
                if not (title_match or desc_match):
                    continue
            
            # 到期时间过滤
            due_date_str = task.get("due_date")
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                    
                    # 过滤已过期任务
                    if overdue and due_date < today:
                        filtered_tasks.append(task)
                    # 过滤即将到期任务（24小时内）
                    elif due_soon and today <= due_date <= today + timedelta(days=1):
                        filtered_tasks.append(task)
                    # 不过滤到期时间相关的任务
                    elif not (overdue or due_soon):
                        filtered_tasks.append(task)
                except ValueError:
                    # 日期格式错误，不过滤
                    if not (overdue or due_soon):
                        filtered_tasks.append(task)
            else:
                # 没有设置到期时间，不过滤
                if not (overdue or due_soon):
                    filtered_tasks.append(task)
        
        return filtered_tasks
    
    def change_task_status(self, task_id, new_status):
        """更改任务状态
        
        Args:
            task_id: 任务ID
            new_status: 新的状态（todo/in_progress/completed）
        
        Returns:
            是否更改成功
        """
        valid_statuses = ["todo", "in_progress", "completed"]
        if new_status not in valid_statuses:
            return False
        
        # 更新任务状态
        return self.update_task(task_id, status=new_status)
    
    def add_task_progress(self, task_id, content):
        """添加任务进展记录
        
        Args:
            task_id: 任务ID
            content: 进展内容
        
        Returns:
            是否添加成功
        """
        return self.data_manager.add_progress_record(task_id, content)
    
    def set_task_priority(self, task_id, priority):
        """设置任务优先级
        
        Args:
            task_id: 任务ID
            priority: 优先级（high/medium/low）
        
        Returns:
            是否设置成功
        """
        valid_priorities = ["high", "medium", "low"]
        if priority not in valid_priorities:
            return False
        
        return self.update_task(task_id, priority=priority)
    
    def set_task_category(self, task_id, category):
        """设置任务分类
        
        Args:
            task_id: 任务ID
            category: 分类名称
        
        Returns:
            是否设置成功
        """
        return self.update_task(task_id, category=category)
    
    def set_task_due_date(self, task_id, due_date):
        """设置任务截止日期
        
        Args:
            task_id: 任务ID
            due_date: 截止日期
        
        Returns:
            是否设置成功
        """
        return self.update_task(task_id, due_date=due_date)
    
    def add_task_tag(self, task_id, tag):
        """添加任务标签
        
        Args:
            task_id: 任务ID
            tag: 标签名称
        
        Returns:
            是否添加成功
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        tags = task.get("tags", [])
        if tag not in tags:
            tags.append(tag)
            return self.update_task(task_id, tags=tags)
        
        return True
    
    def remove_task_tag(self, task_id, tag):
        """移除任务标签
        
        Args:
            task_id: 任务ID
            tag: 标签名称
        
        Returns:
            是否移除成功
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        tags = task.get("tags", [])
        if tag in tags:
            tags.remove(tag)
            return self.update_task(task_id, tags=tags)
        
        return True
    
    def calculate_task_progress(self, task_id):
        """计算任务完成进度
        
        Args:
            task_id: 任务ID
        
        Returns:
            进度百分比（0-100）
        """
        task = self.get_task(task_id)
        if not task:
            return 0
        
        # 根据状态快速判断
        if task.get("status") == "completed":
            return 100
        
        # 根据进展记录计算进度
        progress_records = task.get("progress_records", [])
        if not progress_records:
            return 0 if task.get("status") == "todo" else 50
        
        # 计算完成的进展记录比例
        completed_count = sum(1 for record in progress_records if record.get("completed", False))
        total_count = len(progress_records)
        
        return int((completed_count / total_count) * 100)
    
    def get_overdue_tasks(self):
        """获取所有已过期的任务
        
        Returns:
            过期任务列表
        """
        return self.list_tasks(overdue=True)
    
    def get_due_soon_tasks(self):
        """获取即将到期的任务（24小时内）
        
        Returns:
            即将到期任务列表
        """
        return self.list_tasks(due_soon=True)
    
    def get_high_priority_tasks(self):
        """获取所有高优先级任务
        
        Returns:
            高优先级任务列表
        """
        return self.list_tasks(priority="high")
    
    def get_tasks_by_category(self, category_name):
        """获取指定分类下的所有任务
        
        Args:
            category_name: 分类名称
        
        Returns:
            该分类下的任务列表
        """
        return self.list_tasks(category=category_name)
    
    def get_daily_tasks(self, date=None):
        """获取指定日期的每日任务
        
        Args:
            date: 日期，默认为当天
        
        Returns:
            每日任务列表
        """
        # 获取基本的每日任务列表
        daily_tasks = self.data_manager.get_daily_tasks(date)
        
        # 丰富任务信息
        enriched_tasks = []
        for task_ref in daily_tasks:
            task = self.get_task(task_ref["id"])
            if task:
                enriched_tasks.append(task)
        
        return enriched_tasks
    
    def search_tasks(self, search_text):
        """搜索任务
        
        Args:
            search_text: 搜索文本
        
        Returns:
            匹配的任务列表
        """
        return self.list_tasks(search_text=search_text)
    
    def get_task_stats(self):
        """获取任务统计信息
        
        Returns:
            统计信息字典
        """
        # 获取所有任务
        all_tasks = self.list_tasks()
        
        # 按状态统计
        status_counts = {"todo": 0, "in_progress": 0, "completed": 0}
        # 按优先级统计
        priority_counts = {"high": 0, "medium": 0, "low": 0}
        # 按分类统计
        category_counts = {}
        
        overdue_count = 0
        due_soon_count = 0
        today_count = 0
        
        today_date = get_current_date()
        today_date_obj = datetime.strptime(today_date, "%Y-%m-%d").date()
        
        for task in all_tasks:
            # 状态统计
            status = task.get("status", "todo")
            if status in status_counts:
                status_counts[status] += 1
            
            # 优先级统计
            priority = task.get("priority", "medium")
            if priority in priority_counts:
                priority_counts[priority] += 1
            
            # 分类统计
            category = task.get("category", "")
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # 到期时间统计
            due_date_str = task.get("due_date")
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                    
                    if due_date < today_date_obj:
                        overdue_count += 1
                    elif due_date == today_date_obj:
                        today_count += 1
                    elif due_date <= today_date_obj + timedelta(days=1):
                        due_soon_count += 1
                except ValueError:
                    pass
            
            # 今天的任务
            task_date = task.get("date", "")
            if task_date == today_date and not due_date_str:
                today_count += 1
        
        return {
            "total": len(all_tasks),
            "by_status": status_counts,
            "by_priority": priority_counts,
            "by_category": category_counts,
            "overdue": overdue_count,
            "due_soon": due_soon_count,
            "due_today": today_count
        }