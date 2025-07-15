'''一定要修改最后的stockfish路径！！！'''
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import jwt
import os
import asyncio
from datetime import datetime, timedelta, timezone
from functools import wraps
from dao import ChessDB
from analysis_service import AnalysisService
from teaching_service import TeachingService
from competition_service import CompetitionService
import hashlib
import json
import base64
import random
from fisher import StockfishEngine
import openai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置OpenAI API配置
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')

# 检查必要的环境变量
if not openai.api_key:
    print("⚠️  警告: 未设置 OPENAI_API_KEY 环境变量，AI功能将不可用")

# 延迟导入 chess 库以避免启动时的错误
try:
    import chess
    import chess.pgn
    CHESS_AVAILABLE = True
except ImportError:
    CHESS_AVAILABLE = False
    print("⚠️  警告: python-chess 库未安装，国际象棋功能将受限")

app = Flask(__name__)
CORS(app)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=24)

# 全局数据库实例
db = ChessDB()

# JWT认证装饰器
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': {'code': 'UNAUTHORIZED', 'message': 'Token is missing'}}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = db.get_user_by_username(data['username'])
            if not current_user:
                return jsonify({'error': {'code': 'UNAUTHORIZED', 'message': 'Invalid token'}}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': {'code': 'UNAUTHORIZED', 'message': 'Token has expired'}}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': {'code': 'UNAUTHORIZED', 'message': 'Invalid token'}}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# 工具函数
def utc_now():
    """获取当前UTC时间（替代废弃的utc_now()）"""
    return datetime.now(timezone.utc)

def run_async_safe(coro):
    """安全地运行异步函数，避免事件循环冲突"""
    try:
        # 尝试获取当前事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，创建一个新的线程来运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            # 如果没有运行的事件循环，直接运行
            return asyncio.run(coro)
    except RuntimeError:
        # 如果获取事件循环失败，创建新的
        return asyncio.run(coro)

def check_chess_library():
    """检查chess库是否可用"""
    if not CHESS_AVAILABLE:
        return jsonify({'error': {'code': 'SERVICE_UNAVAILABLE', 'message': 'Chess library not available'}}), 503
    return None

