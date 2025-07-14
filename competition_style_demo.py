#!/usr/bin/env python3
"""
竞技模式个人风格分析演示脚本
=========================

演示如何使用竞技分析功能：
1. 用户风格分析
2. 技术水平评估  
3. 对局表现统计
4. 改进建议生成

使用方法：
python competition_style_demo.py
"""

import asyncio
import sys
import os
from datetime import datetime

# 导入必要的模块
try:
    from competition_service import CompetitionService
    from dao import ChessDB
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)

class CompetitionStyleDemo:
    """竞技风格分析演示类"""
    
    def __init__(self):
        self.db = ChessDB()
        print("🎯 竞技模式个人风格分析演示")
        print("=" * 50)
    
    def print_section(self, title):
        """打印章节标题"""
        print(f"\n{'='*20} {title} {'='*20}")
    
    async def demo_user_analysis(self, username):
        """演示用户风格分析"""
        self.print_section(f"分析用户: {username}")
        
        try:
            # 调用分析服务
            result = await CompetitionService.analyze_player_style(username)
            
            if result["success"]:
                analysis = result
                
                # 基本信息
                basic_info = analysis.get("basic_info", {})
                print(f"📊 基本信息:")
                print(f"   用户名: {basic_info.get('username', username)}")
                print(f"   总对局: {basic_info.get('total_games', 0)}局")
                print(f"   胜率: {basic_info.get('win_rate', 0):.1f}%")
                print(f"   评分: {basic_info.get('rating', 'N/A')}")
                
                # 棋风特征
                if "playing_style" in analysis:
                    style = analysis["playing_style"]
                    print(f"\n🎨 棋风特征:")
                    print(f"   主要风格: {style.get('primary_style', '未知')}")
                    print(f"   置信度: {style.get('style_confidence', 0)*100:.1f}%")
                    
                    if "style_breakdown" in style:
                        print(f"   详细分析:")
                        for aspect, score in style["style_breakdown"].items():
                            print(f"     {aspect}: {score}分")
                
                # 技术分析
                if "technical_analysis" in analysis:
                    tech = analysis["technical_analysis"]
                    print(f"\n⚙️ 技术分析:")
                    for phase, data in tech.items():
                        if isinstance(data, dict) and "score" in data:
                            print(f"   {phase}: {data['score']}分")
                            if "analysis" in data:
                                print(f"     {data['analysis']}")
                
                # 优势和劣势
                if "strengths" in analysis:
                    print(f"\n💪 技术优势:")
                    for strength in analysis["strengths"]:
                        print(f"   ✅ {strength}")
                
                if "weaknesses" in analysis:
                    print(f"\n⚠️ 需要改进:")
                    for weakness in analysis["weaknesses"]:
                        print(f"   🔸 {weakness}")
                
                # 改进建议
                if "recommendations" in analysis:
                    print(f"\n🎯 改进建议:")
                    for i, rec in enumerate(analysis["recommendations"], 1):
                        print(f"   {i}. {rec}")
                
                return True
                
            else:
                print(f"❌ 分析失败: {result.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"❌ 分析过程中出错: {e}")
            return False
    
    def list_available_users(self):
        """列出可用的用户"""
        try:
            users = self.db.get_all_users()
            if users:
                print(f"\n👥 数据库中的用户 (共{len(users)}个):")
                for i, user in enumerate(users[:10], 1):  # 只显示前10个
                    games_count = len(self.db.get_user_games(user.username))
                    print(f"   {i}. {user.username} (对局: {games_count})")
                if len(users) > 10:
                    print(f"   ... 还有{len(users)-10}个用户")
                return [user.username for user in users]
            else:
                print("❌ 数据库中没有用户数据")
                return []
        except Exception as e:
            print(f"❌ 获取用户列表失败: {e}")
            return []
    
    async def interactive_demo(self):
        """交互式演示"""
        print("🚀 欢迎使用竞技模式个人风格分析演示！")
        
        # 列出可用用户
        users = self.list_available_users()
        
        if not users:
            print("\n💡 建议先运行 generate_test_data.py 生成测试数据")
            return
        
        while True:
            print(f"\n" + "="*60)
            print("📋 请选择操作:")
            print("1. 分析指定用户")
            print("2. 分析所有用户 (批量)")
            print("3. 分析测试用户 test_player")
            print("4. 退出")
            
            choice = input("\n请输入选项 (1-4): ").strip()
            
            if choice == "1":
                username = input("请输入用户名: ").strip()
                if username:
                    await self.demo_user_analysis(username)
                else:
                    print("❌ 用户名不能为空")
            
            elif choice == "2":
                print("\n🔄 批量分析用户...")
                for username in users[:5]:  # 只分析前5个用户
                    success = await self.demo_user_analysis(username)
                    if not success:
                        break
                    print("\n" + "-"*40)
            
            elif choice == "3":
                await self.demo_user_analysis("test_player")
            
            elif choice == "4":
                print("👋 感谢使用！")
                break
            
            else:
                print("❌ 无效选择，请重新输入")
    
    async def quick_demo(self):
        """快速演示"""
        print("⚡ 快速演示模式")
        
        # 检查test_player是否存在
        test_user = self.db.get_user_by_username("test_player")
        if test_user:
            await self.demo_user_analysis("test_player")
        else:
            users = self.list_available_users()
            if users:
                print(f"\n🎯 使用第一个用户进行演示: {users[0]}")
                await self.demo_user_analysis(users[0])
            else:
                print("❌ 没有可用的用户数据")
                print("💡 请先运行: python generate_test_data.py")
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'db'):
            self.db.close()

async def main():
    """主函数"""
    demo = CompetitionStyleDemo()
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--quick":
            await demo.quick_demo()
        else:
            await demo.interactive_demo()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，退出演示")
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
    finally:
        demo.close()

if __name__ == "__main__":
    # 检查是否有测试数据
    print("🔍 检查测试环境...")
    
    try:
        db = ChessDB()
        users = db.get_all_users()
        if not users:
            print("⚠️  数据库中没有用户数据")
            print("💡 建议先运行: python generate_test_data.py")
            choice = input("是否继续演示? (y/N): ").strip().lower()
            if choice != 'y':
                print("👋 退出演示")
                sys.exit(0)
        db.close()
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
    
    # 运行演示
    asyncio.run(main())
