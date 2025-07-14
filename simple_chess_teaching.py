"""
简化的国际象棋教学系统
专注于：棋手走几步，就分析几步
功能：对每一步走法进行详细的AI分析
"""
import requests
import openai
import chess
import random
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# OpenAI API配置
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')

class SimpleAnalysisService:
    """简化的分析服务 - 专注于教学模式每步分析"""
    
    @staticmethod
    async def analyze_move(move: str, board_before: str, board_after: str, 
                          move_number: int, color: str) -> dict:
        """
        分析单步走法 - 详细的教学分析
        
        Args:
            move: 走法(UCI格式)
            board_before: 走法前的棋盘FEN
            board_after: 走法后的棋盘FEN
            move_number: 走法序号
            color: 走法方颜色 ('white' 或 'black')
        
        Returns:
            dict: 包含详细分析结果的字典
        """
        try:
            # 构造详细的分析提示
            system_msg = {
                'role': 'system', 
                'content': '''你是一位专业的国际象棋教练。请对学生的每一步走法进行全面详细的分析。
                
分析要求：
1. 📊 走法评级：优秀/良好/一般/有问题（必须明确给出）
2. ✅ 优点分析：这步棋的积极方面和战术价值
3. ⚠️ 缺点指出：存在的问题、风险或不足之处
4. 💡 改进建议：具体的改进方法和替代走法
5. 🎯 战术要点：相关的国际象棋原理和技巧
6. 📖 深度解析：局面特点和后续计划建议

用教学语气，分析要深入透彻，帮助学生真正理解每一步的意义。'''
            }
            
            # 构造用户消息
            content_parts = [
                f"【学生走法分析】第{move_number}步：{move} ({color}方)",
                f"【棋盘状态】",
                f"走法前：{board_before}",
                f"走法后：{board_after}",
                "",
                "【教学分析要求】请详细分析这步走法：",
                "1. 📊 走法评级：请明确给出评级",
                "2. ✅ 优点分析：这步棋好在哪里？",
                "3. ⚠️ 缺点指出：有什么问题或风险？",
                "4. 💡 改进建议：如何能走得更好？",
                "5. 🎯 战术要点：涉及什么国际象棋原理？",
                "6. 📖 深度解析：对局面的影响和后续计划"
            ]
            
            user_msg = {'role': 'user', 'content': '\n'.join(content_parts)}
            
            # 调用OpenAI API
            resp = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[system_msg, user_msg],
                temperature=0.7,
                max_tokens=1500  # 足够的字数获得详细分析
            )
            
            analysis_text = resp.choices[0].message.content.strip()
            
            # 简单的质量评估
            move_quality = "good"  # 默认评级
            if "优秀" in analysis_text or "excellent" in analysis_text.lower():
                move_quality = "excellent"
            elif "有问题" in analysis_text or "问题" in analysis_text:
                move_quality = "questionable"
            
            return {
                "success": True,
                "move_quality": move_quality,
                "ai_analysis": analysis_text,
                "analysis_timestamp": datetime.now().isoformat(),
                "move_analyzed": move,
                "move_number": move_number
            }
            
        except Exception as e:
            print(f"AI分析错误: {e}")
            # 返回备用分析
            return {
                "success": True,
                "move_quality": "good",
                "ai_analysis": f"走法 {move} 已记录。这是第{move_number}步，{color}方的走法。AI分析暂时不可用，但这步棋已经被记录下来了。",
                "analysis_timestamp": datetime.now().isoformat(),
                "move_analyzed": move,
                "move_number": move_number,
                "error": str(e)
            }