def generate_token(username):
    """生成JWT token"""
    payload = {
        'username': username,
        'exp': utc_now() + app.config['JWT_EXPIRATION_DELTA']
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """验证密码"""
    return hashlib.sha256(password.encode()).hexdigest() == hashed

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Resource not found'}}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

# ==================== 身份验证 ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Username and password are required'}}), 422
        
        user = db.get_user_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            return jsonify({'error': {'code': 'UNAUTHORIZED', 'message': 'Invalid username or password'}}), 401
        
        # 更新最后登录时间
        db.update_user(username, last_login=utc_now())
        
        token = generate_token(username)
        response = jsonify({
            'token': token,
            'user': {
                'id': str(user.user_id),
                'username': user.username
            }
        })
        response.set_cookie('token', token, httponly=True, secure=True, samesite='Strict', max_age=86400)
        return response
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """用户登出"""
    response = jsonify({'message': 'Logged out successfully'})
    response.set_cookie('token', '', expires=0)
    return response, 204

# ==================== 用户相关 ====================

@app.route('/api/user/avatar', methods=['GET'])
@token_required
def get_user_avatar(current_user):
    """获取用户头像"""
    # 返回默认头像的base64编码
    default_avatar = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiBmaWxsPSIjZjBmMGYwIi8+CjxjaXJjbGUgY3g9IjUwIiBjeT0iMzUiIHI9IjE1IiBmaWxsPSIjY2NjY2NjIi8+CjxwYXRoIGQ9Ik0yMCA4MEM5MCA4MCA3MCA2MCA1MCA2MFMxMCA4MCAyMCA4MFoiIGZpbGw9IiNjY2NjY2MiLz4KPC9zdmc+"
    
    return jsonify({'avatar': default_avatar})

@app.route('/api/user/profile', methods=['GET'])
@token_required
def get_user_profile(current_user):
    """获取用户个人信息"""
    return jsonify({
        'id': str(current_user.user_id),
        'username': current_user.username,
        'email': f"{current_user.username}@example.com",  # 示例邮箱
        'createdAt': current_user.created_at.isoformat() if current_user.created_at else None,
        'stats': {
            'totalGames': current_user.total_games,
            'wins': current_user.win_games,
            'losses': current_user.total_games - current_user.win_games,
            'draws': 0,  # 暂时没有平局统计
            'winRate': float(current_user.winning_rate) / 100.0
        }
    })

@app.route('/api/user/history', methods=['GET'])
@token_required
def get_user_history(current_user):
    """获取用户历史对局"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        sort_param = request.args.get('sort', 'date_desc')
        
        # 限制参数范围
        page = max(1, page)
        limit = max(1, min(100, limit))
        
        # 获取用户所有对局
        all_games = db.get_user_games(current_user.username)
        
        # 转换为API格式
        games_data = []
        for game in all_games:
            # 确定对手和用户颜色
            if game.player1_id == current_user.user_id:
                opponent = game.player2.username if game.player2 else "AI"
                user_color = "white"
                if game.result == "player1_win":
                    result = "win"
                elif game.result == "player2_win":
                    result = "loss"
                else:
                    result = "draw"
            else:
                opponent = game.player1.username if game.player1 else "AI"
                user_color = "black"
                if game.result == "player2_win":
                    result = "win"
                elif game.result == "player1_win":
                    result = "loss"
                else:
                    result = "draw"
            
            # 计算对局时长
            duration = 0
            if game.start_time and game.end_time:
                duration = int((game.end_time - game.start_time).total_seconds())
            
            # 获取走法数量
            moves = db.get_game_moves(game.game_id)
            move_count = len(moves)
            
            games_data.append({
                'gameId': str(game.game_id),
                'opponent': opponent,
                'result': result,
                'date': game.start_time.isoformat() if game.start_time else None,
                'duration': duration,
                'userColor': user_color,
                'moveCount': move_count,
                'gameType': "match"  # 目前只有对战模式
            })
        
        # 排序
        if sort_param == 'date_desc':
            games_data.sort(key=lambda x: x['date'] or '', reverse=True)
        elif sort_param == 'date_asc':
            games_data.sort(key=lambda x: x['date'] or '')
        elif sort_param == 'result_win':
            games_data = [g for g in games_data if g['result'] == 'win']
        elif sort_param == 'result_loss':
            games_data = [g for g in games_data if g['result'] == 'loss']
        elif sort_param == 'result_draw':
            games_data = [g for g in games_data if g['result'] == 'draw']
        
        # 分页
        total = len(games_data)
        start = (page - 1) * limit
        end = start + limit
        games_page = games_data[start:end]
        
        total_pages = (total + limit - 1) // limit
        
        return jsonify({
            'games': games_page,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'totalPages': total_pages,
                'hasNext': page < total_pages,
                'hasPrev': page > 1
            }
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@app.route('/api/user/history/<game_id>', methods=['GET'])
@token_required
def get_game_detail(current_user, game_id):
    """获取单局详细复盘数据"""
    try:
        chess_check = check_chess_library()
        if chess_check:
            return chess_check
            
        game = db.get_game_by_id(int(game_id))
        if not game:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Game not found'}}), 404
        
        # 检查用户是否有权限访问
        if game.player1_id != current_user.user_id and game.player2_id != current_user.user_id:
            return jsonify({'error': {'code': 'FORBIDDEN', 'message': 'Access denied'}}), 403
        
        # 获取走法和棋盘状态
        moves = db.get_game_moves(game.game_id)
        move_list = []
        board_states = []
        timestamps = []
        
        # 构建走法列表和棋盘状态
        board = chess.Board()
        board_states.append(board.fen())
        
        for move in moves:
            move_list.append(move.move_notation)
            board_states.append(move.fen_after)
            timestamps.append(move.created_at.isoformat() if hasattr(move, 'created_at') else game.start_time.isoformat())
        
        # 构建评论数据
        comments = []
        for i, move in enumerate(moves):
            if move.comment:
                comments.append({
                    'moveIndex': i,
                    'userComment': move.comment,
                    'aiComment': move.evaluation or ""
                })
        
        return jsonify({
            'gameId': str(game.game_id),
            'moves': move_list,
            'boardStates': board_states,
            'timestamps': timestamps,
            'comments': comments
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

# ==================== 对弈模式 ====================

# 全局变量存储活跃游戏状态
active_games = {}

@app.route('/api/game/match', methods=['POST'])
@token_required
def create_match(current_user):
    """创建新的对弈游戏"""
    try:
        data = request.get_json()
        user_color = data.get('color')
        difficulty = data.get('difficulty')
        
        if user_color not in ['white', 'black']:
            return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid color'}}), 422
        
        if difficulty not in ['easy', 'medium', 'hard']:
            return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid difficulty'}}), 422
        
        # 创建新游戏记录
        # 对于AI对战，我们创建一个虚拟的AI用户
        ai_user = db.get_user_by_username('AI')
        if not ai_user:
            ai_user = db.add_user('AI', hash_password('ai_password'), elo_rating=1600)
        
        if user_color == 'white':
            game = db.add_game(current_user.username, 'AI', None)  # result为None表示进行中
        else:
            game = db.add_game('AI', current_user.username, None)
        
        # 初始化游戏状态
        initial_board = chess.Board()
        game_state = {
            'board': initial_board,
            'user_color': user_color,
            'current_player': 'white',
            'difficulty': difficulty,
            'move_history': [],
            'status': 'ongoing'
        }
        
        ai_first_move = None
        
        # 如果用户选择黑方，AI需要先走一步白棋
        if user_color == 'black':
            try:
                if stockfish_engine:
                    ai_move = stockfish_engine.get_best_move_sync(initial_board.fen())
                    if ai_move:
                        move_obj = chess.Move.from_uci(ai_move)
                        if move_obj in initial_board.legal_moves:
                            # AI走第一步
                            initial_board.push(move_obj)
                            ai_first_move = ai_move
                            
                            # 记录AI的走法到数据库
                            move_data = {
                                'move_number': 1,
                                'ply_number': 1,
                                'color': 'white',
                                'move_notation': ai_move,
                                'fen_before': chess.Board().fen(),
                                'fen_after': initial_board.fen()
                            }
                            db.add_move(game.game_id, move_data)
                            
                            # 更新游戏状态
                            game_state['current_player'] = 'black'
                            game_state['move_history'].append({
                                'move': ai_move,
                                'player': 'AI',
                                'move_number': 1
                            })
                
                if not ai_first_move:
                    # 如果AI无法走棋，使用默认开局走法
                    default_moves = ['e2e4', 'd2d4', 'g1f3', 'c2c4']
                    for default_move in default_moves:
                        try:
                            move_obj = chess.Move.from_uci(default_move)
                            if move_obj in initial_board.legal_moves:
                                initial_board.push(move_obj)
                                ai_first_move = default_move
                                
                                # 记录到数据库
                                move_data = {
                                    'move_number': 1,
                                    'ply_number': 1,
                                    'color': 'white',
                                    'move_notation': default_move,
                                    'fen_before': chess.Board().fen(),
                                    'fen_after': initial_board.fen()
                                }
                                db.add_move(game.game_id, move_data)
                                
                                game_state['current_player'] = 'black'
                                game_state['move_history'].append({
                                    'move': default_move,
                                    'player': 'AI',
                                    'move_number': 1
                                })
                                break
                        except:
                            continue
                            
            except Exception as e:
                print(f"AI走第一步时出错: {e}")
                # 使用默认走法 e2e4
                try:
                    move_obj = chess.Move.from_uci('e2e4')
                    initial_board.push(move_obj)
                    ai_first_move = 'e2e4'
                    
                    move_data = {
                        'move_number': 1,
                        'ply_number': 1,
                        'color': 'white',
                        'move_notation': 'e2e4',
                        'fen_before': chess.Board().fen(),
                        'fen_after': initial_board.fen()
                    }
                    db.add_move(game.game_id, move_data)
                    
                    game_state['current_player'] = 'black'
                    game_state['move_history'].append({
                        'move': 'e2e4',
                        'player': 'AI',
                        'move_number': 1
                    })
                except:
                    pass
        
        # 更新棋盘状态
        game_state['board'] = initial_board
        active_games[game.game_id] = game_state
        
        response_data = {
            'gameId': str(game.game_id),
            'userColor': user_color,
            'currentPlayer': game_state['current_player'],
            'difficulty': difficulty,
            'initialBoard': initial_board.fen()
        }
        
        # 如果AI先走了，包含AI的走法信息
        if ai_first_move:
            response_data['aiFirstMove'] = ai_first_move
        
        return jsonify(response_data), 201
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@app.route('/api/game/<game_id>', methods=['GET'])
@token_required
def get_game_state(current_user, game_id):
    """获取对局当前状态"""
    try:
        game_id = int(game_id)
        game = db.get_game_by_id(game_id)
        
        if not game:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Game not found'}}), 404
        
        # 检查权限
        if game.player1_id != current_user.user_id and game.player2_id != current_user.user_id:
            return jsonify({'error': {'code': 'FORBIDDEN', 'message': 'Access denied'}}), 403
        
        # 获取游戏状态
        game_state = active_games.get(game_id)
        if not game_state:
            # 如果游戏不在活跃状态，从数据库重建
            moves = db.get_game_moves(game_id)
            board = chess.Board()
            move_list = []
            
            for move in moves:
                move_list.append(move.move_notation)
                board.push_uci(move.move_notation)
            
            user_color = 'white' if game.player1_id == current_user.user_id else 'black'
            game_state = {
                'board': board,
                'user_color': user_color,
                'current_player': 'white' if board.turn else 'black',
                'move_history': move_list,
                'status': 'finished' if game.result else 'ongoing'
            }
        
        # 确定结果
        result = 'ongoing'
        if game.result:
            if game.player1_id == current_user.user_id:
                result = 'win' if game.result == 'player1_win' else 'loss'
            else:
                result = 'win' if game.result == 'player2_win' else 'loss'
        
        # 获取玩家评价
        evaluation = run_async_safe(CompetitionService.summarize_player(current_user.username))
        
        return jsonify({
            'gameId': str(game_id),
            'boardState': game_state['board'].fen(),
            'moves': game_state['move_history'],
            'currentPlayer': game_state['current_player'],
            'userColor': game_state['user_color'],
            'status': game_state['status'],
            'result': result,
            'moveCount': len(game_state['move_history']),
            'startTime': game.start_time.isoformat() if game.start_time else None,
            'lastMoveTime': game.end_time.isoformat() if game.end_time else None,
            'evaluation': evaluation
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@app.route('/api/game/<game_id>/move', methods=['POST'])
@token_required
def make_move(current_user, game_id):
    """提交用户走法"""
    try:
        game_id = int(game_id)
        data = request.get_json()
        user_move = data.get('move')
        
        if not user_move:
            return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Move is required'}}), 422
        
        game = db.get_game_by_id(game_id)
        if not game:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Game not found'}}), 404
        
        # 检查权限
        if game.player1_id != current_user.user_id and game.player2_id != current_user.user_id:
            return jsonify({'error': {'code': 'FORBIDDEN', 'message': 'Access denied'}}), 403
        
        game_state = active_games.get(game_id)
        if not game_state:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Game session not found'}}), 404
        
        if game_state['status'] != 'ongoing':
            return jsonify({'error': {'code': 'CONFLICT', 'message': 'Game is finished'}}), 409
        
        board = game_state['board']
        user_color = game_state['user_color']
        
        # 检查是否轮到用户
        current_turn = 'white' if board.turn else 'black'
        if current_turn != user_color:
            return jsonify({'error': {'code': 'CONFLICT', 'message': 'Not your turn'}}), 409
        
        # 验证走法
        try:
            move = chess.Move.from_uci(user_move)
            if move not in board.legal_moves:
                return jsonify({'error': {'code': 'BAD_REQUEST', 'message': 'Illegal move'}}), 400
        except:
            return jsonify({'error': {'code': 'BAD_REQUEST', 'message': 'Invalid move format'}}), 400
        
        # 执行用户走法
        fen_before = board.fen()
        board.push(move)
        fen_after = board.fen()
        
        # 记录用户走法
        move_number = len(game_state['move_history']) // 2 + 1
        ply_number = len(game_state['move_history']) + 1
        
        move_data = {
            'move_number': move_number,
            'ply_number': ply_number,
            'color': user_color,
            'move_notation': user_move,
            'fen_before': fen_before,
            'fen_after': fen_after,
            'evaluation': '0.0',
            'comment': 'User move'
        }
        db.add_move(game_id, move_data)
        game_state['move_history'].append(user_move)
        
        # 检查游戏是否结束
        if board.is_checkmate():
            result = 'win'
            game_result = 'player1_win' if user_color == 'white' else 'player2_win'
            db.update_game(game_id, result=game_result, end_time=utc_now())
            game_state['status'] = 'finished'
            
            return jsonify({
                'userMove': user_move,
                'aiMove': None,
                'result': result,
                'boardState': board.fen(),
                'moveCount': len(game_state['move_history']),
                'isCheck': board.is_check(),
                'isCheckmate': True,
                'capturedPiece': None
            })
        
        elif board.is_stalemate() or board.is_insufficient_material():
            result = 'draw'
            db.update_game(game_id, result='draw', end_time=utc_now())
            game_state['status'] = 'finished'
            
            return jsonify({
                'userMove': user_move,
                'aiMove': None,
                'result': result,
                'boardState': board.fen(),
                'moveCount': len(game_state['move_history']),
                'isCheck': board.is_check(),
                'isCheckmate': False,
                'capturedPiece': None
            })
        
        # AI走法
        # ai_move = get_ai_move(board, game_state['difficulty'])
        try:
            # 使用同步方法避免在Flask中使用asyncio.run()
            time_limits = {"easy": 0.1, "medium": 0.5, "hard": 2.0}
            time_limit = time_limits.get(game_state['difficulty'], 0.5)
            ai_move = stockfish_engine.get_best_move_sync(board.fen(), time_limit)
        except Exception as e:
            print(f"AI走法错误: {e}")
            ai_move = None
        if not ai_move:
            # AI无法走棋
            result = 'win'
            game_result = 'player1_win' if user_color == 'white' else 'player2_win'
            db.update_game(game_id, result=game_result, end_time=utc_now())
            game_state['status'] = 'finished'
        else:
            # 执行AI走法
            fen_before_ai = board.fen()
            # Stockfish返回的可能是chess.Move对象或uci字符串，需兼容
            if isinstance(ai_move, str):
                ai_move_obj = chess.Move.from_uci(ai_move)
                ai_move_uci = ai_move
            else:
                ai_move_obj = ai_move
                ai_move_uci = ai_move.uci()
            board.push(ai_move_obj)
            fen_after_ai = board.fen()
            
            # 记录AI走法
            ai_color = 'black' if user_color == 'white' else 'white'
            ai_move_data = {
                'move_number': move_number,
                'ply_number': ply_number + 1,
                'color': ai_color,
                'move_notation': ai_move_uci,
                'fen_before': fen_before_ai,
                'fen_after': fen_after_ai,
                'evaluation': '0.0',
                'comment': 'AI move'
            }
            db.add_move(game_id, ai_move_data)
            game_state['move_history'].append(ai_move_uci)
            
            # 检查AI走法后的游戏状态
            if board.is_checkmate():
                result = 'loss'
                game_result = 'player2_win' if user_color == 'white' else 'player1_win'
                db.update_game(game_id, result=game_result, end_time=utc_now())
                game_state['status'] = 'finished'
            elif board.is_stalemate() or board.is_insufficient_material():
                result = 'draw'
                db.update_game(game_id, result='draw', end_time=utc_now())
                game_state['status'] = 'finished'
            else:
                result = 'ongoing'

        return jsonify({
            'userMove': user_move,
            'aiMove': ai_move_uci if ai_move else None,
            'result': result,
            'boardState': board.fen(),
            'moveCount': len(game_state['move_history']),
            'isCheck': board.is_check(),
            'isCheckmate': board.is_checkmate(),
            'capturedPiece': None,  # TODO: 实现吃子检测
            'evaluation': {
                'score': 0.0,
                'depth': 1
            }
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@app.route('/api/game/<game_id>/resign', methods=['POST'])
@token_required
def resign_game(current_user, game_id):
    """用户认输"""
    try:
        game_id = int(game_id)
        game = db.get_game_by_id(game_id)
        
        if not game:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Game not found'}}), 404
        
        # 检查权限
        if game.player1_id != current_user.user_id and game.player2_id != current_user.user_id:
            return jsonify({'error': {'code': 'FORBIDDEN', 'message': 'Access denied'}}), 403
        
        if game.result:
            return jsonify({'error': {'code': 'CONFLICT', 'message': 'Game is already finished'}}), 409
        
        # 确定结果
        if game.player1_id == current_user.user_id:
            game_result = 'player2_win'
        else:
            game_result = 'player1_win'
        
        db.update_game(game_id, result=game_result, end_time=utc_now())
        
        # 更新游戏状态
        if game_id in active_games:
            active_games[game_id]['status'] = 'finished'
        
        # 获取最终棋盘状态
        game_state = active_games.get(game_id)
        final_board = game_state['board'].fen() if game_state else "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        move_count = len(game_state['move_history']) if game_state else 0
        
        # 计算时长
        duration = 0
        if game.start_time:
            duration = int((utc_now() - game.start_time).total_seconds())
        
        return jsonify({
            'result': 'loss',
            'reason': 'resignation',
            'finalBoard': final_board,
            'moveCount': move_count,
            'duration': duration
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

# ==================== 教学模式 ====================

# 预定义的教学课程
PREDEFINED_LESSONS = [
    {
        'lessonId': 'lesson_1',
        'title': '开局基础：中心控制',
        'description': '学习如何在开局阶段控制棋盘中心',
        'difficulty': 'beginner',
        'category': 'opening',
        'estimatedTime': 15,
        'completionRate': 0.85,
        'prerequisites': [],
        'boardState': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
        'moves': [],
        'userColor': 'white',
        'instructions': '在开局阶段，控制中心格子e4、e5、d4、d5是至关重要的。现在请走出1.e4来控制中心。',
        'objectives': ['掌握中心控制的基本概念', '学会开局的基本走法'],
        'hints': ['e4是经典的开局走法', '控制中心有助于棋子发展']
    },
    {
        'lessonId': 'lesson_2',
        'title': '棋子发展：马的出动',
        'description': '学习如何正确发展马匹',
        'difficulty': 'beginner',
        'category': 'opening',
        'estimatedTime': 20,
        'completionRate': 0.78,
        'prerequisites': ['lesson_1'],
        'boardState': 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1',
        'moves': ['e2e4'],
        'userColor': 'white',
        'instructions': '现在黑方已经应对了e5。接下来我们要发展马匹。请走Nf3发展马匹并攻击对方的兵。',
        'objectives': ['学会正确发展马匹', '理解马的攻击和防守作用'],
        'hints': ['马匹应该尽早发展', 'Nf3是常见的发展走法']
    },
    {
        'lessonId': 'lesson_3',
        'title': '残局基础：王兵残局',
        'description': '掌握基本的王兵残局技巧',
        'difficulty': 'intermediate',
        'category': 'endgame',
        'estimatedTime': 25,
        'completionRate': 0.62,
        'prerequisites': ['lesson_1', 'lesson_2'],
        'boardState': '8/8/8/8/8/8/4P3/4K3 w - - 0 1',
        'moves': [],
        'userColor': 'white',
        'instructions': '在王兵残局中，推进兵并配合王的支持是关键。现在请推进兵到e3。',
        'objectives': ['掌握王兵残局的基本技巧', '学会王兵配合'],
        'hints': ['王要支持兵的推进', '兵要尽快推进到升变']
    }
]

@app.route('/api/teaching/lessons', methods=['GET'])
@token_required
def get_lessons(current_user):
    """获取教学课程列表"""
    try:
        # 获取用户完成的课程（这里简化处理）
        completed_lessons = set()  # 实际应该从数据库获取
        
        lessons = []
        for lesson in PREDEFINED_LESSONS:
            lesson_data = lesson.copy()
            lesson_data['isCompleted'] = lesson['lessonId'] in completed_lessons
            lessons.append(lesson_data)
        
        # 统计分类信息
        categories = {}
        for lesson in lessons:
            category = lesson['category']
            if category not in categories:
                categories[category] = {'count': 0, 'completedCount': 0}
            categories[category]['count'] += 1
            if lesson['isCompleted']:
                categories[category]['completedCount'] += 1
        
        category_list = [
            {'category': cat, 'count': data['count'], 'completedCount': data['completedCount']}
            for cat, data in categories.items()
        ]
        
        return jsonify({
            'lessons': lessons,
            'categories': category_list
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@app.route('/api/teaching/<lesson_id>', methods=['GET'])
@token_required
def get_lesson_detail(current_user, lesson_id):
    """获取特定教学课程的详细信息"""
    try:
        lesson = None
        for l in PREDEFINED_LESSONS:
            if l['lessonId'] == lesson_id:
                lesson = l
                break
        
        if not lesson:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Lesson not found'}}), 404
        
        # 构建棋盘状态
        board = chess.Board(lesson['boardState'])
        for move in lesson['moves']:
            board.push_uci(move)
        
        current_player = 'white' if board.turn else 'black'
        
        return jsonify({
            'lessonId': lesson['lessonId'],
            'title': lesson['title'],
            'description': lesson['description'],
            'boardState': board.fen(),
            'moves': lesson['moves'],
            'currentPlayer': current_player,
            'userColor': lesson['userColor'],
            'instructions': lesson['instructions'],
            'objectives': lesson['objectives'],
            'hints': lesson['hints']
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@app.route('/api/teaching/start', methods=['POST'])
@token_required
def start_teaching_game(current_user):
    """开始教学模式对局"""
    try:
        data = request.get_json()
        lesson_type = data.get('lesson_type', 'general')  # general, opening, endgame
        user_color = data.get('color', 'white')
        
        # 创建教学对局记录（这里简化处理，实际应存数据库）
        teaching_game = {
            'id': f"teaching_{current_user.user_id}_{utc_now().timestamp()}",
            'user_id': current_user.user_id,
            'lesson_type': lesson_type,
            'user_color': user_color,
            'board_state': chess.Board().fen(),
            'moves': [],
            'analysis_history': [],
            'created_at': utc_now().isoformat()
        }
        
        # 如果用户选择黑方，AI需要先走一步白棋
        ai_first_move = None
        ai_first_analysis = None
        
        if user_color == 'black':
            board = chess.Board()
            
            # AI走第一步白棋
            try:
                if stockfish_engine:
                    ai_move = stockfish_engine.get_best_move_sync(board.fen())
                    if ai_move:
                        move_obj = chess.Move.from_uci(ai_move)
                        if move_obj in board.legal_moves:
                            board_before = board.fen()
                            board.push(move_obj)
                            ai_first_move = ai_move
                            
                            # 更新游戏状态
                            teaching_game['board_state'] = board.fen()
                            
                            # 记录AI的第一步
                            move_data = {
                                'move_number': 1,
                                'move': ai_move,
                                'color': 'white',
                                'board_before': board_before,
                                'board_after': board.fen(),
                                'is_ai_move': True,
                                'timestamp': utc_now().isoformat()
                            }
                            teaching_game['moves'].append(move_data)
                            
                            # 为AI的第一步生成分析（可选）
                            ai_first_analysis = f"AI选择了开局走法 {ai_move}，这是一个标准的开局原则。"
                            
                if not ai_first_move:
                    # 如果AI无法走棋，使用默认开局走法
                    default_moves = ['e2e4', 'd2d4', 'g1f3', 'c2c4']
                    for default_move in default_moves:
                        try:
                            move_obj = chess.Move.from_uci(default_move)
                            if move_obj in board.legal_moves:
                                board_before = board.fen()
                                board.push(move_obj)
                                ai_first_move = default_move
                                teaching_game['board_state'] = board.fen()
                                
                                move_data = {
                                    'move_number': 1,
                                    'move': default_move,
                                    'color': 'white',
                                    'board_before': board_before,
                                    'board_after': board.fen(),
                                    'is_ai_move': True,
                                    'timestamp': utc_now().isoformat()
                                }
                                teaching_game['moves'].append(move_data)
                                ai_first_analysis = f"AI选择了经典开局走法 {default_move}。"
                                break
                        except:
                            continue
                            
            except Exception as e:
                print(f"AI走第一步时出错: {e}")
                # 使用默认走法 e2e4
                try:
                    move_obj = chess.Move.from_uci('e2e4')
                    board_before = board.fen()
                    board.push(move_obj)
                    ai_first_move = 'e2e4'
                    teaching_game['board_state'] = board.fen()
                    
                    move_data = {
                        'move_number': 1,
                        'move': 'e2e4',
                        'color': 'white',
                        'board_before': board_before,
                        'board_after': board.fen(),
                        'is_ai_move': True,
                        'timestamp': utc_now().isoformat()
                    }
                    teaching_game['moves'].append(move_data)
                    ai_first_analysis = "AI选择了经典的王兵开局 e2e4。"
                except:
                    pass
        
        # 存储到session或数据库（这里简化用全局变量）
        if not hasattr(app, 'teaching_games'):
            app.teaching_games = {}
        app.teaching_games[teaching_game['id']] = teaching_game
        
        response_data = {
            'success': True,
            'gameId': teaching_game['id'],
            'boardState': teaching_game['board_state'],
            'userColor': user_color,
            'lessonType': lesson_type,
            'instructions': '欢迎进入教学模式！每走一步都会得到AI分析和指导。'
        }
        
        # 如果AI先走了，包含AI的走法信息
        if ai_first_move:
            response_data['aiFirstMove'] = ai_first_move
            response_data['aiFirstAnalysis'] = ai_first_analysis
            response_data['currentPlayer'] = 'black'  # 现在轮到用户（黑方）
        else:
            response_data['currentPlayer'] = 'white'  # 用户（白方）先走
        
        return jsonify(response_data), 201
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@app.route('/api/teaching/<game_id>/move', methods=['POST'])
@token_required
def make_teaching_move(current_user, game_id):
    """在教学模式下提交走法（实时分析）"""
    try:
        # 获取教学对局
        if not hasattr(app, 'teaching_games') or game_id not in app.teaching_games:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Teaching game not found'}}), 404
        
        teaching_game = app.teaching_games[game_id]
        
        data = request.get_json()
        user_move = data.get('move')
        
        if not user_move:
            return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Move is required'}}), 422
        
        # 构建当前棋盘状态
        board = chess.Board(teaching_game['board_state'])
        
        # 验证走法
        try:
            move = chess.Move.from_uci(user_move)
            if move not in board.legal_moves:
                return jsonify({'error': {'code': 'BAD_REQUEST', 'message': 'Illegal move'}}), 400
        except:
            return jsonify({'error': {'code': 'BAD_REQUEST', 'message': 'Invalid move format'}}), 400
        
        # 保存走法前的状态
        board_before = board.fen()
        
        # 执行用户走法
        board.push(move)
        board_after = board.fen()
        move_number = len(teaching_game['moves']) + 1
        color = teaching_game['user_color']
        
        # 🔥 核心功能：实时分析走法
        game_context = {
            'mode': 'teaching',
            'lesson_type': teaching_game['lesson_type'],
            'move_count': move_number
        }
        
        analysis_result = run_async_safe(AnalysisService.analyze_move(
            user_move=user_move,
            board_before=board_before,
            board_after=board_after,
            move_number=move_number,
            color=color,
            game_context=game_context
        ))
        
        # 更新教学对局状态
        move_data = {
            'move_number': move_number,
            'move': user_move,
            'color': color,
            'board_before': board_before,
            'board_after': board_after,
            'analysis': analysis_result,
            'timestamp': utc_now().isoformat()
        }
        
        teaching_game['moves'].append(move_data)
        teaching_game['board_state'] = board_after
        teaching_game['analysis_history'].append(analysis_result)
        
        # AI应对（简化处理）
        ai_move = None
        ai_analysis = None
        
        if not board.is_game_over():
            # 获取合法走法列表
            legal_moves = list(board.legal_moves)
            if len(legal_moves) > 0:
                # 让AI走一步（简化：随机选择）
                import random
                ai_move_obj = random.choice(legal_moves)
                ai_move = ai_move_obj.uci()
                
                board.push(ai_move_obj)
                ai_board_after = board.fen()
                
                # 分析AI走法（也在教学模式下进行分析）
                ai_analysis = run_async_safe(AnalysisService.analyze_move(
                    user_move=ai_move,
                    board_before=board_after,
                    board_after=ai_board_after,
                    move_number=move_number + 1,
                    color='black' if color == 'white' else 'white',
                    game_context={'mode': 'teaching', 'lesson_type': teaching_game['lesson_type'], 'is_ai_move': True}
                ))
                
                # 保存AI走法
                ai_move_data = {
                    'move_number': move_number + 1,
                    'move': ai_move,
                    'color': 'black' if color == 'white' else 'white',
                    'board_before': board_after,
                    'board_after': ai_board_after,
                    'analysis': ai_analysis,
                    'timestamp': utc_now().isoformat()
                }
                
                teaching_game['moves'].append(ai_move_data)
                teaching_game['board_state'] = ai_board_after
                teaching_game['analysis_history'].append(ai_analysis)
        
        return jsonify({
            'success': True,
            'userMove': user_move,
            'userAnalysis': analysis_result.get('ai_analysis', '') if analysis_result.get('success') else '分析暂时不可用',
            'moveQuality': analysis_result.get('move_quality', 'unknown'),
            'aiMove': ai_move,
            'aiAnalysis': ai_analysis.get('ai_analysis', '') if ai_analysis and ai_analysis.get('success') else '',
            'currentFen': teaching_game['board_state'],
            'moveNumber': move_number,
            'gameStatus': 'ongoing' if not board.is_game_over() else 'finished'
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@app.route('/api/teaching/<game_id>/history', methods=['GET'])
@token_required
def get_teaching_history(current_user, game_id):
    """获取教学对局的分析历史"""
    try:
        if not hasattr(app, 'teaching_games') or game_id not in app.teaching_games:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Teaching game not found'}}), 404
        
        teaching_game = app.teaching_games[game_id]
        
        # 构建当前棋盘以获取更多状态信息
        try:
            board = chess.Board(teaching_game['board_state'])
            current_turn = 'white' if board.turn else 'black'
            is_game_over = board.is_game_over()
        except:
            current_turn = 'white'
            is_game_over = False
        
        return jsonify({
            'gameId': game_id,
            'lessonType': teaching_game['lesson_type'],
            'userColor': teaching_game['user_color'],
            'moveHistory': teaching_game['moves'],
            'analysisHistory': teaching_game['analysis_history'],
            'currentBoard': teaching_game['board_state'],
            'currentTurn': current_turn,
            'isGameOver': is_game_over,
            'totalMoves': len(teaching_game['moves'])
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500
        
        # 检查课程是否完成
        result = 'ongoing'
        if lesson_id == 'lesson_1' and user_move == 'e2e4':
            result = 'lesson_complete'
        elif lesson_id == 'lesson_2' and user_move == 'g1f3':
            result = 'lesson_complete'
        elif lesson_id == 'lesson_3' and user_move == 'e2e3':
            result = 'lesson_complete'
        
        # 下一步指导
        next_instruction = ''
        if result == 'lesson_complete':
            next_instruction = '恭喜！你已经完成了这个教学模块。'
        elif lesson_id == 'lesson_1':
            next_instruction = '很好！现在观察黑方的应对，然后我们将学习如何发展马匹。'
        elif lesson_id == 'lesson_2':
            next_instruction = '优秀！马匹的发展是开局的重要组成部分。'
        
        # 计算进度
        total_steps = 3  # 简化处理
        current_step = 1 if user_move else 0
        if result == 'lesson_complete':
            current_step = total_steps
        
        # 提供替代走法
        alternative_moves = []
        if lesson_id == 'lesson_1' and user_move != 'e2e4':
            alternative_moves.append({
                'move': 'e2e4',
                'comment': '这是控制中心的经典走法'
            })
        
        # 获取教学评价
        evaluation = run_async_safe(TeachingService.generate_lessons(current_user.username, 3))
        
        return jsonify({
            'userMove': user_move,
            'aiMove': ai_move,
            'result': result,
            'boardState': board.fen(),
            'userComment': user_comment,
            'aiComment': ai_comment,
            'moveRating': move_rating,
            'alternativeMoves': alternative_moves,
            'nextInstruction': next_instruction,
            'progress': {
                'currentStep': current_step,
                'totalSteps': total_steps,
                'completion': current_step / total_steps
            },
            'evaluation': evaluation
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

# ==================== 教学相关API ====================

@app.route('/api/teaching/skills/<username>', methods=['GET'])
@token_required
def analyze_user_skills(current_user, username):
    """分析指定用户的技能掌握情况"""
    try:
        # 验证权限（用户只能查看自己的技能分析或管理员权限）
        if current_user.username != username:
            # 这里可以添加管理员权限检查
            pass
        
        skill_analysis = run_async_safe(TeachingService.analyze_user_skills(username))
        
        if "error" in skill_analysis:
            return jsonify({
                'success': False,
                'error': skill_analysis["error"]
            }), 404
        
        return jsonify({
            'success': True,
            'data': skill_analysis
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'SKILL_ANALYSIS_ERROR', 'message': str(e)}}), 500

@app.route('/api/teaching/skills', methods=['GET'])
@token_required
def analyze_current_user_skills(current_user):
    """分析当前用户的技能掌握情况"""
    try:
        skill_analysis = run_async_safe(TeachingService.analyze_user_skills(current_user.username))
        
        if "error" in skill_analysis:
            return jsonify({
                'success': False,
                'error': skill_analysis["error"]
            }), 404
        
        return jsonify({
            'success': True,
            'data': skill_analysis
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'SKILL_ANALYSIS_ERROR', 'message': str(e)}}), 500

@app.route('/api/teaching/learning-plan/<username>', methods=['GET'])
@token_required
def get_user_learning_plan(current_user, username):
    """获取指定用户的个性化学习计划"""
    try:
        # 验证权限
        if current_user.username != username:
            # 这里可以添加管理员权限检查
            pass
        
        learning_plan = run_async_safe(TeachingService.get_personalized_learning_plan(username))
        
        if "error" in learning_plan:
            return jsonify({
                'success': False,
                'error': learning_plan["error"]
            }), 404
        
        return jsonify({
            'success': True,
            'data': learning_plan
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'LEARNING_PLAN_ERROR', 'message': str(e)}}), 500

@app.route('/api/teaching/learning-plan', methods=['GET'])
@token_required
def get_current_user_learning_plan(current_user):
    """获取当前用户的个性化学习计划"""
    try:
        learning_plan = run_async_safe(TeachingService.get_personalized_learning_plan(current_user.username))
        
        if "error" in learning_plan:
            return jsonify({
                'success': False,
                'error': learning_plan["error"]
            }), 404
        
        return jsonify({
            'success': True,
            'data': learning_plan
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'LEARNING_PLAN_ERROR', 'message': str(e)}}), 500

@app.route('/api/teaching/personalized-lessons', methods=['POST'])
@token_required
def generate_personalized_lessons(current_user):
    """生成个性化教学课程"""
    try:
        data = request.get_json()
        lessons_count = data.get('lessons_count', 3)
        target_username = data.get('username', current_user.username)
        
        # 验证权限
        if current_user.username != target_username:
            # 这里可以添加管理员权限检查
            pass
        
        # 限制课程数量
        lessons_count = max(1, min(10, lessons_count))
        
        lessons = run_async_safe(TeachingService.generate_lessons(target_username, lessons_count))
        
        return jsonify({
            'success': True,
            'data': {
                'username': target_username,
                'lessons_count': lessons_count,
                'lessons': lessons,
                'generated_at': datetime.now().isoformat()
            }
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({'error': {'code': 'LESSON_GENERATION_ERROR', 'message': str(e)}}), 500

@app.route('/api/teaching/skill-definitions', methods=['GET'])
@token_required
def get_skill_definitions(current_user):
    """获取技能定义和评估标准"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'skill_definitions': TeachingService.SKILL_DEFINITIONS,
                'total_skills': len(TeachingService.SKILL_DEFINITIONS)
            }
        })
    except Exception as e:
        return jsonify({'error': {'code': 'SKILL_DEFINITIONS_ERROR', 'message': str(e)}}), 500

