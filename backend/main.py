#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工作计划记录小程序后端主入口"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from flask import Flask, request, jsonify

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入各个功能模块
from .task_manager import TaskManager
from .category_manager import CategoryManager
from .utils import get_current_date, ensure_dir_exists

# 创建Flask应用实例
app = Flask(__name__)

# 添加CORS支持
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# 处理OPTIONS请求
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return '', 204

# 配置应用
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")

# 确保数据目录存在
ensure_dir_exists(DATA_DIR)

# 初始化各个管理器
task_manager = TaskManager(BASE_DIR)
category_manager = CategoryManager(BASE_DIR)


# 辅助函数：格式化API响应
def make_response(success: bool, data: Any = None, message: str = "") -> Dict[str, Any]:
    """生成标准的API响应格式
    
    Args:
        success: 操作是否成功
        data: 返回的数据
        message: 消息文本
    
    Returns:
        格式化的响应字典
    """
    return {
        "success": success,
        "data": data,
        "message": message
    }


# 任务相关API路由
@app.route('/api/tasks', methods=['POST'])
def create_task():
    """创建新任务"""
    try:
        data = request.json
        
        # 提取任务信息
        title = data.get('title', '').strip() if data.get('title') is not None else ''
        description = data.get('description', '').strip() if data.get('description') is not None else ''
        # 同时支持category和category_id参数，解决前后端参数名不匹配问题
        # 安全地处理可能为None的值
        category_val = data.get('category', '')
        category_id_val = data.get('category_id', '')
        category = (category_val.strip() if category_val is not None else '') or \
                   (category_id_val.strip() if category_id_val is not None else '')
        status = data.get('status', 'todo')
        priority = data.get('priority', 'medium')
        due_date = data.get('due_date')
        tags = data.get('tags', [])
        reminder = data.get('reminder')
        progress_records = data.get('progress_records', [])
        
        # 验证必要字段
        if not title:
            return jsonify(make_response(False, message="任务标题不能为空")), 400
        
        # 验证状态和优先级
        valid_statuses = ['todo', 'in_progress', 'completed']
        valid_priorities = ['high', 'medium', 'low']
        
        if status not in valid_statuses:
            return jsonify(make_response(False, message=f"无效的状态值，有效值：{', '.join(valid_statuses)}")), 400
        
        if priority not in valid_priorities:
            return jsonify(make_response(False, message=f"无效的优先级，有效值：{', '.join(valid_priorities)}")), 400
        
        # 创建任务
        task_id = task_manager.create_task(
            title=title,
            description=description,
            category=category,
            status=status,
            priority=priority,
            due_date=due_date,
            tags=tags,
            reminder=reminder
        )
        
        # 如果有进展记录，更新任务
        if progress_records:
            task = task_manager.get_task(task_id)
            if task:
                task['progress_records'] = progress_records
                task_manager.update_task(task_id, **task)
        
        # 获取创建后的任务详情
        task = task_manager.get_task(task_id)
        
        return jsonify(make_response(True, data=task, message="任务创建成功")), 201
        
    except Exception as e:
        return jsonify(make_response(False, message=f"创建任务失败：{str(e)}")), 500


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    try:
        # 提取查询参数
        status = request.args.get('status')
        category = request.args.get('category')
        date = request.args.get('date')
        priority = request.args.get('priority')
        due_soon = request.args.get('due_soon', 'false').lower() == 'true'
        overdue = request.args.get('overdue', 'false').lower() == 'true'
        search_text = request.args.get('search', '')
        
        # 获取任务列表
        tasks = task_manager.list_tasks(
            status=status,
            category=category,
            date=date,
            priority=priority,
            due_soon=due_soon,
            overdue=overdue,
            search_text=search_text
        )
        
        return jsonify(make_response(True, data=tasks)), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"获取任务列表失败：{str(e)}")), 500


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取单个任务详情"""
    try:
        task = task_manager.get_task(task_id)
        
        if not task:
            return jsonify(make_response(False, message="任务不存在")), 404
        
        return jsonify(make_response(True, data=task)), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"获取任务详情失败：{str(e)}")), 500


@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务信息"""
    try:
        data = request.json
        
        # 检查任务是否存在
        if not task_manager.get_task(task_id):
            return jsonify(make_response(False, message="任务不存在")), 404
        
        # 更新任务
        success = task_manager.update_task(task_id, **data)
        
        if success:
            # 获取更新后的任务详情
            updated_task = task_manager.get_task(task_id)
            return jsonify(make_response(True, data=updated_task, message="任务更新成功")), 200
        else:
            return jsonify(make_response(False, message="任务更新失败")), 500
            
    except Exception as e:
        return jsonify(make_response(False, message=f"更新任务失败：{str(e)}")), 500


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    try:
        # 检查任务是否存在
        if not task_manager.get_task(task_id):
            return jsonify(make_response(False, message="任务不存在")), 404
        
        # 删除任务
        success = task_manager.delete_task(task_id)
        
        if success:
            return jsonify(make_response(True, message="任务删除成功")), 200
        else:
            return jsonify(make_response(False, message="任务删除失败")), 500
            
    except Exception as e:
        return jsonify(make_response(False, message=f"删除任务失败：{str(e)}")), 500


