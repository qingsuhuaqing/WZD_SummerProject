import openai
import os
import json
from dao import ChessDB
from fisher import StockfishEngine  # 导入Stockfish引擎
import asyncio
from datetime import datetime
from typing import Dict, List, Set
import chess
import chess.pgn

class TeachingService:
    # 添加Stockfish引擎实例作为类属性
    stockfish_engine = None
    
    # 定义技能标签和掌握标准
    SKILL_DEFINITIONS = {
        "opening_principles": {
            "name": "开局基本原则",
            "description": "控制中心、发展棋子、王车易位等基础开局原则",
            "mastery_threshold": 0.7,  # 70%以上算掌握
            "evaluation_methods": ["center_control", "piece_development", "castling_timing"]
        },
        "tactical_patterns": {
            "name": "战术主题",
            "description": "捉双、钉住、穿刺、叉攻等战术手段",
            "mastery_threshold": 0.6,
            "evaluation_methods": ["fork_usage", "pin_recognition", "skewer_execution"]
        },
        "endgame_technique": {
            "name": "残局技巧",
            "description": "基本残局定式和技术残局处理",
            "mastery_threshold": 0.65,
            "evaluation_methods": ["pawn_endgames", "rook_endgames", "piece_coordination"]
        },
        "positional_understanding": {
            "name": "位置理解",
            "description": "弱格、棋子活动性、兵形结构等位置概念",
            "mastery_threshold": 0.6,
            "evaluation_methods": ["weak_square_control", "piece_activity", "pawn_structure"]
        },
        "time_management": {
            "name": "时间管理",
            "description": "合理分配思考时间，避免时间紧迫",
            "mastery_threshold": 0.75,
            "evaluation_methods": ["move_time_distribution", "critical_moment_timing"]
        },
        "calculation_accuracy": {
            "name": "计算精度",
            "description": "准确计算战术组合和变化",
            "mastery_threshold": 0.65,
            "evaluation_methods": ["move_accuracy", "blunder_frequency", "missed_tactics"]
        }
    }
    
    @classmethod
    async def initialize_stockfish(cls, stockfish_path: str):
        """初始化Stockfish引擎"""
        if cls.stockfish_engine is None:
            cls.stockfish_engine = StockfishEngine(stockfish_path)
            await cls.stockfish_engine._ensure_engine_running()
    
    @classmethod
    async def generate_lessons(cls, username: str, lessons_count: int) -> str:
        """为用户生成教学课程（基于技能分析，避免重复教学）"""
        db = ChessDB()
        try:
            user = db.get_user_by_username(username)
            if not user:
                raise ValueError('用户不存在')

            # 获取用户技能分析
            skill_analysis_result = await cls.analyze_user_skills(username)
            if "error" in skill_analysis_result:
                raise ValueError(f'技能分析失败: {skill_analysis_result["error"]}')
            
            # 获取个性化学习计划
            learning_plan = await cls.get_personalized_learning_plan(username)
            if "error" in learning_plan:
                raise ValueError(f'学习计划生成失败: {learning_plan["error"]}')

            games = db.get_user_games(username)
            if not games:
                raise ValueError('该用户暂无棋局记录')

            # 汇总数据并添加Stockfish分析
            content_list = []
            for game in games[:3]:  # 只分析最近3场比赛
                pgn_data = db.get_pgn_data(game.game_id)
                moves = db.get_game_moves(game.game_id)
                
                # 获取关键局面的Stockfish分析
                key_analysis = []
                for i, move in enumerate(moves):
                    if i % 5 == 0 or i == len(moves) - 1:  # 每5步分析一次
                        if cls.stockfish_engine:
                            best_moves = await cls.stockfish_engine.get_best_moves(move.fen_before, num_moves=2)
                            key_analysis.append({
                                "move_number": move.move_number,
                                "player_move": move.move_notation,
                                "stockfish_recommendations": best_moves
                            })
                
                game_data = {
                    'game_id': game.game_id,
                    'pgn': pgn_data.pgn_text if pgn_data else '',
                    'headers': json.loads(pgn_data.headers) if pgn_data and pgn_data.headers else {},
                    'moves': [{
                        'move_number': m.move_number,
                        'ply_number': m.ply_number,
                        'color': m.color,
                        'notation': m.move_notation,
                        'fen_before': m.fen_before,
                        'fen_after': m.fen_after,
                        'comment': m.comment
                    } for m in moves],
                    'key_analysis': key_analysis
                }
                content_list.append(game_data)

            # 构造 Prompt（包含技能分析和个性化建议）
            mastered_skills = learning_plan.get("mastered_skills", [])
            skills_to_improve = learning_plan.get("skills_to_improve", [])[:3]  # 重点关注前3个技能
            
            system_msg = {
                'role': 'system', 
                'content': (
                    '你是一名经验丰富的国际象棋教练，需要根据学生的技能掌握情况生成个性化教学方案。'
                    '重要原则：\n'
                    '1. 不要重复教授学生已经掌握的技能\n'
                    '2. 重点关注学生需要提升的薄弱环节\n'
                    '3. 根据学生的实际棋局表现制定针对性练习\n'
                    '4. 每个教学模块应该有明确的学习目标和练习方法'
                )
            }
            
            user_msg = {
                'role': 'user',
                'content': (
                    f"请为用户 {username} (ELO: {user.elo_rating}) 生成 {lessons_count} 个个性化教学模块。\n\n"
                    f"用户基本信息：\n"
                    f"- 总对局数: {user.total_games}\n"
                    f"- 胜率: {user.winning_rate}%\n"
                    f"- 整体技能进度: {learning_plan.get('overall_progress', 0):.1%}\n\n"
                    f"用户已掌握的技能（请不要重复教授）：\n{', '.join(mastered_skills) if mastered_skills else '暂无'}\n\n"
                    f"需要重点提升的技能：\n"
                    + "\n".join([f"- {skill['name']} (当前分数: {skill['current_score']:.2f}, 目标: {skill['target_score']:.2f})" 
                                for skill in skills_to_improve]) + "\n\n"
                    f"历史棋局分析数据（用于制定针对性练习）：\n{content_list}\n\n"
                    f"请生成 {lessons_count} 个教学模块，每个模块应包括：\n"
                    f"1. 模块标题和学习目标\n"
                    f"2. 针对性的理论讲解\n"
                    f"3. 基于用户实际棋局的案例分析\n"
                    f"4. 具体的练习建议和方法\n"
                    f"5. 预期的学习效果和评估标准"
                )
            }

            openai.api_key = os.getenv('OPENAI_API_KEY')
            try:
                resp = openai.ChatCompletion.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4o'),
                    messages=[system_msg, user_msg],
                    temperature=0.7,
                    max_tokens=3000  # 增加token数量以支持更详细的个性化内容
                )
                return resp.choices[0].message.content.strip()
            except Exception as ex:
                raise RuntimeError(f"OpenAI API error: {str(ex)}")
        finally:
            db.close()
    
    @classmethod
    async def analyze_user_skills(cls, username: str) -> Dict:
        """分析用户已掌握的技能"""
        db = ChessDB()
        try:
            user = db.get_user_by_username(username)
            if not user:
                return {"error": "用户不存在"}

            games = db.get_user_games(username)
            if not games:
                return {"error": "该用户暂无棋局记录"}

            # 分析用户技能掌握情况
            skill_analysis = {}
            
            for skill_id, skill_def in cls.SKILL_DEFINITIONS.items():
                skill_score = await cls._evaluate_skill(db, games, user, skill_id, skill_def)
                skill_analysis[skill_id] = {
                    "name": skill_def["name"],
                    "description": skill_def["description"],
                    "score": skill_score,
                    "mastered": skill_score >= skill_def["mastery_threshold"],
                    "mastery_threshold": skill_def["mastery_threshold"]
                }
            
            # 计算总体技能水平
            mastered_skills = [skill for skill in skill_analysis.values() if skill["mastered"]]
            overall_progress = len(mastered_skills) / len(cls.SKILL_DEFINITIONS)
            
            return {
                "username": username,
                "skill_analysis": skill_analysis,
                "mastered_skills_count": len(mastered_skills),
                "total_skills_count": len(cls.SKILL_DEFINITIONS),
                "overall_progress": overall_progress,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"技能分析失败: {str(e)}"}
        finally:
            db.close()
    
    @classmethod
    async def _evaluate_skill(cls, db: ChessDB, games: list, user, skill_id: str, skill_def: Dict) -> float:
        """评估特定技能的掌握程度"""
        if skill_id == "opening_principles":
            return await cls._evaluate_opening_principles(db, games, user)
        elif skill_id == "tactical_patterns":
            return await cls._evaluate_tactical_patterns(db, games, user)
        elif skill_id == "endgame_technique":
            return await cls._evaluate_endgame_technique(db, games, user)
        elif skill_id == "positional_understanding":
            return await cls._evaluate_positional_understanding(db, games, user)
        elif skill_id == "time_management":
            return await cls._evaluate_time_management(db, games, user)
        elif skill_id == "calculation_accuracy":
            return await cls._evaluate_calculation_accuracy(db, games, user)
        else:
            return 0.0
    
    @classmethod
    async def _evaluate_opening_principles(cls, db: ChessDB, games: list, user) -> float:
        """评估开局原则掌握程度"""
        total_score = 0
        evaluated_games = 0
        
        # 分析最近10局游戏的开局表现
        recent_games = games[-10:] if len(games) > 10 else games
        
        for game in recent_games:
            moves = db.get_game_moves(game.game_id)
            if len(moves) < 10:  # 开局至少需要10步
                continue
                
            opening_moves = moves[:10]  # 分析前10步
            score = 0
            
            # 检查是否及时王车易位
            castled_early = any("O-O" in move.move_notation for move in opening_moves[:8])
            if castled_early:
                score += 0.3
            
            # 检查中心控制（通过e4, d4, e5, d5等走法）
            center_moves = sum(1 for move in opening_moves[:4] 
                             if any(center in move.move_notation for center in ['e4', 'd4', 'e5', 'd5']))
            if center_moves >= 1:
                score += 0.4
            
            # 检查棋子发展（马、象的发展）
            piece_development = sum(1 for move in opening_moves[:8] 
                                  if any(piece in move.move_notation for piece in ['N', 'B']))
            if piece_development >= 3:
                score += 0.3
            
            total_score += score
            evaluated_games += 1
        
        return total_score / evaluated_games if evaluated_games > 0 else 0.0
    
    @classmethod
    async def _evaluate_tactical_patterns(cls, db: ChessDB, games: list, user) -> float:
        """评估战术主题掌握程度"""
        # 这里简化实现，实际可以结合Stockfish分析战术动机
        good_moves = 0
        total_tactical_opportunities = 0
        
        recent_games = games[-5:] if len(games) > 5 else games
        
        for game in recent_games:
            moves = db.get_game_moves(game.game_id)
            
            # 寻找包含战术元素的走法（简化版，实际需要更复杂的分析）
            for move in moves:
                if any(symbol in move.move_notation for symbol in ['x', '+', '#']):  # 吃子、将军、将死
                    total_tactical_opportunities += 1
                    
                    # 使用Stockfish评估该走法是否优秀
                    if cls.stockfish_engine:
                        try:
                            best_moves = await cls.stockfish_engine.get_best_moves(move.fen_before, num_moves=3)
                            if move.move_notation in best_moves[:2]:  # 在前2个推荐走法中
                                good_moves += 1
                        except:
                            pass
        
        return good_moves / total_tactical_opportunities if total_tactical_opportunities > 0 else 0.5
    
    @classmethod
    async def _evaluate_endgame_technique(cls, db: ChessDB, games: list, user) -> float:
        """评估残局技巧掌握程度"""
        endgame_performance = []
        
        recent_games = games[-8:] if len(games) > 8 else games
        
        for game in recent_games:
            moves = db.get_game_moves(game.game_id)
            if len(moves) < 20:  # 游戏太短，没有真正的残局
                continue
                
            # 分析最后15步的表现（残局阶段）
            endgame_moves = moves[-15:]
            accurate_moves = 0
            
            for move in endgame_moves:
                if cls.stockfish_engine:
                    try:
                        best_moves = await cls.stockfish_engine.get_best_moves(move.fen_before, num_moves=5)
                        if move.move_notation in best_moves[:3]:
                            accurate_moves += 1
                    except:
                        pass
            
            if len(endgame_moves) > 0:
                performance = accurate_moves / len(endgame_moves)
                endgame_performance.append(performance)
        
        return sum(endgame_performance) / len(endgame_performance) if endgame_performance else 0.5
    
    @classmethod
    async def _evaluate_positional_understanding(cls, db: ChessDB, games: list, user) -> float:
        """评估位置理解掌握程度"""
        # 简化实现：基于游戏胜率和ELO评级估算
        win_rate = user.winning_rate / 100.0
        elo_factor = min(user.elo_rating / 2000.0, 1.0)  # ELO越高位置理解越好
        
        return (win_rate * 0.6 + elo_factor * 0.4)
    
    @classmethod
    async def _evaluate_time_management(cls, db: ChessDB, games: list, user) -> float:
        """评估时间管理掌握程度"""
        # 简化实现：假设用户时间管理较好（实际需要记录每步用时）
        return 0.7  # 默认评分
    
    @classmethod
    async def _evaluate_calculation_accuracy(cls, db: ChessDB, games: list, user) -> float:
        """评估计算精度"""
        if not cls.stockfish_engine:
            return 0.6  # 无法分析时给默认分
            
        accurate_moves = 0
        total_moves = 0
        
        # 分析最近3局游戏
        recent_games = games[-3:] if len(games) > 3 else games
        
        for game in recent_games:
            moves = db.get_game_moves(game.game_id)
            
            # 随机抽样一些关键位置进行分析
            sample_moves = moves[::5] if len(moves) > 10 else moves  # 每5步抽样1步
            
            for move in sample_moves:
                try:
                    best_moves = await cls.stockfish_engine.get_best_moves(move.fen_before, num_moves=5)
                    total_moves += 1
                    
                    if move.move_notation in best_moves[:3]:
                        accurate_moves += 1
                except:
                    pass
        
        return accurate_moves / total_moves if total_moves > 0 else 0.6
    
    @classmethod
    async def get_personalized_learning_plan(cls, username: str) -> Dict:
        """生成个性化学习计划"""
        # 首先分析用户技能
        skill_analysis_result = await cls.analyze_user_skills(username)
        
        if "error" in skill_analysis_result:
            return skill_analysis_result
        
        skill_analysis = skill_analysis_result["skill_analysis"]
        
        # 识别需要提升的技能（未掌握或分数较低的）
        skills_to_improve = []
        mastered_skills = []
        
        for skill_id, skill_data in skill_analysis.items():
            if not skill_data["mastered"]:
                skills_to_improve.append({
                    "skill_id": skill_id,
                    "name": skill_data["name"],
                    "description": skill_data["description"],
                    "current_score": skill_data["score"],
                    "target_score": skill_data["mastery_threshold"],
                    "priority": skill_data["mastery_threshold"] - skill_data["score"]  # 差距越大优先级越高
                })
            else:
                mastered_skills.append(skill_data["name"])
        
        # 按优先级排序
        skills_to_improve.sort(key=lambda x: x["priority"], reverse=True)
        
        # 生成个性化教学内容推荐
        learning_recommendations = await cls._generate_learning_recommendations(
            username, skills_to_improve[:3], mastered_skills  # 重点关注前3个最需要提升的技能
        )
        
        return {
            "username": username,
            "mastered_skills": mastered_skills,
            "skills_to_improve": skills_to_improve,
            "learning_recommendations": learning_recommendations,
            "overall_progress": skill_analysis_result["overall_progress"],
            "timestamp": datetime.now().isoformat()
        }
    
    @classmethod
    async def _generate_learning_recommendations(cls, username: str, priority_skills: List[Dict], mastered_skills: List[str]) -> List[Dict]:
        """生成个性化学习推荐"""
        recommendations = []
        
        for skill in priority_skills:
            # 根据技能类型生成具体的学习建议
            if skill["skill_id"] == "opening_principles":
                recommendations.append({
                    "skill_focus": skill["name"],
                    "learning_objectives": [
                        "练习控制中心的开局走法（e4, d4等）",
                        "学习及时王车易位的时机",
                        "掌握马和象的最佳发展方式"
                    ],
                    "practice_exercises": [
                        "意大利开局练习",
                        "西班牙开局基础变化",
                        "王翼印度防御要点"
                    ],
                    "estimated_study_time": "2-3周"
                })
            elif skill["skill_id"] == "tactical_patterns":
                recommendations.append({
                    "skill_focus": skill["name"],
                    "learning_objectives": [
                        "识别和执行基本战术主题",
                        "提高战术视野和计算能力",
                        "学会在实战中寻找战术机会"
                    ],
                    "practice_exercises": [
                        "每日战术题训练",
                        "捉双和叉攻专项练习",
                        "钉住和穿刺技巧训练"
                    ],
                    "estimated_study_time": "1-2周"
                })
            elif skill["skill_id"] == "endgame_technique":
                recommendations.append({
                    "skill_focus": skill["name"],
                    "learning_objectives": [
                        "掌握基本残局定式",
                        "提高残局棋子协调能力",
                        "学习常见残局转换技巧"
                    ],
                    "practice_exercises": [
                        "王兵对王残局练习",
                        "车兵残局基础训练",
                        "简单子力残局定式"
                    ],
                    "estimated_study_time": "3-4周"
                })
            # 可以继续添加其他技能的推荐...
        
        return recommendations