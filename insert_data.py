from dao import init_db, add_sample_data, ChessDB
from datetime import datetime
import json


def test_database_operations():
    # 初始化数据库（强制重建）
    print("初始化数据库...")
    init_db(drop_existing=True)
    add_sample_data()

    # 创建数据库操作实例
    db = ChessDB()

    try:
        print("\n=== 测试用户操作 ===")
        # 1. 添加新用户
        print("1. 添加新用户")
        new_user = db.add_user("alice", "alice_hash", 1500)
        print(f"添加用户: {new_user.username} (ELO: {new_user.elo_rating})")

        # 2. 更新用户信息
        print("\n2. 更新用户信息")
        updated_user = db.update_user(
            "alice",
            elo_rating=1520,
            last_login=datetime.now()
        )
        print(f"更新用户ELO: {updated_user.elo_rating}")
        print(f"最后登录时间: {updated_user.last_login}")

        # 3. 查询用户
        print("\n3. 查询用户")
        user = db.get_user_by_username("magnus")
        print(f"用户信息: {user.username}, ELO: {user.elo_rating}, 胜率: {user.winning_rate}%")

        print("\n=== 测试棋局操作 ===")
        # 4. 添加新棋局
        print("4. 添加新棋局")
        game = db.add_game("alice", "magnus", "player2_win")
        print(f"添加棋局ID: {game.game_id}, 结果: {game.result}")

        # 5. 添加PGN数据
        print("\n5. 添加PGN数据")
        pgn_text = """
[Event "Test Game"]
[White "Alice"]
[Black "Magnus"]
[Result "0-1"]
[ECO "B20"]

1. e4 c5 2. Nf3 Nc6 3. Bb5 g6 4. O-O Bg7 5. c3 Nf6 *
"""
        headers = {
            "Event": "Test Game",
            "White": "Alice",
            "Black": "Magnus",
            "Result": "0-1",
            "ECO": "B20"
        }
        pgn_data = db.add_pgn_data(game.game_id, pgn_text, headers)
        print(f"添加PGN数据成功，ID: {pgn_data.pgn_id}")

        # 6. 添加棋步记录
        print("\n6. 添加棋步记录")
        moves = [
            {
                "move_number": 1,
                "ply_number": 1,
                "color": "white",
                "move_notation": "e4",
                "fen_before": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "fen_after": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                "evaluation": "+0.3",
                "comment": "标准开局"
            },
            {
                "move_number": 1,
                "ply_number": 2,
                "color": "black",
                "move_notation": "c5",
                "fen_before": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                "fen_after": "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
                "evaluation": "+0.1",
                "comment": "西西里防御"
            }
        ]

        for move_data in moves:
            move = db.add_move(game.game_id, move_data)
            print(f"添加棋步: {move.move_notation} (回合 {move.move_number})")

        # 7. 查询棋局信息
        print("\n7. 查询棋局信息")
        game_moves = db.get_game_moves(game.game_id)
        print(f"棋局 {game.game_id} 共有 {len(game_moves)} 步棋")
        for i, move in enumerate(game_moves[:3]):  # 只打印前3步
            print(f"第 {move.move_number}.{move.ply_number} 步: {move.color} {move.move_notation}")

        # 8. 查询PGN数据
        print("\n8. 查询PGN数据")
        pgn_data = db.get_pgn_data(game.game_id)
        if pgn_data:
            print(f"PGN头部信息: {pgn_data.headers}")
            print(f"PGN文本前50字符: {pgn_data.pgn_text[:50]}...")
        else:
            print("未找到PGN数据")

        # 9. 更新棋局基本信息
        print("\n9. 更新棋局基本信息")
        try:
            # 先确保回滚任何之前的事务
            db.session.rollback()
            
            # 更新棋局基本信息
            updated_game = db.update_game(
                game.game_id,
                result="draw",
                end_time=datetime.now(),
                eco_code="D02"
            )
            print(f"成功更新棋局: ID {updated_game.game_id}")
            print(f"新结果: {updated_game.result}")
            print(f"结束时间: {updated_game.end_time}")
            print(f"ECO代码: {updated_game.eco_code}")
            
            # 验证更新
            refreshed_game = db.get_game_by_id(game.game_id)
            print("验证结果:")
            print(f"结果: {refreshed_game.result}")
            print(f"结束时间: {refreshed_game.end_time}")
            print(f"ECO代码: {refreshed_game.eco_code}")
            
        except Exception as e:
            print(f"更新棋局时出错: {e}")
            # 打印更详细的错误信息
            import traceback
            traceback.print_exc()
            
            # 检查游戏状态
            game_state = db.get_game_by_id(game.game_id)
            print(f"当前游戏状态: 结果={game_state.result if game_state else 'None'}")

        # 10. 更新PGN数据
        print("\n10. 更新PGN数据")
        updated_headers = {
            "Event": "Updated Test Game",
            "White": "Alice (Updated)",
            "Black": "Magnus (Updated)",
            "Result": "1/2-1/2",  # 平局
            "ECO": "D02",
            "NewField": "Additional Info"
        }
        updated_pgn = db.update_pgn_data(
            game.game_id,
            pgn_text="[Event \"Updated Game\"]\n1. e4 *",
            headers=updated_headers
        )
        print("PGN数据更新成功")

        # 验证更新
        updated_pgn = db.get_pgn_data(game.game_id)
        print(f"更新后PGN头部: {updated_pgn.headers}")
        print(f"更新后PGN文本: {updated_pgn.pgn_text[:50]}...")

        # 11. 查询用户棋局
        print("\n11. 查询用户棋局")
        alice_games = db.get_user_games("alice")
        print(f"Alice参与的对局数: {len(alice_games)}")

        # 12. 测试删除操作
        print("\n=== 测试删除操作 ===")

        # 先查询当前用户统计
        alice_before = db.get_user_by_username("alice")
        magnus_before = db.get_user_by_username("magnus")
        print(f"Alice原对局数: {alice_before.total_games}, 胜局: {alice_before.win_games}")
        print(f"Magnus原对局数: {magnus_before.total_games}, 胜局: {magnus_before.win_games}")

        # 删除棋局
        print("\n12. 删除棋局")
        if alice_games:
            db.delete_game(alice_games[0].game_id)
            print(f"已删除棋局 ID: {alice_games[0].game_id}")

            # 验证统计更新
            alice_after = db.get_user_by_username("alice")
            magnus_after = db.get_user_by_username("magnus")
            print(f"Alice更新后对局数: {alice_after.total_games}, 胜局: {alice_after.win_games}")
            print(f"Magnus更新后对局数: {magnus_after.total_games}, 胜局: {magnus_after.win_games}")

        # 13. 查询排名
        print("\n13. 查询玩家排名")
        top_players = db.get_users_by_ranking(3)
        print("Top 3 玩家:")
        for i, player in enumerate(top_players, 1):
            print(f"{i}. {player.username}: ELO {player.elo_rating}, 胜率 {player.winning_rate}%")

    except Exception as e:
        print(f"\n发生错误: {e}")
    finally:
        db.close()
        print("\n测试完成，数据库连接已关闭")


if __name__ == "__main__":
    test_database_operations()