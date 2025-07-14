import os
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, User, Game, PGNData, Move

# 数据库连接配置
#DATABASE_URI = "mysql+pymysql://root:mrd200476@8.154.21.102:3306/chess_db"
DATABASE_URI = "sqlite:///chess_db.sqlite"

# 初始化数据库
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

def init_db(drop_existing=False):
    """创建所有表"""
    if drop_existing:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def add_sample_data():
    """添加示例数据"""
    with Session() as session:
        # 添加用户
        users = [
            User(username="magnus", password_hash="hash1", elo_rating=2850),
            User(username="hikaru", password_hash="hash2", elo_rating=2800)
        ]
        session.add_all(users)
        session.commit()
        
        # 添加棋局
        game = Game(
            player1_id=users[0].user_id,
            player2_id=users[1].user_id,
            result="player1_win"
        )
        session.add(game)
        session.commit()
        
        # 添加PGN数据
        pgn_text = """
[Event "Example Game"]
[Site "?"]
[Date "2023.05.15"]
[Round "?"]
[White "Magnus"]
[Black "Hikaru"]
[Result "1-0"]
[ECO "C42"]
[WhiteElo "2850"]
[BlackElo "2800"]

1. e4 e5 2. Nf3 Nf6 3. Nxe5 d6 4. Nf3 Nxe4 5. d4 d5 6. Bd3 Nc6 7. O-O Be7
8. c4 Nb4 9. Be2 O-O 10. Nc3 Bf5 11. a3 Nxc3 12. bxc3 Nc6 13. Re1 Re8 14. Bf4
Bd6 15. Bxd6 Qxd6 16. cxd5 Qxd5 17. Qxd5 Nxd5 18. Nd2 Nf6 19. c4 Rac8 20. Rac1
Rxc4 21. Rxc4 Bxc4 22. Nxc4 Nxe4 23. Rxe4 Rxe4 24. Bf3 Re1+ 25. Kf2 Ra1 26. Ke3
Kf8 27. a4 Ke7 28. a5 Kd6 29. a6 bxa6 30. d5 Kc5 31. d6 Kxc4 32. d7 Kb3 33. d8=Q+
Kxb2 34. Qd4+ Kb3 35. Qb6+ Ka4 36. Qa6# 1-0
"""
        headers = {
            "Event": "Example Game",
            "White": "Magnus",
            "Black": "Hikaru",
            "Result": "1-0",
            "ECO": "C42"
        }
        pgn_data = PGNData(
            game_id=game.game_id,
            pgn_text=pgn_text,
            headers=json.dumps(headers)  # 存储为JSON字符串
        )
        session.add(pgn_data)
        
        # 添加棋步数据
        moves = [
            {
                "move_number": 1,
                "ply_number": 1,
                "color": "white",
                "move_notation": "e4",
                "fen_before": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "fen_after": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                "evaluation": "+0.2",
                "comment": "标准开局"
            },
            {
                "move_number": 1,
                "ply_number": 2,
                "color": "black",
                "move_notation": "e5",
                "fen_before": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                "fen_after": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
                "evaluation": "+0.1",
                "comment": "对称回应"
            }
        ]
        
        for move_data in moves:
            move = Move(game_id=game.game_id, **move_data)
            session.add(move)
        
        # 更新用户统计数据
        users[0].total_games = 1
        users[0].win_games = 1
        users[0].winning_rate = 100.0
        
        users[1].total_games = 1
        users[1].win_games = 0
        users[1].winning_rate = 0.0
        
        session.commit()