@app.route('/api/tasks/<task_id>/status', methods=['PATCH'])
def change_task_status(task_id):
    """更改任务状态"""
    try:
        data = request.json
        new_status = data.get('status', '').strip()
        
        # 验证状态值
        valid_statuses = ['todo', 'in_progress', 'completed']
        if new_status not in valid_statuses:
            return jsonify(make_response(False, message=f"无效的状态值，有效值：{', '.join(valid_statuses)}")), 400
        
        # 更改状态
        success = task_manager.change_task_status(task_id, new_status)
        
        if success:
            # 获取更新后的任务详情
            updated_task = task_manager.get_task(task_id)
            return jsonify(make_response(True, data=updated_task, message="任务状态更新成功")), 200
        else:
            return jsonify(make_response(False, message="任务状态更新失败")), 500
            
    except Exception as e:
        return jsonify(make_response(False, message=f"更改任务状态失败：{str(e)}")), 500


@app.route('/api/tasks/<task_id>/progress', methods=['POST'])
def add_task_progress(task_id):
    """添加任务进展记录"""
    try:
        data = request.json
        content = data.get('content', '').strip()
        
        # 验证内容
        if not content:
            return jsonify(make_response(False, message="进展内容不能为空")), 400
        
        # 添加进展记录
        success = task_manager.add_task_progress(task_id, content)
        
        if success:
            # 获取更新后的任务详情
            updated_task = task_manager.get_task(task_id)
            return jsonify(make_response(True, data=updated_task, message="进展记录添加成功")), 200
        else:
            return jsonify(make_response(False, message="任务不存在或进展记录添加失败")), 500
            
    except Exception as e:
        return jsonify(make_response(False, message=f"添加进展记录失败：{str(e)}")), 500


@app.route('/api/tasks/<task_id>/progress/calculate', methods=['GET'])
def calculate_task_progress(task_id):
    """计算任务进度"""
    try:
        progress = task_manager.calculate_task_progress(task_id)
        
        return jsonify(make_response(True, data={"progress": progress})), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"计算任务进度失败：{str(e)}")), 500


# 分类相关API路由
@app.route('/api/categories', methods=['POST'])
def create_category():
    """创建新分类"""
    try:
        data = request.json
        
        # 提取分类信息
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        color = data.get('color', '#4CAF50')
        icon = data.get('icon')
        
        # 验证必要字段
        if not name:
            return jsonify(make_response(False, message="分类名称不能为空")), 400
        
        # 检查分类是否已存在
        if category_manager.category_exists(name):
            return jsonify(make_response(False, message="分类已存在")), 409
        
        # 创建分类
        success = category_manager.create_category(
            name=name,
            description=description,
            color=color,
            icon=icon
        )
        
        if success:
            # 获取创建后的分类详情
            category = category_manager.get_category(name)
            return jsonify(make_response(True, data=category, message="分类创建成功")), 201
        else:
            return jsonify(make_response(False, message="分类创建失败")), 500
            
    except Exception as e:
        return jsonify(make_response(False, message=f"创建分类失败：{str(e)}")), 500


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """获取分类列表"""
    try:
        categories = category_manager.list_categories()
        return jsonify(make_response(True, data=categories)), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"获取分类列表失败：{str(e)}")), 500


@app.route('/api/categories/<category_name>', methods=['GET'])
def get_category(category_name):
    """获取单个分类详情"""
    try:
        category = category_manager.get_category(category_name)
        
        if not category:
            return jsonify(make_response(False, message="分类不存在")), 404
        
        return jsonify(make_response(True, data=category)), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"获取分类详情失败：{str(e)}")), 500


