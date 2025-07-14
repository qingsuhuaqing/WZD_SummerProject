import os
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, User, Game, PGNData, Move

# 使用SQLite进行本地测试
DATABASE_URI = "sqlite:///chess_games_local.db"

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

1. e4 e5 2. Nf3 Nf6 3. Nxe5 d6 4. Nf3 Nxe4 5. d3 Nf6 6. d4 d5 7. Bd3 Be7
8. O-O O-O 9. c4 c6 10. Nc3 Re8 11. cxd5 cxd5 12. Qc2 Nc6 13. a3 Be6
14. Bf4 Rc8 15. Qb3 Na5 16. Qa2 Nc4 17. Bxc4 Rxc4 18. Ne5 Rc2 19. Qb3 Qd6
20. f3 Rec8 21. Rad1 Nh5 22. Be3 Nf6 23. Nd3 R8c3 24. Qb4 Qxb4 25. axb4 Rxb2
26. Ra1 a6 27. Rfc1 Rcc2 28. Rxc2 Rxc2 29. Kf1 Nd7 30. Ra5 Nb6 31. Rxd5 Nxd5
32. Nxd5 Bxd5 33. Ne5 f6 34. Nd7 Kf7 35. Nb8 Ra2 36. Nxa6 Ra1+ 37. Ke2 Rb1
38. Nc5 Rxb4 39. Nxb7 Rb2+ 40. Kf1 f5 41. Nd6+ Ke6 42. Nf7 Kf6 43. Ng5 Be6
44. Nxe6 Kxe6 45. g3 Kd5 46. Kg1 Kc4 47. Kf1 Kd3 48. Kg1 Ke2 49. Kh1 Kf1
50. Bg1 Rb1 51. Kh2 Be1 52. Kg2 Bd2 53. Kh3 Be1 54. Kg2 Bd2 55. Kh3 Be1
56. Kg2 Bd2 1-0
"""
        
        headers = json.dumps({
            "Event": "Example Game",
            "Site": "?",
            "Date": "2023.05.15",
            "Round": "?",
            "White": "Magnus",
            "Black": "Hikaru",
            "Result": "1-0",
            "ECO": "C42"
        })
        
        pgn_data = PGNData(
            game_id=game.game_id,
            pgn_text=pgn_text.strip(),
            headers=headers
        )
        session.add(pgn_data)
        
        # 添加几步走法示例
        moves_data = [
            {"move_number": 1, "ply_number": 1, "move_notation": "e4", "color": "white", "fen_after_move": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"},
            {"move_number": 1, "ply_number": 2, "move_notation": "e5", "color": "black", "fen_after_move": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"},
            {"move_number": 2, "ply_number": 3, "move_notation": "Nf3", "color": "white", "fen_after_move": "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"}
        ]
        
        for move_data in moves_data:
            move = Move(
                game_id=game.game_id,
                move_number=move_data["move_number"],
                ply_number=move_data["ply_number"],
                move_notation=move_data["move_notation"],
                color=move_data["color"],
                fen_after_move=move_data["fen_after_move"]
            )
            session.add(move)
        
        session.commit()
        print(f"✅ 已添加示例数据：用户 {len(users)} 个，棋局 1 个，走法 {len(moves_data)} 步")


class ChessDB:
    """国际象棋数据库操作类 - SQLite版本用于测试"""
    
    def __init__(self):
        self.session = Session()
    
    def close(self):
        """关闭数据库连接"""
        self.session.close()
    
    # 用户相关操作
    def add_user(self, username, password_hash, elo_rating=1200):
        """添加新用户"""
        user = User(
            username=username,
            password_hash=password_hash,
            elo_rating=elo_rating
        )
        self.session.add(user)
        self.session.commit()
        return user
    
    def get_user_by_username(self, username):
        """根据用户名获取用户"""
        return self.session.query(User).filter_by(username=username).first()
    
    def get_users_by_ranking(self, limit=10):
        """获取排名前N的用户"""
        return self.session.query(User).order_by(User.elo_rating.desc()).limit(limit).all()
    
    # 棋局相关操作
    def add_game(self, player1_username, player2_username, result=None):
        """添加新棋局"""
        player1 = self.get_user_by_username(player1_username)
        player2 = self.get_user_by_username(player2_username)
        
        if not player1 or not player2:
            raise ValueError("玩家不存在")
        
        game = Game(
            player1_id=player1.user_id,
            player2_id=player2.user_id,
            result=result
        )
        self.session.add(game)
        self.session.commit()
        return game
    
    def get_game_by_id(self, game_id):
        """根据ID获取棋局"""
        return self.session.query(Game).filter_by(game_id=game_id).first()
    
    def get_user_games(self, username):
        """获取用户的所有棋局"""
        user = self.get_user_by_username(username)
        if not user:
            return []
        
        return self.session.query(Game).filter(
            (Game.player1_id == user.user_id) | (Game.player2_id == user.user_id)
        ).all()
    
    # PGN相关操作
    def add_pgn_data(self, game_id, pgn_text, headers=None):
        """添加PGN数据"""
        headers_json = json.dumps(headers) if headers else None
        pgn_data = PGNData(
            game_id=game_id,
            pgn_text=pgn_text,
            headers=headers_json
        )
        self.session.add(pgn_data)
        self.session.commit()
        return pgn_data
    
    def get_pgn_data(self, game_id):
        """获取PGN数据"""
        return self.session.query(PGNData).filter_by(game_id=game_id).first()
    
    # 走法相关操作
    def add_move(self, game_id, move_data):
        """添加走法"""
        move = Move(
            game_id=game_id,
            move_number=move_data.get("move_number"),
            ply_number=move_data.get("ply_number"),
            move_notation=move_data.get("move_notation"),
            color=move_data.get("color"),
            fen_after_move=move_data.get("fen_after_move")
        )
        self.session.add(move)
        self.session.commit()
        return move
    
    def get_game_moves(self, game_id):
        """获取棋局的所有走法"""
        return self.session.query(Move).filter_by(game_id=game_id).order_by(Move.ply_number).all()
