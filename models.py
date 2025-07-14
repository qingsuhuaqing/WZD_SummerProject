from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Text, TIMESTAMP, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    """用户表模型"""
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_login = Column(TIMESTAMP)
    elo_rating = Column(Integer, default=1200)
    total_games = Column(Integer, default=0)
    win_games = Column(Integer, default=0)
    winning_rate = Column(DECIMAL(5, 2), default=0.0)
    
    # 关系
    games_as_player1 = relationship("Game", foreign_keys="Game.player1_id", back_populates="player1")
    games_as_player2 = relationship("Game", foreign_keys="Game.player2_id", back_populates="player2")

class Game(Base):
    """棋局表模型"""
    __tablename__ = 'games'
    
    game_id = Column(Integer, primary_key=True)
    player1_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    player2_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    result = Column(Enum('player1_win', 'player2_win', 'draw', name='game_result'))
    start_time = Column(TIMESTAMP, server_default=func.now())
    end_time = Column(TIMESTAMP)
    
    # 关系
    player1 = relationship("User", foreign_keys=[player1_id], back_populates="games_as_player1")
    player2 = relationship("User", foreign_keys=[player2_id], back_populates="games_as_player2")
    # Game类中添加 cascade 参数
    moves = relationship("Move", back_populates="game", order_by="Move.move_number", cascade="all, delete-orphan")
    pgn_data = relationship("PGNData", uselist=False, back_populates="game", cascade="all, delete-orphan")


class PGNData(Base):
    """PGN棋谱数据表模型"""
    __tablename__ = 'pgn_data'
    
    pgn_id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.game_id'), unique=True)
    pgn_text = Column(Text, nullable=False)
    headers = Column(Text)  # 存储为JSON字符串
    
    # 关系
    game = relationship("Game", back_populates="pgn_data")

class Move(Base):
    """走棋记录表模型"""
    __tablename__ = 'moves'
    
    move_id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.game_id'), nullable=False)
    move_number = Column(Integer, nullable=False)
    ply_number = Column(Integer, nullable=False)
    color = Column(Enum('white', 'black', name='move_color'), nullable=False)
    move_notation = Column(String(10), nullable=False)
    fen_before = Column(String(100), nullable=False)
    fen_after = Column(String(100), nullable=False)
    evaluation = Column(String(20))
    comment = Column(Text)
    
    # 关系
    game = relationship("Game", back_populates="moves")