@app.route('/api/categories/<category_name>', methods=['PUT'])
def update_category(category_name):
    """更新分类信息"""
    try:
        data = request.json
        
        # 检查分类是否存在
        if not category_manager.category_exists(category_name):
            return jsonify(make_response(False, message="分类不存在")), 404
        
        # 提取更新信息
        new_name = data.get('name')
        description = data.get('description')
        color = data.get('color')
        icon = data.get('icon')
        
        # 更新分类
        success = category_manager.update_category(
            old_name=category_name,
            new_name=new_name,
            description=description,
            color=color,
            icon=icon
        )
        
        if success:
            # 获取更新后的分类详情
            updated_category = category_manager.get_category(new_name or category_name)
            return jsonify(make_response(True, data=updated_category, message="分类更新成功")), 200
        else:
            return jsonify(make_response(False, message="分类更新失败")), 500
            
    except Exception as e:
        return jsonify(make_response(False, message=f"更新分类失败：{str(e)}")), 500


@app.route('/api/categories/<category_name>', methods=['DELETE'])
def delete_category(category_name):
    """删除分类"""
    try:
        # 检查分类是否存在
        if not category_manager.category_exists(category_name):
            return jsonify(make_response(False, message="分类不存在")), 404
        
        # 删除分类
        success = category_manager.delete_category(category_name)
        
        if success:
            return jsonify(make_response(True, message="分类删除成功")), 200
        else:
            return jsonify(make_response(False, message="分类删除失败")), 500
            
    except Exception as e:
        return jsonify(make_response(False, message=f"删除分类失败：{str(e)}")), 500


@app.route('/api/categories/<category_name>/tasks', methods=['GET'])
def get_category_tasks(category_name):
    """获取分类下的任务列表"""
    try:
        # 检查分类是否存在
        if not category_manager.category_exists(category_name):
            return jsonify(make_response(False, message="分类不存在")), 404
        
        # 获取分类下的任务
        tasks = category_manager.get_category_tasks(category_name)
        
        return jsonify(make_response(True, data=tasks)), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"获取分类任务失败：{str(e)}")), 500


# 统计信息相关API路由
@app.route('/api/stats/tasks', methods=['GET'])
def get_task_stats():
    """获取任务统计信息"""
    try:
        stats = task_manager.get_task_stats()
        return jsonify(make_response(True, data=stats)), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"获取任务统计失败：{str(e)}")), 500


@app.route('/api/stats/categories', methods=['GET'])
def get_category_stats():
    """获取分类统计信息"""
    try:
        stats = category_manager.get_category_stats()
        return jsonify(make_response(True, data=stats)), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"获取分类统计失败：{str(e)}")), 500


# 每日任务相关API路由
@app.route('/api/daily', methods=['GET'])
def get_daily_tasks():
    """获取今日任务"""
    try:
        date = request.args.get('date')
        tasks = task_manager.get_daily_tasks(date)
        return jsonify(make_response(True, data=tasks)), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"获取每日任务失败：{str(e)}")), 500


# 搜索相关API路由
@app.route('/api/search', methods=['GET'])
def search_tasks():
    """搜索任务"""
    try:
        search_text = request.args.get('q', '')
        if not search_text:
            return jsonify(make_response(False, message="搜索文本不能为空")), 400
        
        tasks = task_manager.search_tasks(search_text)
        return jsonify(make_response(True, data=tasks)), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"搜索任务失败：{str(e)}")), 500


# 特殊任务筛选API路由
@app.route('/api/tasks/overdue', methods=['GET'])
def get_overdue_tasks():
    """获取已过期任务"""
    try:
        tasks = task_manager.get_overdue_tasks()
        return jsonify(make_response(True, data=tasks)), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"获取过期任务失败：{str(e)}")), 500


@app.route('/api/tasks/due-soon', methods=['GET'])
def get_due_soon_tasks():
    """获取即将到期任务"""
    try:
        tasks = task_manager.get_due_soon_tasks()
        return jsonify(make_response(True, data=tasks)), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"获取即将到期任务失败：{str(e)}")), 500


@app.route('/api/tasks/high-priority', methods=['GET'])
def get_high_priority_tasks():
    """获取高优先级任务"""
    try:
        tasks = task_manager.get_high_priority_tasks()
        return jsonify(make_response(True, data=tasks)), 200
        
    except Exception as e:
        return jsonify(make_response(False, message=f"获取高优先级任务失败：{str(e)}")), 500


# 应用初始化和运行
if __name__ == '__main__':
    # 启动Flask服务器
    print(f"工作计划记录小程序后端服务启动中...")
    print(f"数据存储目录: {DATA_DIR}")
    print(f"服务监听地址: http://localhost:5000")
    print(f"API文档请访问: http://localhost:5000/api/docs")
    
    # 在开发模式下启动服务
    app.run(host='localhost', port=5000, debug=True)