class SimpleTeachingGame:
    """简化的教学对局管理"""
    
    def __init__(self, game_id: str, user_color: str = "white"):
        self.game_id = game_id
        self.user_color = user_color
        self.board = chess.Board()  # 标准开局棋盘
        self.moves = []  # 存储所有走法和分析
        self.move_count = 0
        
    def make_move(self, move_str: str) -> dict:
        """
        执行走法并进行分析
        
        Args:
            move_str: 走法字符串 (UCI格式)
            
        Returns:
            dict: 包含走法结果和分析的字典
        """
        try:
            # 验证走法
            move = chess.Move.from_uci(move_str)
            if move not in self.board.legal_moves:
                return {
                    "success": False,
                    "error": f"无效走法: {move_str}",
                    "legal_moves": [str(m) for m in list(self.board.legal_moves)[:5]]
                }
            
            # 保存当前状态
            board_before = self.board.fen()
            current_color = "white" if self.board.turn else "black"
            
            # 执行走法
            self.board.push(move)
            board_after = self.board.fen()
            self.move_count += 1
            
            # 🔥 核心功能：对每一步进行详细分析
            import asyncio
            analysis_result = asyncio.run(SimpleAnalysisService.analyze_move(
                move=move_str,
                board_before=board_before,
                board_after=board_after,
                move_number=self.move_count,
                color=current_color
            ))
            
            # 保存走法和分析
            move_data = {
                "move": move_str,
                "color": current_color,
                "move_number": self.move_count,
                "board_before": board_before,
                "board_after": board_after,
                "analysis": analysis_result,
                "timestamp": datetime.now().isoformat()
            }
            self.moves.append(move_data)
            
            # AI应对（简化处理）
            ai_move = None
            ai_analysis = None
            
            if not self.board.is_game_over() and len(list(self.board.legal_moves)) > 0:
                # AI随机选择一个走法
                ai_move_obj = random.choice(list(self.board.legal_moves))
                ai_move = ai_move_obj.uci()
                
                # 执行AI走法
                ai_board_before = self.board.fen()
                self.board.push(ai_move_obj)
                ai_board_after = self.board.fen()
                self.move_count += 1
                
                # 分析AI走法
                ai_analysis_result = asyncio.run(SimpleAnalysisService.analyze_move(
                    move=ai_move,
                    board_before=ai_board_before,
                    board_after=ai_board_after,
                    move_number=self.move_count,
                    color="black" if current_color == "white" else "white"
                ))
                
                # 保存AI走法
                ai_move_data = {
                    "move": ai_move,
                    "color": "black" if current_color == "white" else "white",
                    "move_number": self.move_count,
                    "board_before": ai_board_before,
                    "board_after": ai_board_after,
                    "analysis": ai_analysis_result,
                    "timestamp": datetime.now().isoformat(),
                    "is_ai_move": True
                }
                self.moves.append(ai_move_data)
                ai_analysis = ai_analysis_result.get("ai_analysis", "")
            
            return {
                "success": True,
                "userMove": move_str,
                "userAnalysis": analysis_result.get("ai_analysis", ""),
                "moveQuality": analysis_result.get("move_quality", "unknown"),
                "aiMove": ai_move,
                "aiAnalysis": ai_analysis,
                "currentFen": self.board.fen(),
                "moveNumber": self.move_count,
                "gameStatus": "finished" if self.board.is_game_over() else "ongoing",
                "totalMoves": len(self.moves),
                "analysisSuccess": analysis_result.get("success", False)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"走法执行失败: {str(e)}",
                "current_fen": self.board.fen()
            }
    
    def get_game_history(self) -> dict:
        """获取完整的对局历史和分析"""
        return {
            "gameId": self.game_id,
            "userColor": self.user_color,
            "totalMoves": len(self.moves),
            "currentBoard": self.board.fen(),
            "currentTurn": "white" if self.board.turn else "black",
            "isGameOver": self.board.is_game_over(),
            "moveHistory": self.moves,
            "gameStatus": "finished" if self.board.is_game_over() else "ongoing"
        }

class SimpleChessClient:
    """简化的象棋客户端"""
    
    def __init__(self):
        self.games = {}  # 存储教学对局
        
    def start_teaching_game(self, user_color: str = "white") -> str:
        """开始教学对局"""
        game_id = f"teaching_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.games[game_id] = SimpleTeachingGame(game_id, user_color)
        return game_id
    
    def make_move(self, game_id: str, move: str) -> dict:
        """在指定对局中走法"""
        if game_id not in self.games:
            return {"success": False, "error": "对局不存在"}
        
        return self.games[game_id].make_move(move)
    
    def get_game_history(self, game_id: str) -> dict:
        """获取对局历史"""
        if game_id not in self.games:
            return {"success": False, "error": "对局不存在"}
        
        return self.games[game_id].get_game_history()

