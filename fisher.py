import chess
import chess.engine
import asyncio

class StockfishEngine:
    def __init__(self, stockfish_path: str, default_time_limit: float = 0.1):
        """
        初始化 Stockfish 引擎。
        
        Args:
            stockfish_path (str): Stockfish 可执行文件的完整路径。
            default_time_limit (float): 每次分析的默认思考时间（秒）。
        """
        self.stockfish_path = stockfish_path
        self.default_time_limit = default_time_limit
        self._transport = None  # 用于存储传输对象
        self._engine = None # 用于存储引擎实例

    async def _ensure_engine_running(self):
        """确保 Stockfish 引擎已启动。"""
        print(f"self._engine:", self._engine)
        if self._engine is None:
            try:
                # 尝试启动引擎 - popen_uci 返回 (transport, engine) 元组
                self._transport, self._engine = await chess.engine.popen_uci(self.stockfish_path)
                # 调整引擎选项，例如设置线程数、哈希表大小等
                # await self._engine.configure({"Threads": 4, "Hash": 256}) 
                print(f"Stockfish 引擎已成功启动：{self.stockfish_path}")
            except Exception as e:
                print(f"启动 Stockfish 引擎失败: {e}")
                raise

    def ensure_engine_running_sync(self):
        """同步方式确保 Stockfish 引擎已启动（供主线程初始化用）"""
        asyncio.run(self._ensure_engine_running())

    async def get_best_moves(self, fen_string: str, num_moves: int = 3, time_limit: float = None) -> list[str]:
        """
        获取当前棋局下 Stockfish 推荐的最优走法序列。

        Args:
            fen_string (str): 当前棋局的 FEN 字符串。
            num_moves (int): 希望获取的最优走法的数量，默认为 3 个。
            time_limit (float, optional): 引擎思考的时间限制（秒）。
                                          如果为 None，则使用初始化时设置的 default_time_limit。

        Returns:
            list[str]: 一个字符串列表，包含 Stockfish 推荐的最优走法序列。
                       列表中的走法是 UCI 格式（例如 "e2e4"）。
                       如果无法获取走法，则返回空列表。
        """
        await self._ensure_engine_running() # 确保引擎已启动并连接

        if self._engine is None:
            return [] # 如果引擎未启动，则返回空列表

        try:
            board = chess.Board(fen_string)
            
            # 检查棋局是否已结束
            if board.is_game_over():
                print("棋局已结束，无法生成走法。")
                return []

            limit = chess.engine.Limit(time=time_limit if time_limit is not None else self.default_time_limit)
            
            # 使用 analyse 方法获取多个最优走法
            # multipv 参数告诉引擎返回多个最佳走法
            info = await self._engine.analyse(board, limit, multipv=num_moves)
            
            moves = []
            for entry in info:
                if "pv" in entry and entry["pv"]:
                    # pv (principal variation) 是引擎认为的最佳走法序列
                    # 我们可以取序列的第一个走法作为当前局面下的最优解
                    moves.append(entry["pv"][0].uci()) 
            
            return moves

        except ValueError as e:
            print(f"无效的 FEN 字符串: {fen_string} - {e}")
            return []
        except Exception as e:
            print(f"分析棋局时发生错误: {e}")
            return []

    def get_best_move_sync(self, fen_string: str, time_limit: float = None) -> str:
        """
        同步方式获取最佳走法（专为Flask等同步环境设计）
        
        Args:
            fen_string (str): 当前棋局的 FEN 字符串
            time_limit (float): 思考时间限制
            
        Returns:
            str: UCI格式的最佳走法，如果无法获取则返回None
        """
        try:
            # 使用简单的同步方式直接创建引擎
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                board = chess.Board(fen_string)
                
                if board.is_game_over():
                    print("棋局已结束，无法生成走法。")
                    return None
                
                # 设置思考时间
                limit = chess.engine.Limit(time=time_limit if time_limit is not None else self.default_time_limit)
                
                # 获取最佳走法
                result = engine.play(board, limit)
                return result.move.uci() if result.move else None
                
        except Exception as e:
            print(f"同步获取走法失败: {e}")
            return None

    async def quit_engine(self):
        """关闭 Stockfish 引擎。"""
        if self._engine:
            await self._engine.quit()
            self._engine = None
            self._transport = None
            print("Stockfish 引擎已关闭。")