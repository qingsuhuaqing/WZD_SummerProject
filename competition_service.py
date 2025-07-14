import openai
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置OpenAI API配置
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
from dao import ChessDB
from fisher import StockfishEngine  # 导入Stockfish引擎
import asyncio
import chess
import chess.pgn
from typing import Optional, Dict, Any

class CompetitionService:
    
    # 添加Stockfish引擎实例作为类属性
    stockfish_engine = None
    
    @classmethod
    async def initialize_stockfish(cls, stockfish_path: str):
        """初始化Stockfish引擎"""
        if cls.stockfish_engine is None:
            cls.stockfish_engine = StockfishEngine(stockfish_path)
            await cls.stockfish_engine._ensure_engine_running()
    
    @classmethod
    async def summarize_player(cls, username: str) -> str:
        """总结玩家水平和风格"""
        db = ChessDB()
        try:
            user = db.get_user_by_username(username)
            if not user:
                raise ValueError('用户不存在')

            games = db.get_user_games(username)
            if not games:
                raise ValueError('该用户暂无棋局记录')

            # 获取最近一场比赛的详细分析
            latest_game = games[-1] if games else None
            game_analysis = ""
            if latest_game and cls.stockfish_engine:
                # 获取比赛关键步数的Stockfish分析
                moves = db.get_game_moves(latest_game.game_id)
                key_moves = []
                for move in moves:
                    best_moves = await cls.stockfish_engine.get_best_moves(move.fen_before, num_moves=1)
                    key_moves.append({
                        "move_number": move.move_number,
                        "player_move": move.move_notation,
                        "stockfish_recommendation": best_moves[0] if best_moves else "无推荐"
                    })
                
                game_analysis = "\n".join([
                    f"第{move['move_number']}步: 玩家走法={move['player_move']}, Stockfish推荐={move['stockfish_recommendation']}"
                    for move in key_moves
                ])

            summary_data = []
            for game in games:
                summary_data.append({
                    'game_id': game.game_id,
                    'result': game.result if game.result else 'unknown',
                    'opponent': game.player2.username if game.player1_id == user.user_id else game.player1.username
                })

            system_msg = {'role': 'system', 'content': '你是一名国际象棋数据分析师，擅长从历史对局评估棋手水平和风格。'}
            user_msg = {
                'role': 'user',
                'content': (
                    f"请基于用户 {username} (ELO: {user.elo_rating}) 的历史棋局数据，总结棋手的水平评分和风格特点。\n"
                    f"总对局数: {user.total_games}, 胜率: {user.winning_rate}%\n"
                    f"以下是棋局概览：\n{summary_data}\n\n"
                    f"【最近对局关键步分析】\n{game_analysis if game_analysis else '无分析数据'}"
                )
            }

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
    
    @classmethod        
    async def get_ai_move(cls, fen_string: str, difficulty_level: str = "medium", time_limit: float = None) -> Optional[str]:
        """
        获取AI的下一步走法
    
        Args:
            fen_string (str): 当前棋局的FEN字符串
            difficulty_level (str): 难度级别 ("easy", "medium", "hard")
            time_limit (float): 思考时间限制，如果为None则根据难度级别设置
        
        Returns:
            Optional[str]: AI推荐的走法（UCI格式），如果无法获取则返回None
        """
        if cls.stockfish_engine is None:
            raise RuntimeError("Stockfish引擎未初始化，请先调用initialize_stockfish方法")
        
        # 根据难度级别设置思考时间
        if time_limit is None:
            time_limits = {
                "easy": 0.1,    # 简单：0.1秒
                "medium": 0.5,  # 中等：0.5秒  
                "hard": 2.0     # 困难：2.0秒
            }
            time_limit = time_limits.get(difficulty_level, 0.5)
        
        try:
            best_moves = await cls.stockfish_engine.get_best_moves(
                fen_string, 
                num_moves=1, 
                time_limit=time_limit
            )
            return best_moves[0] if best_moves else None
        except Exception as e:
            print(f"获取AI走法时出错: {e}")
            return None
    
    @classmethod
    async def start_human_vs_ai_game(cls, player_username: str, player_color: str = "white", 
                                   difficulty_level: str = "medium") -> Dict[str, Any]:
        """
        开始人机对战游戏
        
        Args:
            player_username (str): 玩家用户名
            player_color (str): 玩家执子颜色 ("white" 或 "black")
            difficulty_level (str): AI难度级别 ("easy", "medium", "hard")
        
        Returns:
            Dict[str, Any]: 包含游戏信息的字典
        """
        db = ChessDB()
        try:
            # 验证用户是否存在
            user = db.get_user_by_username(player_username)
            if not user:
                raise ValueError('用户不存在')
            
            # 创建新游戏记录
            ai_username = f"AI_{difficulty_level.upper()}"
            
            if player_color.lower() == "white":
                player1_id = user.user_id
                player2_username = ai_username
            else:
                player1_username = ai_username  
                player2_id = user.user_id
            
            # 在数据库中创建游戏记录
            game_id = db.create_game(
                player1_id if player_color.lower() == "white" else None,
                player2_id if player_color.lower() == "black" else None,
                player1_username if player_color.lower() == "black" else None,
                player2_username if player_color.lower() == "white" else None
            )
            
            # 初始化棋盘
            board = chess.Board()
            initial_fen = board.fen()
            
            # 保存初始状态
            db.save_game_move(game_id, 0, "", initial_fen, initial_fen)
            
            game_info = {
                "game_id": game_id,
                "player_color": player_color,
                "ai_difficulty": difficulty_level,
                "current_fen": initial_fen,
                "board_state": str(board),
                "turn": "white",
                "game_status": "active"
            }
            
            # 如果AI执白棋，立即进行AI的第一步
            if player_color.lower() == "black":
                ai_move_result = await cls.make_ai_move(game_id, initial_fen, difficulty_level)
                if ai_move_result["success"]:
                    game_info.update(ai_move_result)
            
            return game_info
            
        except Exception as e:
            raise RuntimeError(f"创建人机对战游戏失败: {str(e)}")
        finally:
            db.close()
    
    @classmethod
    async def make_ai_move(cls, game_id: int, current_fen: str, difficulty_level: str = "medium") -> Dict[str, Any]:
        """
        执行AI移动
        
        Args:
            game_id (int): 游戏ID
            current_fen (str): 当前棋局FEN字符串
            difficulty_level (str): AI难度级别
        
        Returns:
            Dict[str, Any]: 包含移动结果的字典
        """
        if cls.stockfish_engine is None:
            raise RuntimeError("Stockfish引擎未初始化")
        
        db = ChessDB()
        try:
            # 获取AI的走法
            ai_move_uci = await cls.get_ai_move(current_fen, difficulty_level)
            
            if not ai_move_uci:
                return {
                    "success": False,
                    "error": "AI无法生成有效走法",
                    "game_status": "error"
                }
            
            # 执行走法并更新棋盘
            board = chess.Board(current_fen)
            move = chess.Move.from_uci(ai_move_uci)
            
            if move not in board.legal_moves:
                return {
                    "success": False,
                    "error": "AI生成了非法走法",
                    "game_status": "error"
                }
            
            board.push(move)
            new_fen = board.fen()
            move_notation = board.san(move)
            
            # 获取当前移动数
            moves = db.get_game_moves(game_id)
            move_number = len(moves)
            
            # 保存AI走法到数据库
            db.save_game_move(game_id, move_number, move_notation, current_fen, new_fen)
            
            # 检查游戏状态
            game_status = "active"
            result = None
            
            if board.is_checkmate():
                game_status = "finished"
                result = "AI获胜"
            elif board.is_stalemate() or board.is_insufficient_material():
                game_status = "finished"
                result = "平局"
            elif board.is_check():
                game_status = "check"
            
            # 如果游戏结束，更新数据库
            if game_status == "finished":
                db.update_game_result(game_id, result)
            
            return {
                "success": True,
                "ai_move": ai_move_uci,
                "move_notation": move_notation,
                "current_fen": new_fen,
                "board_state": str(board),
                "turn": "white" if board.turn else "black",
                "game_status": game_status,
                "result": result,
                "move_number": move_number
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"AI移动执行失败: {str(e)}",
                "game_status": "error"
            }
        finally:
            db.close()
    
    @classmethod
    async def make_human_move(cls, game_id: int, current_fen: str, human_move_uci: str, 
                            ai_difficulty: str = "medium") -> Dict[str, Any]:
        """
        执行人类玩家移动，然后自动执行AI回应
        
        Args:
            game_id (int): 游戏ID
            current_fen (str): 当前棋局FEN字符串
            human_move_uci (str): 人类玩家的走法（UCI格式）
            ai_difficulty (str): AI难度级别
        
        Returns:
            Dict[str, Any]: 包含移动结果的字典
        """
        db = ChessDB()
        try:
            # 验证并执行人类走法
            board = chess.Board(current_fen)
            human_move = chess.Move.from_uci(human_move_uci)
            
            if human_move not in board.legal_moves:
                return {
                    "success": False,
                    "error": "非法走法",
                    "game_status": "error"
                }
            
            board.push(human_move)
            human_move_notation = board.san(human_move)
            after_human_fen = board.fen()
            
            # 获取当前移动数并保存人类走法
            moves = db.get_game_moves(game_id)
            move_number = len(moves)
            db.save_game_move(game_id, move_number, human_move_notation, current_fen, after_human_fen)
            
            # 检查游戏是否在人类走法后结束
            if board.is_checkmate():
                db.update_game_result(game_id, "玩家获胜")
                return {
                    "success": True,
                    "human_move": human_move_uci,
                    "human_move_notation": human_move_notation,
                    "current_fen": after_human_fen,
                    "board_state": str(board),
                    "game_status": "finished",
                    "result": "玩家获胜"
                }
            elif board.is_stalemate() or board.is_insufficient_material():
                db.update_game_result(game_id, "平局")
                return {
                    "success": True,
                    "human_move": human_move_uci,
                    "human_move_notation": human_move_notation,
                    "current_fen": after_human_fen,
                    "board_state": str(board),
                    "game_status": "finished",
                    "result": "平局"
                }
            
            # 执行AI回应
            ai_response = await cls.make_ai_move(game_id, after_human_fen, ai_difficulty)
            
            return {
                "success": True,
                "human_move": human_move_uci,
                "human_move_notation": human_move_notation,
                "ai_move": ai_response.get("ai_move"),
                "ai_move_notation": ai_response.get("move_notation"),
                "current_fen": ai_response.get("current_fen", after_human_fen),
                "board_state": ai_response.get("board_state"),
                "turn": ai_response.get("turn"),
                "game_status": ai_response.get("game_status"),
                "result": ai_response.get("result"),
                "move_number": move_number + 1
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"执行走法失败: {str(e)}",
                "game_status": "error"
            }
        finally:
            db.close()
    
    @classmethod
    async def get_game_status(cls, game_id: int) -> Dict[str, Any]:
        """
        获取游戏当前状态
        
        Args:
            game_id (int): 游戏ID
        
        Returns:
            Dict[str, Any]: 游戏状态信息
        """
        db = ChessDB()
        try:
            game = db.get_game_by_id(game_id)
            if not game:
                raise ValueError("游戏不存在")
            
            moves = db.get_game_moves(game_id)
            latest_move = moves[-1] if moves else None
            current_fen = latest_move.fen_after if latest_move else chess.Board().fen()
            
            board = chess.Board(current_fen)
            
            return {
                "game_id": game_id,
                "current_fen": current_fen,
                "board_state": str(board),
                "turn": "white" if board.turn else "black",
                "move_count": len(moves),
                "game_result": game.result,
                "is_finished": game.result is not None,
                "legal_moves": [move.uci() for move in board.legal_moves]
            }
            
        except Exception as e:
            raise RuntimeError(f"获取游戏状态失败: {str(e)}")
        finally:
            db.close()
    
    @classmethod
    async def analyze_player_style(cls, username: str) -> dict:
        """深度分析玩家风格和技能水平"""
        db = ChessDB()
        try:
            user = db.get_user_by_username(username)
            if not user:
                raise ValueError('用户不存在')

            games = db.get_user_games(username)
            if not games:
                return {
                    "success": False,
                    "message": "该用户暂无棋局记录",
                    "username": username
                }

            # 收集详细的游戏数据
            game_analysis = await cls._collect_game_data(db, games, user)
            
            # 生成AI分析报告
            ai_analysis = await cls._generate_player_analysis(username, user, game_analysis)
            
            return {
                "success": True,
                "username": username,
                "player_stats": {
                    "total_games": user.total_games,
                    "wins": len([g for g in games if cls._is_user_winner(g, user.user_id)]),
                    "losses": len([g for g in games if cls._is_user_loser(g, user.user_id)]),
                    "draws": len([g for g in games if g.result == 'draw']),
                    "winning_rate": user.winning_rate,
                    "elo_rating": user.elo_rating
                },
                "game_analysis": game_analysis,
                "ai_analysis": ai_analysis,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"分析失败: {str(e)}",
                "username": username
            }
        finally:
            db.close()
    
    @classmethod
    async def _collect_game_data(cls, db: ChessDB, games: list, user) -> dict:
        """收集用户游戏数据用于分析"""
        analysis_data = {
            "opening_preferences": {},
            "endgame_performance": {},
            "common_mistakes": [],
            "strong_moves": [],
            "time_distribution": {},
            "opponent_analysis": {}
        }
        
        # 分析最近的几局游戏（最多10局）
        recent_games = games[-10:] if len(games) > 10 else games
        
        for game in recent_games:
            try:
                moves = db.get_game_moves(game.game_id)
                if not moves:
                    continue
                
                # 分析开局
                opening_moves = moves[:6]  # 前6步
                opening_key = "_".join([m.move_notation for m in opening_moves])
                analysis_data["opening_preferences"][opening_key] = analysis_data["opening_preferences"].get(opening_key, 0) + 1
                
                # 分析残局表现（后10步）
                endgame_moves = moves[-10:] if len(moves) > 10 else moves
                if cls.stockfish_engine and len(endgame_moves) > 0:
                    # 获取残局关键位置的Stockfish分析
                    try:
                        for move in endgame_moves[-3:]:  # 分析最后3步
                            best_moves = await cls.stockfish_engine.get_best_moves(move.fen_before, num_moves=3)
                            if move.move_notation in best_moves[:1]:
                                analysis_data["strong_moves"].append({
                                    "game_id": game.game_id,
                                    "move": move.move_notation,
                                    "position": "endgame",
                                    "quality": "excellent"
                                })
                            elif move.move_notation not in best_moves[:3]:
                                analysis_data["common_mistakes"].append({
                                    "game_id": game.game_id,
                                    "move": move.move_notation,
                                    "position": "endgame",
                                    "better_moves": best_moves[:2]
                                })
                    except Exception as e:
                        print(f"Stockfish分析错误: {e}")
                
                # 对手分析
                opponent_name = game.player2.username if game.player1_id == user.user_id else game.player1.username
                if opponent_name not in analysis_data["opponent_analysis"]:
                    analysis_data["opponent_analysis"][opponent_name] = {"games": 0, "wins": 0, "losses": 0, "draws": 0}
                
                analysis_data["opponent_analysis"][opponent_name]["games"] += 1
                if cls._is_user_winner(game, user.user_id):
                    analysis_data["opponent_analysis"][opponent_name]["wins"] += 1
                elif cls._is_user_loser(game, user.user_id):
                    analysis_data["opponent_analysis"][opponent_name]["losses"] += 1
                else:
                    analysis_data["opponent_analysis"][opponent_name]["draws"] += 1
                    
            except Exception as e:
                print(f"游戏数据收集错误: {e}")
                continue
        
        return analysis_data
    
    @classmethod
    async def _generate_player_analysis(cls, username: str, user, game_analysis: dict) -> str:
        """生成AI驱动的玩家分析报告"""
        
        # 构建分析内容
        opening_stats = game_analysis.get("opening_preferences", {})
        most_used_opening = max(opening_stats.items(), key=lambda x: x[1]) if opening_stats else ("无数据", 0)
        
        strong_moves_count = len(game_analysis.get("strong_moves", []))
        mistakes_count = len(game_analysis.get("common_mistakes", []))
        
        opponent_stats = game_analysis.get("opponent_analysis", {})
        total_opponents = len(opponent_stats)
        
        system_msg = {
            'role': 'system', 
            'content': '''你是一位资深的国际象棋教练和数据分析师。请基于玩家的历史战绩数据，深入分析其棋风特点、技术水平、优势和需要改进的方面。
            
分析要求：
1. 🎯 棋风特点：分析玩家的整体下棋风格（攻击型/稳健型/战术型等）
2. 💪 技术优势：指出玩家的强项和优秀表现
3. ⚠️ 待改进方面：指出明显的弱点和需要提升的技能
4. 📈 发展建议：给出具体的训练建议和提升方向
5. 🎓 学习重点：推荐重点学习的开局、中局或残局内容

请用专业而友善的语气，既要鼓励玩家，也要给出实用的改进建议。'''
        }
        
        user_content = f"""请分析用户 {username} 的国际象棋水平和风格特点：

【基础数据】
- ELO评分: {user.elo_rating}
- 总对局数: {user.total_games}
- 胜率: {user.winning_rate:.1f}%

【技术分析】
- 最常用开局: {most_used_opening[0]} (使用{most_used_opening[1]}次)
- 优秀走法数量: {strong_moves_count}
- 失误走法数量: {mistakes_count}
- 对战对手数: {total_opponents}

【开局偏好】
{', '.join([f"{opening}: {count}次" for opening, count in list(opening_stats.items())[:3]])}

【对手战绩】"""

        # 添加对手战绩详情
        for opponent, stats in list(opponent_stats.items())[:5]:  # 显示前5个对手
            win_rate = (stats["wins"] / stats["games"] * 100) if stats["games"] > 0 else 0
            user_content += f"\n- vs {opponent}: {stats['games']}局 (胜率{win_rate:.1f}%)"

        if game_analysis.get("strong_moves"):
            user_content += f"\n\n【优秀走法示例】"
            for move in game_analysis["strong_moves"][:3]:
                user_content += f"\n- 游戏{move['game_id']}: {move['move']} ({move['position']}阶段)"

        if game_analysis.get("common_mistakes"):
            user_content += f"\n\n【常见失误】"
            for mistake in game_analysis["common_mistakes"][:3]:
                user_content += f"\n- 游戏{mistake['game_id']}: {mistake['move']} -> 建议: {', '.join(mistake['better_moves'][:2])}"

        user_msg = {'role': 'user', 'content': user_content}

        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[system_msg, user_msg],
                temperature=0.7,
                max_tokens=2000
            )
            return resp.choices[0].message.content.strip()
        except Exception as ex:
            return f"AI分析暂时不可用: {str(ex)}"
    
    @classmethod
    def _is_user_winner(cls, game, user_id: int) -> bool:
        """判断用户是否赢得了游戏"""
        if game.result == 'player1_win' and game.player1_id == user_id:
            return True
        elif game.result == 'player2_win' and game.player2_id == user_id:
            return True
        return False
    
    @classmethod
    def _is_user_loser(cls, game, user_id: int) -> bool:
        """判断用户是否输掉了游戏"""
        if game.result == 'player1_win' and game.player2_id == user_id:
            return True
        elif game.result == 'player2_win' and game.player1_id == user_id:
            return True
        return False