# ==================== 复盘功能 ====================

@app.route('/api/replay/<game_id>', methods=['GET'])
@token_required
def get_replay_data(current_user, game_id):
    """获取复盘数据"""
    try:
        game = db.get_game_by_id(int(game_id))
        if not game:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Game not found'}}), 404
        
        # 检查权限
        if game.player1_id != current_user.user_id and game.player2_id != current_user.user_id:
            return jsonify({'error': {'code': 'FORBIDDEN', 'message': 'Access denied'}}), 403
        
        # 获取走法
        moves = db.get_game_moves(game.game_id)
        move_list = []
        board_states = []
        timestamps = []
        
        # 构建数据
        board = chess.Board()
        board_states.append(board.fen())
        
        for move in moves:
            move_list.append(move.move_notation)
            board.push_uci(move.move_notation)
            board_states.append(board.fen())
            timestamps.append(move.created_at.isoformat() if hasattr(move, 'created_at') else game.start_time.isoformat())
        
        # 获取对手信息
        if game.player1_id == current_user.user_id:
            opponent = game.player2.username if game.player2 else "AI"
            user_color = 'white'
            if game.result == 'player1_win':
                result = 'win'
            elif game.result == 'player2_win':
                result = 'loss'
            else:
                result = 'draw'
        else:
            opponent = game.player1.username if game.player1 else "AI"
            user_color = 'black'
            if game.result == 'player2_win':
                result = 'win'
            elif game.result == 'player1_win':
                result = 'loss'
            else:
                result = 'draw'
        
        # 计算时长
        duration = 0
        if game.start_time and game.end_time:
            duration = int((game.end_time - game.start_time).total_seconds())
        
        # 使用AI分析服务获取分析报告
        try:
            ai_analysis = AnalysisService.analyze_game(game.game_id)
        except Exception as e:
            ai_analysis = f"AI分析暂时不可用: {str(e)}"
        
        # 获取玩家评价
        evaluation = run_async_safe(CompetitionService.summarize_player(current_user.username))
        
        return jsonify({
            'gameId': str(game.game_id),
            'moves': move_list,
            'boardStates': board_states,
            'timestamps': timestamps,
            'gameInfo': {
                'opponent': opponent,
                'result': result,
                'userColor': user_color,
                'duration': duration,
                'startTime': game.start_time.isoformat() if game.start_time else None,
                'endTime': game.end_time.isoformat() if game.end_time else None,
                'totalMoves': len(move_list),
                'gameType': 'match'
            },
            'aiAnalysis': ai_analysis,
            'keyMoments': [],  # 这里可以添加关键时刻分析
            'evaluation': evaluation
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

# ==================== 用户注册 ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Username and password are required'}}), 422
        
        if len(username) < 3 or len(username) > 20:
            return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Username must be 3-20 characters'}}), 422
        
        if len(password) < 6:
            return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'Password must be at least 6 characters'}}), 422
        
        # 检查用户是否已存在
        if db.get_user_by_username(username):
            return jsonify({'error': {'code': 'CONFLICT', 'message': 'Username already exists'}}), 409
        
        # 创建用户
        user = db.add_user(username, hash_password(password))
        
        token = generate_token(username)
        response = jsonify({
            'token': token,
            'user': {
                'id': str(user.user_id),
                'username': user.username
            }
        })
        response.set_cookie('token', token, httponly=True, secure=True, samesite='Strict', max_age=86400)
        
        return response, 201
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