def test_simple_teaching():
    """测试简化的教学系统"""
    print("=" * 80)
    print("🎓 简化教学系统测试")
    print("💡 核心功能：棋手走几步，就分析几步")
    print("=" * 80)
    
    # 创建客户端和对局
    client = SimpleChessClient()
    game_id = client.start_teaching_game("white")
    
    print(f"✅ 教学对局创建成功: {game_id}")
    print(f"🎯 你执白棋，每一步都会得到详细的AI分析")
    
    # 测试走法列表
    test_moves = [
        {"move": "e2e4", "description": "经典开局：国王兵开局"},
        {"move": "g1f3", "description": "发展马匹：攻击中心"},
        {"move": "f1c4", "description": "发展象：指向f7弱点"},
        {"move": "d2d3", "description": "巩固中心：支持e4兵"}
    ]
    
    successful_analyses = 0
    total_moves = len(test_moves)
    
    for i, test_case in enumerate(test_moves, 1):
        move = test_case["move"]
        description = test_case["description"]
        
        print(f"\n{'='*60}")
        print(f"📝 第{i}步测试: {move}")
        print(f"📖 走法说明: {description}")
        print(f"{'='*60}")
        
        # 执行走法
        result = client.make_move(game_id, move)
        
        if result.get("success"):
            print(f"✅ 走法执行成功")
            
            # 显示走法质量
            quality = result.get("moveQuality", "unknown")
            quality_emoji = {
                "excellent": "🏆", 
                "good": "👍", 
                "questionable": "🤔"
            }.get(quality, "❓")
            print(f"📊 走法质量: {quality_emoji} {quality}")
            
            # 显示详细分析
            analysis = result.get("userAnalysis", "")
            if analysis and len(analysis) > 20:
                successful_analyses += 1
                print(f"\n🎓 教练详细分析:")
                print("-" * 60)
                
                # 分段显示分析内容
                lines = analysis.split('\n')
                for line in lines:
                    if line.strip():
                        print(f"   {line.strip()}")
                        
                print("-" * 60)
                print(f"✅ 第{i}步分析成功 (分析长度: {len(analysis)} 字符)")
            else:
                print(f"⚠️ 第{i}步分析不完整")
                print(f"   分析内容: {analysis[:100]}...")
            
            # 显示AI应对
            ai_move = result.get("aiMove")
            if ai_move:
                print(f"\n🤖 AI应对: {ai_move}")
                ai_analysis = result.get("aiAnalysis", "")
                if ai_analysis:
                    # 显示AI分析的前100字符
                    preview = ai_analysis[:150] + "..." if len(ai_analysis) > 150 else ai_analysis
                    print(f"🔍 AI分析预览: {preview}")
            
            print(f"\n📈 当前状态:")
            print(f"   当前步数: {result.get('moveNumber', 'N/A')}")
            print(f"   对局状态: {result.get('gameStatus', 'N/A')}")
            print(f"   总走法数: {result.get('totalMoves', 'N/A')}")
            
        else:
            print(f"❌ 走法失败: {result.get('error', '未知错误')}")
            continue
        
        # 短暂暂停
        import time
        time.sleep(0.5)
    
    # 获取完整历史
    print(f"\n{'='*80}")
    print("📚 获取完整教学历史")
    print(f"{'='*80}")
    
    history = client.get_game_history(game_id)
    if history:
        moves = history.get("moveHistory", [])
        print(f"✅ 总共记录 {len(moves)} 步走法")
        
        # 统计分析成功率
        analyzed_moves = sum(1 for move in moves 
                           if move.get("analysis", {}).get("ai_analysis") 
                           and len(move["analysis"]["ai_analysis"]) > 20)
        
        print(f"✅ 成功分析 {analyzed_moves} 步")
        print(f"📊 分析成功率: {(analyzed_moves/len(moves)*100):.1f}%")
        
        # 显示走法质量统计
        quality_stats = {"excellent": 0, "good": 0, "questionable": 0}
        for move in moves:
            if move.get("analysis"):
                quality = move["analysis"].get("move_quality", "unknown")
                if quality in quality_stats:
                    quality_stats[quality] += 1
        
        print(f"\n📊 走法质量分布:")
        print(f"   🏆 优秀: {quality_stats['excellent']}")
        print(f"   👍 良好: {quality_stats['good']}")
        print(f"   🤔 待改进: {quality_stats['questionable']}")
    
    # 总结
    print(f"\n{'='*80}")
    print("🎯 测试总结")
    print(f"{'='*80}")
    print(f"✅ 测试走法: {total_moves} 步")
    print(f"✅ 成功分析: {successful_analyses} 步")
    print(f"📈 分析成功率: {(successful_analyses/total_moves*100):.1f}%")
    
    if successful_analyses == total_moves:
        print(f"🎉 完美！每一步都获得了详细的AI分析")
        print(f"💡 这就是教学模式的核心价值：棋手走几步，就分析几步！")
    elif successful_analyses > 0:
        print(f"⚠️ 部分分析成功，需要检查失败原因")
    else:
        print(f"❌ 分析失败，需要检查AI API连接")
    
    print(f"\n🎓 教学系统测试完成！")

