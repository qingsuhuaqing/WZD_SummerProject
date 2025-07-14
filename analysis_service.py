import openai
import os
import json
from dao import ChessDB
from fisher import StockfishEngine  # 导入Stockfish引擎
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置OpenAI API配置
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')

class AnalysisService:
    # 添加Stockfish引擎实例作为类属性
    stockfish_engine = None
    
    @classmethod
    async def initialize_stockfish(cls, stockfish_path: str):
        """初始化Stockfish引擎"""
        if cls.stockfish_engine is None:
            cls.stockfish_engine = StockfishEngine(stockfish_path)
            await cls.stockfish_engine._ensure_engine_running()
    
    @classmethod
    async def analyze_move(cls, user_move: str, board_before: str, board_after: str, 
                          move_number: int, color: str, game_context: dict = None) -> dict:
        """
        分析单步走法 - 在教学模式下进行详细分析
        
        Args:
            user_move: 用户走法(UCI格式)
            board_before: 走法前的棋盘FEN
            board_after: 走法后的棋盘FEN
            move_number: 走法序号
            color: 走法方颜色 ('white' 或 'black')
            game_context: 游戏上下文信息
        
        Returns:
            dict: 包含分析结果的字典
        """
        try:
            # 判断是否为教学模式
            is_teaching_mode = game_context and game_context.get("mode") == "teaching"
            
            # 获取Stockfish推荐走法
            stockfish_moves = []
            if cls.stockfish_engine:
                try:
                    stockfish_moves = await cls.stockfish_engine.get_best_moves(board_before, num_moves=3)
                except Exception as e:
                    print(f"Stockfish分析错误: {e}")
                    stockfish_moves = []
            
            # 分析走法质量
            move_quality = cls._evaluate_move_quality(user_move, stockfish_moves)
            
            # 在教学模式下进行详细AI分析
            if is_teaching_mode:
                try:
                    analysis_text = await cls._get_ai_analysis(
                        user_move, board_before, board_after, move_number, 
                        color, stockfish_moves, game_context
                    )
                except Exception as e:
                    print(f"AI分析错误: {e}")
                    analysis_text = f"走法 {user_move} 已记录，分析暂时不可用"
            else:
                # 非教学模式：返回简化分析
                analysis_text = cls._get_simple_analysis(user_move, stockfish_moves, move_quality)
            
            return {
                "success": True,
                "move_quality": move_quality,
                "ai_analysis": analysis_text,
                "stockfish_recommendations": stockfish_moves,
                "analysis_timestamp": "now",
                "is_teaching_mode": is_teaching_mode
            }
            
        except Exception as e:
            print(f"分析过程出错: {e}")
            return {
                "success": False,
                "error": f"走法分析失败: {str(e)}",
                "move_quality": "unknown",
                "ai_analysis": f"走法 {user_move} 已记录，分析失败",
                "stockfish_recommendations": [],
                "is_teaching_mode": game_context and game_context.get("mode") == "teaching" if game_context else False
            }
    
    @classmethod
    def _evaluate_move_quality(cls, user_move: str, stockfish_moves: list) -> str:
        """评估走法质量"""
        if not stockfish_moves:
            return "good"
        
        # 如果是Stockfish的最佳推荐
        if user_move in stockfish_moves[:1]:
            return "excellent"
        # 如果在前三推荐中
        elif user_move in stockfish_moves[:3]:
            return "good"
        else:
            return "questionable"
    
    @classmethod
    def _get_simple_analysis(cls, user_move: str, stockfish_moves: list, move_quality: str) -> str:
        """获取简化分析结果（非教学模式）"""
        if move_quality == "excellent":
            return f"走法 {user_move} 是优秀选择，符合引擎最佳推荐"
        elif move_quality == "good":
            return f"走法 {user_move} 是良好选择，在引擎推荐范围内"
        else:
            return f"走法 {user_move} 已记录"
    
    @classmethod
    async def _get_ai_analysis(cls, user_move: str, board_before: str, board_after: str,
                              move_number: int, color: str, stockfish_moves: list, 
                              game_context: dict = None) -> str:
        """获取AI分析（教学模式下的详细分析）"""
        # 判断是否为AI走法
        is_ai_move = game_context and game_context.get("is_ai_move", False)
        
        # 根据是否为AI走法调整系统消息
        if is_ai_move:
            system_msg = {
                'role': 'system', 
                'content': '你是一位专业的国际象棋教练。请详细分析AI的走法，向学生解释AI的战术思路、战略目的和这步棋的深层意图。内容要详细、具体、有教育价值。'
            }
        else:
            system_msg = {
                'role': 'system', 
                'content': '你是一位专业的国际象棋教练。请对学生的走法进行全面详细的分析，包括走法评级、优点、缺点、改进建议、战术要点等。用教学语气，分析要深入透彻。'
            }
        
        # 构造用户消息内容
        move_type = "AI走法" if is_ai_move else "学生走法"
        content_parts = [
            f"【{move_type}分析】第{move_number}步：{user_move} ({color}方)",
            f"【棋盘状态】",
            f"走法前：{board_before}",
            f"走法后：{board_after}"
        ]
        
        if stockfish_moves:
            content_parts.append(f"【引擎推荐】Stockfish最佳推荐：{', '.join(stockfish_moves[:3])}")
            # 判断走法质量
            if user_move in stockfish_moves[:1]:
                content_parts.append("✅ 此走法是引擎最佳推荐")
            elif user_move in stockfish_moves[:3]:
                content_parts.append("👍 此走法在引擎前三推荐中")
            else:
                content_parts.append("🤔 此走法不在引擎前三推荐中，可能有改进空间")
        
        if is_ai_move:
            content_parts.extend([
                "",
                "【教学分析要求】请详细分析AI走法：",
                "1. 📋 AI走法评级：优秀/良好/一般/有问题",
                "2. 🎯 战术目的：这步棋的具体战术意图是什么？",
                "3. 📈 战略价值：对整个局面的长远影响", 
                "4. 🧠 思维过程：AI可能的考虑和计算",
                "5. 📚 学习要点：学生可以从中学到什么原理",
                "6. 🔮 后续发展：接下来可能的走法和计划"
            ])
        else:
            content_parts.extend([
                "",
                "【教学分析要求】请全面分析学生走法：",
                "1. 📊 走法评级：优秀/良好/一般/有问题（必须明确给出）",
                "2. ✅ 优点分析：这步棋的积极方面和战术价值",
                "3. ⚠️ 缺点指出：存在的问题、风险或不足之处",
                "4. 💡 改进建议：具体的改进方法和替代走法",
                "5. 🎯 战术要点：相关的国际象棋原理和技巧",
                "6. 📖 深度解析：局面特点和后续计划建议"
            ])
        
        user_msg = {'role': 'user', 'content': '\n'.join(content_parts)}
        
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[system_msg, user_msg],
                temperature=0.7,
                max_tokens=1200  # 增加字数限制以获得更详细的分析
            )
            return resp.choices[0].message.content.strip()
        except Exception as ex:
            error_msg = f"OpenAI API调用失败: {str(ex)}"
            print(error_msg)
            # 返回备用分析而不是抛出异常
            return f"走法 {user_move} 已记录。AI分析暂时不可用，请稍后重试。"

    @classmethod
    async def analyze_teaching_move(cls, lesson_id: str, user_move: str, board_state: str, 
                                   objectives: list, hints: list = None, ai_move: str = None, 
                                   prev_moves: list = None) -> str:
        """教学模式下分析用户单步走子，返回AI点评"""
        # 使用通用分析方法，但添加教学上下文
        game_context = {
            'is_teaching_mode': True,
            'lesson_id': lesson_id,
            'objectives': objectives,
            'hints': hints or []
        }
        
        # 调用通用分析方法
        analysis_result = await cls.analyze_move(
            user_move=user_move,
            board_before=board_state,
            board_after=board_state,  # 简化处理
            move_number=len(prev_moves) + 1 if prev_moves else 1,
            color="white",  # 简化处理
            game_context=game_context
        )
        
        if analysis_result.get("success"):
            return analysis_result.get("ai_analysis", "分析完成")
        else:
            raise RuntimeError(analysis_result.get("error", "教学分析失败"))

    @classmethod
    async def analyze_game(cls, game_id: int) -> str:
        """分析棋局并返回AI生成的报告"""
        db = ChessDB()
        try:
            # 获取 PGN 和走子记录
            pgn_data = db.get_pgn_data(game_id)
            moves = db.get_game_moves(game_id)
            if not pgn_data or not moves:
                raise ValueError('Incomplete game data')

            # 解析headers
            headers = json.loads(pgn_data.headers) if pgn_data.headers else {}

            # 获取关键局面的Stockfish分析
            key_positions = []
            for i, move in enumerate(moves):
                if i % 5 == 0 or i == len(moves) - 1:  # 每5步分析一次
                    if cls.stockfish_engine:
                        best_moves = await cls.stockfish_engine.get_best_moves(move.fen_before, num_moves=2)
                        key_positions.append({
                            "move_number": move.move_number,
                            "position": move.fen_before,
                            "player_move": move.move_notation,
                            "stockfish_recommendations": best_moves
                        })

            # 系统和用户消息构造
            system_msg = {'role': 'system', 'content': '你是一位国际象棋教练，擅长解读棋谱并分析选手走法优劣。'}
            moves_list = '\n'.join([
                f"{m.move_number}.{m.ply_number} {m.move_notation} ({m.color})"
                for m in moves
            ])
            
            key_analysis = "\n".join([
                f"第{pos['move_number']}步: 玩家走法={pos['player_move']}, Stockfish推荐={', '.join(pos['stockfish_recommendations'])}"
                for pos in key_positions
            ]) if key_positions else "无关键局面分析"
            
            user_content = (
                f"请分析以下棋局（ID={game_id}）：\n"
                f"【PGN 头信息】 {headers}\n"
                f"【完整 PGN】\n{pgn_data.pgn_text}\n"
                f"【走子列表】\n{moves_list}\n\n"
                f"【关键局面分析】\n{key_analysis}"
            )
            user_msg = {'role': 'user', 'content': user_content}

            # 调用 OpenAI
            try:
                resp = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[system_msg, user_msg],
                    temperature=0.7,
                    max_tokens=1500
                )
                return resp.choices[0].message.content.strip()
            except Exception as ex:
                raise RuntimeError(f"OpenAI API error: {str(ex)}")
        finally:
            db.close()