# ==================== 启动检查 ====================

@app.route('/api/start', methods=['GET'])
def start_page():
    """检查登录状态"""
    token = request.headers.get('Authorization') or request.cookies.get('token')
    
    if not token:
        return jsonify({'redirect': '/login', 'authenticated': False})
    
    try:
        if token.startswith('Bearer '):
            token = token[7:]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = db.get_user_by_username(data['username'])
        if user:
            return jsonify({'redirect': '/home', 'authenticated': True, 'user': {'username': user.username}})
    except:
        pass
    
    return jsonify({'redirect': '/login', 'authenticated': False})

@app.route('/')
def index():
    """根路径"""
    return jsonify({
        'message': 'Chess Game API Server',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth/*',
            'user': '/api/user/*', 
            'game': '/api/game/*',
            'start': '/api/start'
        }
    })

@app.route('/api/ping', methods=['GET'])
def ping():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': 'pong',
        'timestamp': utc_now().isoformat(),
        'server': 'Chess Game API Server',
        'version': '1.0.0'
    })

@app.route('/api/users/ranking', methods=['GET'])
@token_required
def get_users_ranking(current_user):
    """获取用户排行榜"""
    try:
        limit = request.args.get('limit', 10, type=int)
        users = db.get_users_by_ranking(limit)
        
        users_data = []
        for user in users:
            users_data.append({
                'username': user.username,
                'elo_rating': user.elo_rating,
                'total_games': user.total_games,
                'win_games': user.win_games,
                'winning_rate': float(user.winning_rate)
            })
        
        return jsonify({
            'users': users_data,
            'total': len(users_data)
        })
    except Exception as e:
        return jsonify({'error': {'code': 'RANKING_ERROR', 'message': str(e)}}), 500

@app.route('/api/games/recent', methods=['GET'])
@token_required
def get_recent_games(current_user):
    """获取最近的棋局"""
    try:
        limit = request.args.get('limit', 10, type=int)
        games = db.get_recent_games(limit)
        
        games_data = []
        for game in games:
            games_data.append({
                'game_id': game.game_id,
                'player1_username': game.player1.username,
                'player2_username': game.player2.username,
                'result': game.result,
                'start_time': game.start_time.isoformat() if game.start_time else None,
                'end_time': game.end_time.isoformat() if game.end_time else None
            })
        
        return jsonify({
            'games': games_data,
            'total': len(games_data)
        })
    except Exception as e:
        return jsonify({'error': {'code': 'GAMES_ERROR', 'message': str(e)}}), 500

@app.route('/api/user/analysis', methods=['GET'])
@token_required
def analyze_current_user(current_user):
    """分析当前用户的棋风和技术水平"""
    try:
        analysis_result = run_async_safe(CompetitionService.analyze_player_style(current_user.username))
        
        if analysis_result["success"]:
            return jsonify({
                'success': True,
                'analysis': analysis_result,
                'timestamp': analysis_result["analysis_timestamp"]
            })
        else:
            return jsonify({
                'success': False,
                'error': analysis_result.get("error", analysis_result.get("message", "分析失败"))
            }), 404
            
    except Exception as e:
        return jsonify({'error': {'code': 'ANALYSIS_ERROR', 'message': str(e)}}), 500

@app.route('/api/user/analysis/<username>', methods=['GET'])
@token_required
def analyze_user_by_name(current_user, username):
    """分析指定用户的棋风和技术水平"""
    try:
        # 验证权限（可以查看自己或者是管理员）
        if current_user.username != username:
            # 这里可以添加管理员权限检查
            pass
        
        analysis_result = run_async_safe(CompetitionService.analyze_player_style(username))
        
        if analysis_result["success"]:
            return jsonify({
                'success': True,
                'analysis': analysis_result,
                'timestamp': analysis_result["analysis_timestamp"]
            })
        else:
            return jsonify({
                'success': False,
                'error': analysis_result.get("error", analysis_result.get("message", "分析失败"))
            }), 404
            
    except Exception as e:
        return jsonify({'error': {'code': 'ANALYSIS_ERROR', 'message': str(e)}}), 500

# Stockfish路径配置
STOCKFISH_PATH = os.getenv('STOCKFISH_PATH', r"D:\stockfish\stockfish-windows-x86-64-avx2.exe")
stockfish_engine = StockfishEngine(stockfish_path=STOCKFISH_PATH)
stockfish_engine.ensure_engine_running_sync()

# 为CompetitionService设置Stockfish引擎
CompetitionService.stockfish_engine = stockfish_engine
# 为AnalysisService设置Stockfish引擎
AnalysisService.stockfish_engine = stockfish_engine
# 为TeachingService设置Stockfish引擎
TeachingService.stockfish_engine = stockfish_engine

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