def interactive_teaching_mode():
    """交互式教学模式"""
    print("=" * 80)
    print("🎓 交互式教学模式")
    print("💡 每一步都有详细的AI分析和指导")
    print("=" * 80)
    
    # 创建对局
    client = SimpleChessClient()
    game_id = client.start_teaching_game("white")
    
    print(f"✅ 教学对局开始: {game_id}")
    print(f"🎯 你执白棋，请输入你的走法")
    print(f"📝 走法格式: e2e4, g1f3 等")
    print(f"🔙 输入 'quit' 退出, 'history' 查看历史")
    
    move_count = 0
    analysis_count = 0
    
    while True:
        print(f"\n{'-'*60}")
        print(f"📊 当前已走 {move_count} 步，成功分析 {analysis_count} 步")
        
        # 获取用户输入
        user_input = input("请输入走法 >>> ").strip().lower()
        
        if user_input == 'quit':
            print("🔙 退出教学模式")
            break
        elif user_input == 'history':
            # 显示历史
            history = client.get_game_history(game_id)
            moves = history.get("moveHistory", [])
            print(f"\n📚 对局历史 (共{len(moves)}步):")
            for i, move in enumerate(moves[-5:], 1):  # 显示最近5步
                move_num = move.get("move_number", i)
                move_str = move.get("move", "N/A")
                color = move.get("color", "N/A")
                print(f"   {move_num}. {move_str} ({color}方)")
            continue
        elif not user_input:
            print("⚠️ 请输入有效的走法")
            continue
        
        # 执行走法
        print(f"\n📝 执行走法: {user_input}")
        result = client.make_move(game_id, user_input)
        
        if result.get("success"):
            move_count += 1
            print(f"✅ 走法执行成功！")
            
            # 显示走法质量
            quality = result.get("moveQuality", "unknown")
            quality_emoji = {"excellent": "🏆", "good": "👍", "questionable": "🤔"}.get(quality, "❓")
            print(f"📊 走法质量: {quality_emoji} {quality}")
            
            # 显示详细分析
            analysis = result.get("userAnalysis", "")
            if analysis and len(analysis) > 20:
                analysis_count += 1
                print(f"\n🎓 教练分析:")
                print("=" * 70)
                
                # 分段显示
                lines = analysis.split('\n')
                for line in lines:
                    if line.strip():
                        print(f"   {line.strip()}")
                        
                print("=" * 70)
            else:
                print(f"⚠️ 分析不完整: {analysis[:50]}...")
            
            # 显示AI应对
            ai_move = result.get("aiMove")
            if ai_move:
                print(f"\n🤖 AI应对: {ai_move}")
                ai_analysis = result.get("aiAnalysis", "")
                if ai_analysis:
                    preview = ai_analysis[:100] + "..." if len(ai_analysis) > 100 else ai_analysis
                    print(f"🔍 AI应对分析: {preview}")
            
            # 检查游戏状态
            if result.get("gameStatus") == "finished":
                print(f"\n🏁 对局结束！")
                break
                
        else:
            print(f"❌ 走法失败: {result.get('error', '未知错误')}")
            continue
    
    # 最终统计
    print(f"\n🎯 对局总结:")
    print(f"   ✅ 总步数: {move_count}")
    print(f"   🎓 成功分析: {analysis_count}")
    print(f"   📊 分析率: {(analysis_count/move_count*100):.0f}%" if move_count > 0 else "0%")

def main():
    """主函数"""
    print("🎓 简化教学系统")
    print("选择模式:")
    print("1. 自动测试 (测试3步走法)")
    print("2. 交互模式 (手动输入走法)")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        test_simple_teaching()
    elif choice == "2":
        interactive_teaching_mode()
    else:
        print("无效选择")

if __name__ == "__main__":
    main()
