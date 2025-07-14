"""
竞技分析服务测试文件
===================

测试 CompetitionService 的用户分析功能，包括：
1. 基于历史棋局的玩家风格分析
2. 技术水平评估
3. 改进建议生成

使用方法：
python competition_test.py
"""

import asyncio
import requests
import json
from datetime import datetime
from competition_service import CompetitionService
from dao import ChessDB

# API服务器配置
BASE_URL = "http://127.0.0.1:8000"

class CompetitionAnalysisTest:
    def __init__(self):
        self.token = None
        self.username = None
        self.session = requests.Session()
    
    def _headers(self):
        """获取请求头"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    def _request(self, method, endpoint, **kwargs):
        """统一请求方法"""
        url = f"{BASE_URL}{endpoint}"
        kwargs.setdefault('headers', {}).update(self._headers())
        
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            return None

    # ==================== 认证相关 ====================
    
    def auto_auth(self, username="test_player", password="password123"):
        """自动认证（先登录，失败则注册）"""
        print(f"🔐 自动认证用户: {username}")
        
        # 先尝试登录
        data = {"username": username, "password": password}
        response = self._request('POST', '/api/auth/login', json=data)
        
        if response and response.status_code == 200:
            result = response.json()
            self.token = result.get('token')
            self.username = username
            print(f"✅ 登录成功！")
            return True
        
        # 登录失败则注册
        print("登录失败，尝试注册新用户...")
        response = self._request('POST', '/api/auth/register', json=data)
        
        if response and response.status_code == 201:
            result = response.json()
            self.token = result.get('token')
            self.username = username
            print(f"✅ 注册成功！")
            return True
        else:
            print(f"❌ 认证失败: {response.text if response else '无响应'}")
            return False

    # ==================== 直接服务测试 ====================
    
    async def test_direct_analysis(self, username="test_player"):
        """直接测试 CompetitionService 的分析功能"""
        print(f"\n{'='*60}")
        print("🔬 直接服务测试：用户风格分析")
        print(f"{'='*60}")
        
        try:
            print(f"📊 分析用户: {username}")
            
            # 调用分析服务
            analysis_result = await CompetitionService.analyze_player_style(username)
            
            if analysis_result["success"]:
                print(f"✅ 分析成功！")
                
                # 显示基础统计
                stats = analysis_result["player_stats"]
                print(f"\n📈 基础统计:")
                print(f"   总对局数: {stats['total_games']}")
                print(f"   胜局: {stats['wins']}")
                print(f"   败局: {stats['losses']}")
                print(f"   平局: {stats['draws']}")
                print(f"   胜率: {stats['winning_rate']:.1f}%")
                print(f"   ELO评分: {stats['elo_rating']}")
                
                # 显示游戏分析数据
                game_analysis = analysis_result["game_analysis"]
                print(f"\n🎯 游戏分析数据:")
                
                openings = game_analysis.get("opening_preferences", {})
                if openings:
                    print(f"   开局偏好: {len(openings)} 种不同开局")
                    for opening, count in list(openings.items())[:3]:
                        print(f"     - {opening}: {count}次")
                
                strong_moves = game_analysis.get("strong_moves", [])
                mistakes = game_analysis.get("common_mistakes", [])
                print(f"   优秀走法: {len(strong_moves)} 个")
                print(f"   常见失误: {len(mistakes)} 个")
                
                opponents = game_analysis.get("opponent_analysis", {})
                print(f"   对战对手: {len(opponents)} 人")
                
                # 显示AI分析报告
                ai_analysis = analysis_result["ai_analysis"]
                print(f"\n🤖 AI分析报告:")
                print("=" * 50)
                
                # 分段显示分析内容
                analysis_lines = ai_analysis.split('\n')
                for line in analysis_lines:
                    if line.strip():
                        print(f"   {line.strip()}")
                
                print("=" * 50)
                print(f"✨ 分析完成！时间: {analysis_result['analysis_timestamp']}")
                
            else:
                print(f"❌ 分析失败: {analysis_result.get('error', analysis_result.get('message'))}")
                
        except Exception as e:
            print(f"❌ 直接测试失败: {e}")
    
    # ==================== API测试 ====================
    
    def test_api_analysis(self):
        """测试API端点的分析功能"""
        print(f"\n{'='*60}")
        print("🌐 API测试：用户分析端点")
        print(f"{'='*60}")
        
        # 测试当前用户分析
        print(f"\n📡 测试当前用户分析: GET /api/user/analysis")
        response = self._request('GET', '/api/user/analysis')
        
        if response and response.status_code == 200:
            result = response.json()
            if result["success"]:
                analysis = result["analysis"]
                stats = analysis["player_stats"]
                
                print(f"✅ API调用成功！")
                print(f"   用户: {analysis['username']}")
                print(f"   总对局: {stats['total_games']}")
                print(f"   胜率: {stats['winning_rate']:.1f}%")
                print(f"   ELO: {stats['elo_rating']}")
                
                # 显示AI分析的前几行
                ai_analysis = analysis["ai_analysis"]
                preview_lines = ai_analysis.split('\n')[:5]
                print(f"\n🤖 AI分析预览:")
                for line in preview_lines:
                    if line.strip():
                        print(f"   {line.strip()}")
                print("   ...")
            else:
                print(f"❌ API返回失败: {result.get('error')}")
        else:
            print(f"❌ API调用失败: {response.status_code if response else '无响应'}")
            if response:
                print(f"   错误信息: {response.text}")
        
        # 测试指定用户分析
        print(f"\n📡 测试指定用户分析: GET /api/user/analysis/{self.username}")
        response = self._request('GET', f'/api/user/analysis/{self.username}')
        
        if response and response.status_code == 200:
            result = response.json()
            print(f"✅ 指定用户分析API调用成功！")
        else:
            print(f"❌ 指定用户分析API调用失败: {response.status_code if response else '无响应'}")

    # ==================== 数据库状态检查 ====================
    
    def check_database_status(self):
        """检查数据库中的用户和游戏数据"""
        print(f"\n{'='*60}")
        print("💾 数据库状态检查")
        print(f"{'='*60}")
        
        try:
            db = ChessDB()
            
            # 检查用户数据
            user = db.get_user_by_username(self.username)
            if user:
                print(f"✅ 用户数据存在:")
                print(f"   用户名: {user.username}")
                print(f"   总对局: {user.total_games}")
                print(f"   胜率: {user.winning_rate:.1f}%")
                print(f"   ELO: {user.elo_rating}")
                
                # 检查游戏数据
                games = db.get_user_games(self.username)
                print(f"\n🎮 游戏历史:")
                print(f"   历史对局数: {len(games)}")
                
                if games:
                    print(f"   最近5局:")
                    for i, game in enumerate(games[-5:], 1):
                        opponent = game.player2.username if game.player1_id == user.user_id else game.player1.username
                        result = game.result or "进行中"
                        print(f"     {i}. vs {opponent} - {result}")
                        
                        # 检查走法数据
                        moves = db.get_game_moves(game.game_id)
                        print(f"        走法数: {len(moves)}")
                else:
                    print(f"   📝 提示: 用户暂无游戏记录，建议先进行几局对弈以获得更好的分析效果")
            else:
                print(f"❌ 用户数据不存在")
            
            db.close()
            
        except Exception as e:
            print(f"❌ 数据库检查失败: {e}")

    # ==================== 完整测试流程 ====================
    
    async def run_full_test(self):
        """运行完整的测试流程"""
        print("🚀 竞技分析服务完整测试")
        print("=" * 60)
        
        # 1. 用户认证
        if not self.auto_auth():
            print("❌ 认证失败，测试中止")
            return
        
        # 2. 检查数据库状态
        self.check_database_status()
        
        # 3. 直接服务测试
        await self.test_direct_analysis(self.username)
        
        # 4. API测试
        self.test_api_analysis()
        
        print(f"\n🎉 测试完成！")
        print(f"💡 提示: 如果用户游戏数据较少，建议先使用 test_end.py 或 chess_game_test.py 进行几局对弈")

    # ==================== 交互式测试 ====================
    
    def interactive_test(self):
        """交互式测试菜单"""
        while True:
            print(f"\n{'='*50}")
            print("🎯 竞技分析测试菜单")
            print(f"当前用户: {self.username or '未登录'}")
            print(f"{'='*50}")
            print("1. 🔐 用户认证")
            print("2. 💾 检查数据库状态")
            print("3. 🔬 直接服务测试")
            print("4. 🌐 API端点测试")
            print("5. 🚀 完整测试流程")
            print("6. 🚪 退出")
            
            choice = input("\n请选择功能 (1-6): ").strip()
            
            if choice == "1":
                username = input("用户名 (默认test_player): ").strip() or "test_player"
                password = input("密码 (默认password123): ").strip() or "password123"
                self.auto_auth(username, password)
            elif choice == "2":
                if self.check_auth():
                    self.check_database_status()
            elif choice == "3":
                if self.check_auth():
                    username = input(f"分析用户名 (默认{self.username}): ").strip() or self.username
                    asyncio.run(self.test_direct_analysis(username))
            elif choice == "4":
                if self.check_auth():
                    self.test_api_analysis()
            elif choice == "5":
                if self.check_auth():
                    asyncio.run(self.run_full_test())
            elif choice == "6":
                print("👋 再见！")
                break
            else:
                print("❌ 无效选择，请重新输入")
    
    def check_auth(self):
        """检查是否已认证"""
        if not self.token:
            print("❌ 请先登录！")
            return False
        return True

# ==================== 主函数 ====================

def main():
    """主函数"""
    print("🎯 竞技分析服务测试工具")
    print("=" * 40)
    print("功能包括:")
    print("- 🔬 用户风格深度分析")
    print("- 📊 历史战绩数据挖掘")
    print("- 🤖 AI驱动的改进建议")
    print("- 🌐 API端点完整测试")
    print("=" * 40)
    
    # 检查后端连接
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ 后端连接正常")
        else:
            print("⚠️ 后端响应异常")
    except:
        print("❌ 无法连接到后端服务")
        print(f"请确保后端服务运行在: {BASE_URL}")
        return
    
    # 启动测试器
    tester = CompetitionAnalysisTest()
    
    # 选择模式
    print("\n选择测试模式:")
    print("1. 交互式菜单")
    print("2. 自动完整测试")
    
    mode = input("请选择 (1/2): ").strip()
    
    if mode == "1":
        tester.interactive_test()
    elif mode == "2":
        asyncio.run(tester.run_full_test())
    else:
        print("默认运行交互式菜单")
        tester.interactive_test()

if __name__ == "__main__":
    main()
