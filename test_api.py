#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试DailyEnchant后端API功能"""

import requests
import json
import time
from datetime import datetime, timedelta

# API基础URL
BASE_URL = "http://localhost:5000/api"

class APITester:
    """API测试类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.current_task_id = None
        self.current_category_name = "测试分类"
    
    def log_result(self, test_name, success, message=""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        status = "✓ 通过" if success else "✗ 失败"
        print(f"[{status}] {test_name}: {message}")
    
    def run_test(self, test_name, test_func):
        """运行单个测试"""
        try:
            test_func()
        except Exception as e:
            self.log_result(test_name, False, f"测试异常: {str(e)}")
    
    def create_category(self):
        """测试创建分类API"""
        url = f"{BASE_URL}/categories"
        category_data = {
            "name": self.current_category_name,
            "description": "这是一个测试分类",
            "color": "#FF5733",
            "icon": "fas fa-tag"
        }
        
        # 先检查分类是否已存在，如果存在则删除
        try:
            delete_url = f"{BASE_URL}/categories/{self.current_category_name}"
            self.session.delete(delete_url)
        except:
            pass
            
        response = self.session.post(url, json=category_data)
        data = response.json()
        
        if response.status_code == 201 and data.get("success"):
            self.log_result("创建分类", True, "成功创建测试分类")
        else:
            self.log_result("创建分类", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def get_categories(self):
        """测试获取分类列表API"""
        url = f"{BASE_URL}/categories"
        response = self.session.get(url)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            categories = data.get("data", [])
            self.log_result("获取分类列表", True, f"成功获取{len(categories)}个分类")
        else:
            self.log_result("获取分类列表", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def create_task(self):
        """测试创建任务API"""
        url = f"{BASE_URL}/tasks"
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        task_data = {
            "title": "测试任务 - " + datetime.now().strftime("%H:%M:%S"),
            "description": "这是一个用于测试API的任务",
            "category": self.current_category_name,
            "status": "todo",
            "priority": "medium",
            "due_date": tomorrow,
            "tags": ["测试", "API"]
        }
        
        response = self.session.post(url, json=task_data)
        data = response.json()
        
        if response.status_code == 201 and data.get("success"):
            task = data.get("data", {})
            self.current_task_id = task.get("id")
            self.log_result("创建任务", True, f"成功创建任务: {task.get('title')}")
        else:
            self.log_result("创建任务", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def get_tasks(self):
        """测试获取任务列表API"""
        url = f"{BASE_URL}/tasks"
        response = self.session.get(url)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            tasks = data.get("data", [])
            self.log_result("获取任务列表", True, f"成功获取{len(tasks)}个任务")
        else:
            self.log_result("获取任务列表", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def get_task(self):
        """测试获取单个任务API"""
        if not self.current_task_id:
            self.log_result("获取单个任务", False, "没有可测试的任务ID")
            return
            
        url = f"{BASE_URL}/tasks/{self.current_task_id}"
        response = self.session.get(url)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            task = data.get("data", {})
            self.log_result("获取单个任务", True, f"成功获取任务: {task.get('title')}")
        else:
            self.log_result("获取单个任务", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def update_task(self):
        """测试更新任务API"""
        if not self.current_task_id:
            self.log_result("更新任务", False, "没有可测试的任务ID")
            return
            
        url = f"{BASE_URL}/tasks/{self.current_task_id}"
        update_data = {
            "title": "更新后的测试任务",
            "description": "这是更新后的任务描述",
            "status": "in_progress"
        }
        
        response = self.session.put(url, json=update_data)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            updated_task = data.get("data", {})
            self.log_result("更新任务", True, f"成功更新任务: {updated_task.get('title')}")
        else:
            self.log_result("更新任务", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def change_task_status(self):
        """测试更改任务状态API"""
        if not self.current_task_id:
            self.log_result("更改任务状态", False, "没有可测试的任务ID")
            return
            
        url = f"{BASE_URL}/tasks/{self.current_task_id}/status"
        status_data = {
            "status": "completed"
        }
        
        response = self.session.patch(url, json=status_data)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            updated_task = data.get("data", {})
            self.log_result("更改任务状态", True, f"成功更改任务状态为: {updated_task.get('status')}")
        else:
            self.log_result("更改任务状态", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def add_task_progress(self):
        """测试添加任务进展API"""
        if not self.current_task_id:
            self.log_result("添加任务进展", False, "没有可测试的任务ID")
            return
            
        url = f"{BASE_URL}/tasks/{self.current_task_id}/progress"
        progress_data = {
            "content": f"测试进展记录 - {datetime.now().strftime('%H:%M:%S')}"
        }
        
        response = self.session.post(url, json=progress_data)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            self.log_result("添加任务进展", True, "成功添加任务进展记录")
        else:
            self.log_result("添加任务进展", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def search_tasks(self):
        """测试搜索任务API"""
        url = f"{BASE_URL}/search?q=测试"
        response = self.session.get(url)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            tasks = data.get("data", [])
            self.log_result("搜索任务", True, f"搜索'测试'成功找到{len(tasks)}个任务")
        else:
            self.log_result("搜索任务", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def get_task_stats(self):
        """测试获取任务统计API"""
        url = f"{BASE_URL}/stats/tasks"
        response = self.session.get(url)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            stats = data.get("data", {})
            self.log_result("获取任务统计", True, f"成功获取任务统计信息")
        else:
            self.log_result("获取任务统计", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def get_category_stats(self):
        """测试获取分类统计API"""
        url = f"{BASE_URL}/stats/categories"
        response = self.session.get(url)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            stats = data.get("data", {})
            self.log_result("获取分类统计", True, f"成功获取分类统计信息")
        else:
            self.log_result("获取分类统计", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def delete_task(self):
        """测试删除任务API"""
        if not self.current_task_id:
            self.log_result("删除任务", False, "没有可测试的任务ID")
            return
            
        url = f"{BASE_URL}/tasks/{self.current_task_id}"
        response = self.session.delete(url)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            self.log_result("删除任务", True, "成功删除测试任务")
            self.current_task_id = None
        else:
            self.log_result("删除任务", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def delete_category(self):
        """测试删除分类API"""
        url = f"{BASE_URL}/categories/{self.current_category_name}"
        response = self.session.delete(url)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            self.log_result("删除分类", True, "成功删除测试分类")
        else:
            self.log_result("删除分类", False, f"失败: HTTP {response.status_code}, {data.get('message', '未知错误')}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n===== DailyEnchant后端API测试开始 =====")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试API地址: {BASE_URL}")
        print("====================================")
        
        # 测试分类相关API
        self.run_test("创建分类", self.create_category)
        self.run_test("获取分类列表", self.get_categories)
        
        # 测试任务相关API
        self.run_test("创建任务", self.create_task)
        self.run_test("获取任务列表", self.get_tasks)
        self.run_test("获取单个任务", self.get_task)
        self.run_test("更新任务", self.update_task)
        self.run_test("更改任务状态", self.change_task_status)
        self.run_test("添加任务进展", self.add_task_progress)
        
        # 测试其他API
        self.run_test("搜索任务", self.search_tasks)
        self.run_test("获取任务统计", self.get_task_stats)
        self.run_test("获取分类统计", self.get_category_stats)
        
        # 清理测试数据
        self.run_test("删除任务", self.delete_task)
        self.run_test("删除分类", self.delete_category)
        
        print("====================================")
        
        # 统计测试结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"测试总结: 共{total_tests}项测试, 通过{passed_tests}项, 失败{failed_tests}项")
        
        if failed_tests > 0:
            print("\n失败的测试项:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"- {result['test_name']}: {result['message']}")
        
        # 保存测试结果到日志文件
        self.save_test_results()
        
        print("\n===== DailyEnchant后端API测试结束 =====")
    
    def save_test_results(self):
        """保存测试结果到日志文件"""
        try:
            log_file = "api_test_log.md"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"# DailyEnchant后端API测试日志\n\n")
                f.write(f"## 测试基本信息\n")
                f.write(f"- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"- 测试API地址: {BASE_URL}\n\n")
                
                f.write("## 测试结果\n")
                for result in self.test_results:
                    status = "✅ 通过" if result["success"] else "❌ 失败"
                    f.write(f"- {status} **{result['test_name']}**: {result['message']} ({result['timestamp']})\n")
                
                total_tests = len(self.test_results)
                passed_tests = sum(1 for r in self.test_results if r["success"])
                f.write(f"\n## 测试总结\n")
                f.write(f"- 共{total_tests}项测试\n")
                f.write(f"- 通过{passed_tests}项测试\n")
                f.write(f"- 失败{total_tests - passed_tests}项测试\n")
                
            print(f"\n测试结果已保存到: {log_file}")
        except Exception as e:
            print(f"保存测试结果失败: {str(e)}")

# 运行测试
if __name__ == "__main__":
    # 等待后端服务启动
    print("等待后端服务启动...")
    time.sleep(2)
    
    tester = APITester()
    tester.run_all_tests()