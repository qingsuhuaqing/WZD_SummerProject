#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国际象棋个性化教学服务测试脚本

测试功能：
1. 用户技能分析
2. 个性化学习计划生成 
3. 个性化教学课程生成
4. API端点测试

使用说明：
1. 确保服务器运行在 http://localhost:8000
2. 确保数据库中有测试用户和棋局数据
3. 运行脚本进行自动化测试或交互式测试

作者：Chess Backend Team
"""

import asyncio
import requests
import json
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from teaching_service import TeachingService
from dao import ChessDB
from fisher import StockfishEngine

class TeachingTestClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        
    def login(self, username="testuser", password="password123"):
        """登录获取token"""
        url = f"{self.base_url}/api/auth/login"
        data = {"username": username, "password": password}
        
        try:
            response = self.session.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                self.token = result.get("token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print(f"✅ 登录成功，用户：{username}")
                return True
            else:
                print(f"❌ 登录失败：{response.text}")
                return False
        except Exception as e:
            print(f"❌ 登录请求失败：{e}")
            return False
    
    def test_skill_analysis_api(self, username=None):
        """测试技能分析API"""
        print("\n" + "="*50)
        print("🧠 测试技能分析API")
        print("="*50)
        
        # 测试当前用户技能分析
        url = f"{self.base_url}/api/teaching/skills"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    data = result["data"]
                    print(f"✅ 当前用户技能分析成功")
                    print(f"   用户：{data['username']}")
                    print(f"   已掌握技能数：{data['mastered_skills_count']}/{data['total_skills_count']}")
                    print(f"   整体进度：{data['overall_progress']:.1%}")
                    
                    print("\n📊 技能详情：")
                    for skill_id, skill_data in data["skill_analysis"].items():
                        status = "✅ 已掌握" if skill_data["mastered"] else "❌ 需提升"
                        print(f"   {skill_data['name']}: {skill_data['score']:.2f} {status}")
                else:
                    print(f"❌ 技能分析失败：{result.get('error')}")
            else:
                print(f"❌ API请求失败：{response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ 请求异常：{e}")
        
        # 如果指定了用户名，测试指定用户的技能分析
        if username:
            print(f"\n🎯 测试指定用户({username})技能分析...")
            url = f"{self.base_url}/api/teaching/skills/{username}"
            try:
                response = self.session.get(url)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        data = result["data"]
                        print(f"✅ 用户 {username} 技能分析成功")
                        print(f"   整体进度：{data['overall_progress']:.1%}")
                    else:
                        print(f"❌ 用户 {username} 技能分析失败：{result.get('error')}")
                else:
                    print(f"❌ API请求失败：{response.status_code}")
            except Exception as e:
                print(f"❌ 请求异常：{e}")
    
    def test_learning_plan_api(self, username=None):
        """测试学习计划API"""
        print("\n" + "="*50)
        print("📚 测试个性化学习计划API")
        print("="*50)
        
        # 测试当前用户学习计划
        url = f"{self.base_url}/api/teaching/learning-plan"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    data = result["data"]
                    print(f"✅ 当前用户学习计划生成成功")
                    print(f"   用户：{data['username']}")
                    print(f"   已掌握技能：{', '.join(data['mastered_skills']) if data['mastered_skills'] else '暂无'}")
                    
                    if data["skills_to_improve"]:
                        print(f"\n🎯 需要提升的技能：")
                        for skill in data["skills_to_improve"][:3]:
                            print(f"   {skill['name']}: {skill['current_score']:.2f} → {skill['target_score']:.2f}")
                    
                    if data["learning_recommendations"]:
                        print(f"\n📖 学习建议：")
                        for i, rec in enumerate(data["learning_recommendations"], 1):
                            print(f"   {i}. {rec['skill_focus']}")
                            print(f"      预估学习时间：{rec.get('estimated_study_time', '未知')}")
                else:
                    print(f"❌ 学习计划生成失败：{result.get('error')}")
            else:
                print(f"❌ API请求失败：{response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ 请求异常：{e}")
    
    def test_personalized_lessons_api(self, lessons_count=2):
        """测试个性化课程生成API"""
        print("\n" + "="*50)
        print("🎓 测试个性化课程生成API")
        print("="*50)
        
        url = f"{self.base_url}/api/teaching/personalized-lessons"
        data = {"lessons_count": lessons_count}
        
        try:
            print(f"📝 正在生成 {lessons_count} 个个性化教学课程...")
            response = self.session.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    lesson_data = result["data"]
                    print(f"✅ 个性化课程生成成功")
                    print(f"   用户：{lesson_data['username']}")
                    print(f"   课程数量：{lesson_data['lessons_count']}")
                    print(f"   生成时间：{lesson_data['generated_at']}")
                    
                    print(f"\n📚 课程内容预览：")
                    lessons_text = lesson_data["lessons"]
                    # 显示前500个字符作为预览
                    preview = lessons_text[:500] + "..." if len(lessons_text) > 500 else lessons_text
                    print(f"   {preview}")
                else:
                    print(f"❌ 课程生成失败：{result.get('error')}")
            else:
                print(f"❌ API请求失败：{response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ 请求异常：{e}")
    
    def test_skill_definitions_api(self):
        """测试技能定义API"""
        print("\n" + "="*50)
        print("📋 测试技能定义API")
        print("="*50)
        
        url = f"{self.base_url}/api/teaching/skill-definitions"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    data = result["data"]
                    print(f"✅ 技能定义获取成功")
                    print(f"   总技能数：{data['total_skills']}")
                    
                    print(f"\n📊 技能定义列表：")
                    for skill_id, skill_def in data["skill_definitions"].items():
                        print(f"   {skill_def['name']} (掌握阈值: {skill_def['mastery_threshold']:.2f})")
                        print(f"      {skill_def['description']}")
                else:
                    print(f"❌ 获取技能定义失败：{result.get('error')}")
            else:
                print(f"❌ API请求失败：{response.status_code}")
        except Exception as e:
            print(f"❌ 请求异常：{e}")

async def test_teaching_service_direct():
    """直接测试TeachingService类方法"""
    print("\n" + "="*60)
    print("🔧 直接测试TeachingService类方法")
    print("="*60)
    
    # 初始化Stockfish引擎
    stockfish_path = r"D:\stockfish\stockfish-windows-x86-64-avx2.exe"
    if os.path.exists(stockfish_path):
        TeachingService.stockfish_engine = StockfishEngine(stockfish_path)
        await TeachingService.initialize_stockfish(stockfish_path)
        print("✅ Stockfish引擎初始化成功")
    else:
        print("⚠️  警告：Stockfish引擎路径不存在，部分功能可能受限")
    
    # 获取测试用户
    db = ChessDB()
    try:
        users = db.get_all_users()
        if not users:
            print("❌ 数据库中没有用户数据，请先运行 generate_test_data.py")
            return
        
        test_user = users[0]
        username = test_user.username
        print(f"🎯 使用测试用户：{username}")
        
        # 测试技能分析
        print(f"\n🧠 测试技能分析...")
        skill_result = await TeachingService.analyze_user_skills(username)
        if "error" not in skill_result:
            print(f"✅ 技能分析成功")
            print(f"   整体进度：{skill_result['overall_progress']:.1%}")
            print(f"   已掌握技能：{skill_result['mastered_skills_count']}/{skill_result['total_skills_count']}")
        else:
            print(f"❌ 技能分析失败：{skill_result['error']}")
        
        # 测试学习计划生成
        print(f"\n📚 测试学习计划生成...")
        plan_result = await TeachingService.get_personalized_learning_plan(username)
        if "error" not in plan_result:
            print(f"✅ 学习计划生成成功")
            print(f"   需要提升的技能数：{len(plan_result['skills_to_improve'])}")
            if plan_result["learning_recommendations"]:
                print(f"   学习建议数：{len(plan_result['learning_recommendations'])}")
        else:
            print(f"❌ 学习计划生成失败：{plan_result['error']}")
        
        # 测试个性化课程生成
        print(f"\n🎓 测试个性化课程生成...")
        try:
            lessons = await TeachingService.generate_lessons(username, 2)
            print(f"✅ 个性化课程生成成功")
            print(f"   课程长度：{len(lessons)} 字符")
            # 显示课程内容的前200个字符
            preview = lessons[:200] + "..." if len(lessons) > 200 else lessons
            print(f"   内容预览：{preview}")
        except Exception as e:
            print(f"❌ 个性化课程生成失败：{e}")
            
    finally:
        db.close()

def run_interactive_test():
    """运行交互式测试"""
    print("🎮 欢迎使用国际象棋个性化教学测试工具")
    print("="*60)
    
    client = TeachingTestClient()
    
    # 登录
    username = input("请输入用户名 (默认: testuser): ").strip() or "testuser"
    password = input("请输入密码 (默认: password123): ").strip() or "password123"
    
    if not client.login(username, password):
        print("❌ 登录失败，无法继续测试")
        return
    
    while True:
        print("\n" + "="*40)
        print("请选择测试项目：")
        print("1. 技能分析API测试")
        print("2. 学习计划API测试")
        print("3. 个性化课程生成API测试")
        print("4. 技能定义API测试")
        print("5. 运行所有API测试")
        print("6. 直接测试服务类方法")
        print("0. 退出")
        print("="*40)
        
        choice = input("请输入选择 (0-6): ").strip()
        
        if choice == "1":
            test_username = input("请输入要分析的用户名 (留空使用当前用户): ").strip() or None
            client.test_skill_analysis_api(test_username)
        elif choice == "2":
            client.test_learning_plan_api()
        elif choice == "3":
            lessons_count = input("请输入课程数量 (默认: 2): ").strip()
            try:
                lessons_count = int(lessons_count) if lessons_count else 2
            except ValueError:
                lessons_count = 2
            client.test_personalized_lessons_api(lessons_count)
        elif choice == "4":
            client.test_skill_definitions_api()
        elif choice == "5":
            client.test_skill_definitions_api()
            client.test_skill_analysis_api()
            client.test_learning_plan_api()
            client.test_personalized_lessons_api(2)
        elif choice == "6":
            print("🔧 运行直接服务测试...")
            asyncio.run(test_teaching_service_direct())
        elif choice == "0":
            print("👋 感谢使用，再见！")
            break
        else:
            print("❌ 无效选择，请重新输入")

def run_automated_test():
    """运行自动化测试"""
    print("🤖 运行自动化测试")
    print("="*60)
    
    client = TeachingTestClient()
    
    # 自动登录
    if not client.login("testuser", "password123"):
        print("❌ 自动登录失败，尝试其他用户...")
        # 尝试数据库中的第一个用户
        db = ChessDB()
        try:
            users = db.get_all_users()
            if users:
                test_user = users[0]
                if not client.login(test_user.username, "password123"):
                    print("❌ 所有登录尝试失败")
                    return
            else:
                print("❌ 数据库中没有用户，请先运行 generate_test_data.py")
                return
        finally:
            db.close()
    
    # 运行所有测试
    client.test_skill_definitions_api()
    client.test_skill_analysis_api()
    client.test_learning_plan_api()
    client.test_personalized_lessons_api(2)
    
    # 运行直接服务测试
    print("\n🔧 运行直接服务测试...")
    asyncio.run(test_teaching_service_direct())
    
    print("\n✅ 自动化测试完成！")

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        run_automated_test()
    else:
        run_interactive_test()

if __name__ == "__main__":
    main()