class ChessDB:
    """数据库操作类"""
    
    def __init__(self):
        self.session = Session()
    
    # ========== 用户操作 ==========
    def get_user_by_username(self, username):
        """根据用户名获取用户"""
        return self.session.query(User).filter_by(username=username).first()
    
    def add_user(self, username, password_hash, elo_rating=1200):
        """添加新用户"""
        if self.get_user_by_username(username):
            raise ValueError("用户名已存在")
            
        user = User(
            username=username,
            password_hash=password_hash,
            elo_rating=elo_rating,
            total_games=0,
            win_games=0,
            winning_rate=0.0
        )
        self.session.add(user)
        self.session.commit()
        return user
    
    def update_user(self, username, **kwargs):
        """
        更新用户信息
        可更新字段: password_hash, last_login, elo_rating, 
                  total_games, win_games, winning_rate
        """
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError("用户不存在")
            
        allowed_fields = {
            'password_hash', 'last_login', 'elo_rating',
            'total_games', 'win_games', 'winning_rate'
        }
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)
            else:
                raise ValueError(f"不允许更新字段: {field}")
        
        self.session.commit()
        return user
    
    def delete_user(self, username):
        """删除用户及其关联棋局"""
        user = self.get_user_by_username(username)
        if user:
            # 1. 删除用户作为player1的棋局
            games_as_player1 = self.session.query(Game).filter_by(player1_id=user.user_id).all()
            for game in games_as_player1:
                self.delete_game(game.game_id)  # 使用已实现的delete_game方法
            
            # 2. 删除用户作为player2的棋局
            games_as_player2 = self.session.query(Game).filter_by(player2_id=user.user_id).all()
            for game in games_as_player2:
                self.delete_game(game.game_id)
            
            # 3. 删除用户
            self.session.delete(user)
            self.session.commit()
            return True
        return False
    
    # ========== 棋局操作 ==========
    def get_game_by_id(self, game_id):
        """根据ID获取棋局"""
        return self.session.query(Game).get(game_id)
    
    def add_game(self, player1_username, player2_username, result):
        """
        添加新棋局
        参数:
            player1_username: 玩家1用户名
            player2_username: 玩家2用户名
            result: 结果("player1_win"/"player2_win"/"draw")
        返回: 创建的Game对象
        """
        player1 = self.get_user_by_username(player1_username)
        player2 = self.get_user_by_username(player2_username)
        
        if not player1 or not player2:
            raise ValueError("用户不存在")
            
        game = Game(
            player1_id=player1.user_id,
            player2_id=player2.user_id,
            result=result
        )
        self.session.add(game)
        
        # 更新玩家统计信息
        player1.total_games += 1
        player2.total_games += 1
        
        if result == "player1_win":
            player1.win_games += 1
        elif result == "player2_win":
            player2.win_games += 1

        # 计算胜率
        player1.winning_rate = (player1.win_games / player1.total_games) * 100
        player2.winning_rate = (player2.win_games / player2.total_games) * 100
        
        self.session.commit()
        return game
    
    def add_pgn_data(self, game_id, pgn_text, headers=None):
        """
        添加PGN数据
        参数:
            game_id: 关联的棋局ID
            pgn_text: 完整的PGN文本
            headers: PGN头部信息(dict)
        返回: 创建的PGNData对象
        """
        if headers is None:
            headers = {}
            
        pgn_data = PGNData(
            game_id=game_id,
            pgn_text=pgn_text,
            headers=json.dumps(headers)
        )
        self.session.add(pgn_data)
        self.session.commit()
        return pgn_data
    
    def add_move(self, game_id, move_data):
        """
        添加棋步记录
        参数:
            game_id: 关联的棋局ID
            move_data: 包含棋步信息的字典，需要包含:
                - move_number: 完整步数
                - ply_number: 半回合数
                - color: 'white'或'black'
                - move_notation: 棋步表示法(如"e4")
                - fen_before: 走棋前FEN
                - fen_after: 走棋后FEN
                - evaluation: 引擎评价(可选)
                - comment: 注释(可选)
        返回: 创建的Move对象
        """
        required_fields = {
            'move_number', 'ply_number', 'color',
            'move_notation', 'fen_before', 'fen_after'
        }
        
        if not required_fields.issubset(move_data.keys()):
            missing = required_fields - set(move_data.keys())
            raise ValueError(f"缺少必要字段: {missing}")
            
        move = Move(game_id=game_id, **move_data)
        self.session.add(move)
        self.session.commit()
        return move
    
    def update_game(self, game_id, **kwargs):
        """
        更新棋局信息
        可更新字段: result, end_time, eco_code
        """
        # 开始新的事务
        self.session.rollback()  # 清除之前可能的错误状态
        
        game = self.get_game_by_id(game_id)
        if not game:
            raise ValueError("棋局不存在")
            
        allowed_fields = {'result', 'end_time', 'eco_code'}
        for field, value in kwargs.items():
            if field not in allowed_fields:
                raise ValueError(f"不允许更新字段: {field}")
            
            # 特殊验证
            if field == 'result' and value not in ['player1_win', 'player2_win', 'draw']:
                raise ValueError("无效的结果值")
                
            if field == 'end_time' and not isinstance(value, datetime):
                raise ValueError("end_time必须是datetime对象")
        
        # 如果更新结果，需要同步更新用户统计
        if 'result' in kwargs:
            old_result = game.result
            new_result = kwargs['result']
            
            if old_result != new_result:
                player1 = self.session.query(User).get(game.player1_id)
                player2 = self.session.query(User).get(game.player2_id)
                
                # 回滚旧结果的统计
                if old_result == "player1_win":
                    player1.win_games = max(player1.win_games - 1, 0)
                elif old_result == "player2_win":
                    player2.win_games = max(player2.win_games - 1, 0)
                
                # 应用新结果的统计
                if new_result == "player1_win":
                    player1.win_games += 1
                elif new_result == "player2_win":
                    player2.win_games += 1
                
                # 重新计算胜率
                player1.winning_rate = (player1.win_games / player1.total_games) * 100 if player1.total_games > 0 else 0
                player2.winning_rate = (player2.win_games / player2.total_games) * 100 if player2.total_games > 0 else 0
        
        # 执行更新
        for field, value in kwargs.items():
            setattr(game, field, value)
        
        self.session.commit()
        return game

    
    def update_pgn_data(self, game_id, pgn_text=None, headers=None):
        """
        更新PGN数据
        参数:
            game_id: 关联的棋局ID
            pgn_text: 新的PGN文本(可选)
            headers: 新的头部信息(可选)
        返回: 更新的PGNData对象
        """
        pgn_data = self.session.query(PGNData).filter_by(game_id=game_id).first()
        if not pgn_data:
            raise ValueError("PGN数据不存在")
        
        if pgn_text is not None:
            pgn_data.pgn_text = pgn_text
        if headers is not None:
            pgn_data.headers = json.dumps(headers)  # 确保转换为JSON字符串
        
        self.session.commit()
        return pgn_data
    
    def delete_game(self, game_id):
        """删除棋局(会级联删除相关PGN和棋步数据)"""
        game = self.get_game_by_id(game_id)
        if game:
            # 更新玩家统计信息
            player1 = self.session.query(User).get(game.player1_id)
            player2 = self.session.query(User).get(game.player2_id)
            
            if player1 and player2:
                # 减少总对局数
                player1.total_games = max(player1.total_games - 1, 0)
                player2.total_games = max(player2.total_games - 1, 0)
                
                # 根据实际结果减少胜局数
                if game.result == "player1_win":
                    player1.win_games = max(player1.win_games - 1, 0)
                elif game.result == "player2_win":
                    player2.win_games = max(player2.win_games - 1, 0)
                
                # 打印调试信息（修正标签）
                #print(f"[Delete Game] Before commit: {player1.username} total_games={player1.total_games}, win_games={player1.win_games}")
                #print(f"[Delete Game] Before commit: {player2.username} total_games={player2.total_games}, win_games={player2.win_games}")

                # 断言，确保数据有效
                assert 0 <= player1.win_games <= player1.total_games, f"Error: {player1.username} win_games ({player1.win_games}) > total_games ({player1.total_games})"
                assert 0 <= player2.win_games <= player2.total_games, f"Error: {player2.username} win_games ({player2.win_games}) > total_games ({player2.total_games})"
                
                # 重新计算胜率
                player1.winning_rate = (player1.win_games / player1.total_games) * 100 if player1.total_games > 0 else 0
                player2.winning_rate = (player2.win_games / player2.total_games) * 100 if player2.total_games > 0 else 0
            
            self.session.delete(game)
            self.session.commit()
            return True
        return False
    
    # ========== 查询操作 ==========
    def get_user_games(self, username):
        """获取用户所有棋局"""
        user = self.get_user_by_username(username)
        if not user:
            return []
            
        games_as_player1 = self.session.query(Game).filter_by(player1_id=user.user_id).all()
        games_as_player2 = self.session.query(Game).filter_by(player2_id=user.user_id).all()
        
        return games_as_player1 + games_as_player2
    
    def get_game_moves(self, game_id):
        """获取棋局所有棋步，按顺序返回"""
        return self.session.query(Move).filter_by(game_id=game_id).order_by(Move.move_number, Move.ply_number).all()
    
    def get_pgn_data(self, game_id):
        """获取棋局的PGN数据"""
        pgn_data = self.session.query(PGNData).filter_by(game_id=game_id).first()
        if pgn_data:
            # 创建副本以避免污染原始对象
            pgn_data_copy = PGNData(
                game_id=pgn_data.game_id,
                pgn_text=pgn_data.pgn_text,
                headers=pgn_data.headers
            )
            if pgn_data_copy.headers:
                pgn_data_copy.headers = json.loads(pgn_data_copy.headers)
            return pgn_data_copy
        return None
    
    def get_recent_games(self, limit=10):
        """获取最近棋局，按开始时间降序"""
        return self.session.query(Game).order_by(Game.start_time.desc()).limit(limit).all()
    
    def get_users_by_ranking(self, limit=10):
        """获取玩家排名，按ELO降序"""
        return self.session.query(User).order_by(User.elo_rating.desc()).limit(limit).all()
    
    def get_all_users(self):
        """获取所有用户"""
        return self.session.query(User).all()
    
    # ========== 其他操作 ==========
    def execute_raw_sql(self, sql, params=None):
        """执行原始SQL查询"""
        if params is None:
            params = {}
        return self.session.execute(text(sql), params)
    
    def close(self):
        """关闭数据库连接"""
        self.session.close()