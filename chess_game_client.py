import requests

# API服务器地址
BASE_URL = "http://127.0.0.1:8000"

# 获取令牌
def get_token(username, password):
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
    if response.status_code == 200:
        return response.json().get("token")
    else:
        print(f"获取令牌失败: {response.status_code} - {response.text}")
        return None

# 注册用户
def register_user(username, password):
    data = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
    if response.status_code == 201:
        print(f"用户 {username} 注册成功。")
        return response.json().get("token")
    else:
        print(f"注册用户失败: {response.status_code} - {response.text}")
        return None

# 创建新对弈
def create_match(token, color="white", difficulty="easy"):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"color": color, "difficulty": difficulty}
    response = requests.post(f"{BASE_URL}/api/game/match", headers=headers, json=data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"创建新对弈失败: {response.status_code} - {response.text}")
        return None

# 获取特定游戏详情
def get_game_details(game_id, token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"{BASE_URL}/api/game/{game_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取游戏详情失败: {response.status_code} - {response.text}")
        return None

# 走棋
def make_move(token, game_id, move):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"move": move}
    response = requests.post(f"{BASE_URL}/api/game/{game_id}/move", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"走棋失败: {response.status_code} - {response.text}")
        return None

# 认输
def resign_game(token, game_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/game/{game_id}/resign", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"认输失败: {response.status_code} - {response.text}")
        return None

# 获取用户个人资料
def get_user_profile(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/user/profile", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取用户资料失败: {response.status_code} - {response.text}")
        return None

# 获取用户历史对局
def get_user_history(token, page=1, limit=10, sort='date_desc'):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page": page, "limit": limit, "sort": sort}
    response = requests.get(f"{BASE_URL}/api/user/history", headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取历史对局失败: {response.status_code} - {response.text}")
        return None

# 获取特定对局的详细复盘数据
def get_game_replay(token, game_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/user/history/{game_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取复盘数据失败: {response.status_code} - {response.text}")
        return None

# 获取排行榜
def get_rankings(token, limit=10):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": limit}
    response = requests.get(f"{BASE_URL}/api/users/ranking", headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取排行榜失败: {response.status_code} - {response.text}")
        return None

def play_interactive_game():
    """交互式游戏客户端"""
    # 用户手动输入用户名和密码
    username = input("请输入用户名: ").strip()
    password = input("请输入密码: ").strip()
    token = get_token(username, password)

    # 登录失败且用户名不存在时询问是否注册
    if not token:
        print("登录失败，是否注册新用户？(y/n): ", end="")
        choice = input().strip().lower()
        if choice == 'y':
            reg_token = register_user(username, password)
            if reg_token:
                print("注册并登录成功！")
                token = reg_token
            else:
                print("无法注册新用户，程序退出。")
                return
        else:
            print("未注册新用户，程序退出。")
            return

    if not token:
        print("无法继续操作，未获取到有效令牌。")
        return

    print("\n=== 国际象棋对弈开始 ===")
    
    # 选择颜色
    print("选择你的颜色:")
    print("1. 白棋 (先手)")
    print("2. 黑棋 (后手)")
    color_choice = input("请选择 (1/2): ").strip()
    user_color = "white" if color_choice == "1" else "black"
    
    # 选择难度
    print("选择AI难度:")
    print("1. 简单")
    print("2. 中等")
    print("3. 困难")
    diff_choice = input("请选择 (1/2/3): ").strip()
    difficulty_map = {"1": "easy", "2": "medium", "3": "hard"}
    difficulty = difficulty_map.get(diff_choice, "easy")
    
    # 创建新对弈
    new_game = create_match(token, color=user_color, difficulty=difficulty)
    if not new_game:
        print("创建对弈失败")
        return
    
    game_id = new_game.get("gameId")
    print(f"\n游戏创建成功！游戏ID: {game_id}")
    print(f"你的颜色: {user_color}")
    print(f"AI难度: {difficulty}")
    
    # 游戏循环
    while True:
        # 获取游戏状态
        game_details = get_game_details(game_id, token)
        if not game_details:
            print("获取游戏状态失败")
            break
        
        current_player = game_details.get("currentPlayer")
        status = game_details.get("status")
        result = game_details.get("result")
        moves = game_details.get("moves", [])
        
        print(f"\n当前轮到: {current_player}")
        print(f"已走步数: {len(moves)}")
        if moves:
            print(f"最后一步: {moves[-1]}")
        
        # 检查游戏是否结束
        if status == "finished":
            print(f"\n=== 游戏结束 ===")
            if result == "win":
                print("恭喜你获胜！")
            elif result == "loss":
                print("你败了，再接再厉！")
            else:
                print("平局！")
            break
        
        # 如果轮到用户
        if current_player == user_color:
            print("\n轮到你走棋了！")
            print("输入走法 (如: e2e4) 或 'resign' 认输或 'quit' 退出:")
            user_input = input(">>> ").strip().lower()
            
            if user_input == 'quit':
                print("退出游戏")
                break
            elif user_input == 'resign':
                print("你选择认输")
                resign_result = resign_game(token, game_id)
                print("游戏结束")
                break
            else:
                # 尝试走棋
                move_result = make_move(token, game_id, user_input)
                if move_result:
                    print(f"你的走法: {user_input}")
                    if move_result.get("aiMove"):
                        print(f"AI应对: {move_result.get('aiMove')}")
                    
                    # 检查游戏结果
                    if move_result.get("result") != "ongoing":
                        result = move_result.get("result")
                        print(f"\n=== 游戏结束 ===")
                        if result == "win":
                            print("恭喜你获胜！")
                        elif result == "loss":
                            print("你败了，再接再厉！")
                        else:
                            print("平局！")
                        break
                else:
                    print("走法无效，请重新输入")
        else:
            print("等待AI走棋...")
            import time
            time.sleep(1)  # 等待AI走棋

def show_user_profile(token):
    """显示用户个人资料"""
    print("\n=== 个人资料 ===")
    profile = get_user_profile(token)
    if profile:
        print(f"用户ID: {profile.get('id')}")
        print(f"用户名: {profile.get('username')}")
        print(f"邮箱: {profile.get('email')}")
        print(f"注册时间: {profile.get('createdAt', 'N/A')}")
        
        stats = profile.get('stats', {})
        print(f"\n=== 对局统计 ===")
        print(f"总对局数: {stats.get('totalGames', 0)}")
        print(f"胜利场数: {stats.get('wins', 0)}")
        print(f"失败场数: {stats.get('losses', 0)}")
        print(f"平局场数: {stats.get('draws', 0)}")
        print(f"胜率: {stats.get('winRate', 0):.1%}")
    else:
        print("无法获取个人资料")

def show_user_history(token):
    """显示用户历史对局"""
    print("\n=== 历史对局 ===")
    
    # 获取排序选项
    print("选择排序方式:")
    print("1. 按时间倒序 (最新的在前)")
    print("2. 按时间正序 (最旧的在前)")
    print("3. 只显示胜利的对局")
    print("4. 只显示失败的对局")
    
    sort_choice = input("请选择排序方式 (1-4): ").strip()
    sort_map = {
        "1": "date_desc",
        "2": "date_asc", 
        "3": "result_win",
        "4": "result_loss"
    }
    sort_type = sort_map.get(sort_choice, "date_desc")
    
    # 获取显示数量
    try:
        limit = int(input("显示多少条记录 (默认10): ").strip() or "10")
        limit = min(max(1, limit), 50)  # 限制在1-50之间
    except ValueError:
        limit = 10
    
    history = get_user_history(token, page=1, limit=limit, sort=sort_type)
    if not history:
        print("无法获取历史对局")
        return
    
    games = history.get('games', [])
    pagination = history.get('pagination', {})
    
    print(f"\n找到 {pagination.get('total', 0)} 条对局记录，显示前 {len(games)} 条:")
    print("-" * 80)
    
    for i, game in enumerate(games, 1):
        result_color = {
            'win': '🏆',
            'loss': '❌', 
            'draw': '⚖️'
        }.get(game.get('result'), '❓')
        
        print(f"{i:2d}. {result_color} vs {game.get('opponent', 'Unknown')}")
        print(f"    时间: {game.get('date', 'N/A')[:19] if game.get('date') else 'N/A'}")
        print(f"    颜色: {'白棋' if game.get('userColor') == 'white' else '黑棋'}")
        print(f"    步数: {game.get('moveCount', 0)}")
        print(f"    时长: {game.get('duration', 0)//60}分{game.get('duration', 0)%60}秒")
        
        # 询问是否查看详细复盘
        view_detail = input(f"    查看详细复盘? (y/n): ").strip().lower()
        if view_detail == 'y':
            show_game_replay(token, game.get('gameId'))
        print()

def show_game_replay(token, game_id):
    """显示对局复盘"""
    print(f"\n=== 对局复盘 (ID: {game_id}) ===")
    
    replay = get_game_replay(token, game_id)
    if not replay:
        print("无法获取复盘数据")
        return
    
    moves = replay.get('moves', [])
    comments = replay.get('comments', [])
    
    print(f"走法序列 ({len(moves)} 步):")
    for i, move in enumerate(moves):
        move_num = i // 2 + 1
        color = "白" if i % 2 == 0 else "黑"
        print(f"{move_num:2d}. {color}: {move}")
        
        # 显示评论
        for comment in comments:
            if comment.get('moveIndex') == i:
                if comment.get('userComment'):
                    print(f"    💬 {comment.get('userComment')}")
                if comment.get('aiComment'):
                    print(f"    🤖 {comment.get('aiComment')}")
    
    print(f"\n对局信息:")
    print(f"总步数: {len(moves)}")
    print(f"开始时间: {replay.get('timestamps', [None])[0] if replay.get('timestamps') else 'N/A'}")

def show_rankings(token):
    """显示排行榜"""
    print("\n=== 排行榜 ===")
    
    try:
        limit = int(input("显示前多少名 (默认10): ").strip() or "10")
        limit = min(max(1, limit), 50)
    except ValueError:
        limit = 10
    
    rankings = get_rankings(token, limit)
    if not rankings:
        print("无法获取排行榜")
        return
    
    users = rankings.get('users', [])
    print(f"\n排行榜 (前{len(users)}名):")
    print("-" * 60)
    print(f"{'排名':<4} {'用户名':<15} {'等级分':<8} {'总局数':<6} {'胜率':<8}")
    print("-" * 60)
    
    for i, user in enumerate(users, 1):
        username = user.get('username', 'N/A')
        elo = user.get('elo_rating', 0)
        total_games = user.get('total_games', 0)
        win_rate = user.get('winning_rate', 0)
        
        print(f"{i:<4} {username:<15} {elo:<8} {total_games:<6} {win_rate:<8.1f}%")

def main_menu(token, username):
    """主菜单"""
    while True:
        print("\n=== 国际象棋游戏客户端 ===")
        print("1. 开始新对弈")
        print("2. 查看个人资料")
        print("3. 查看历史对局")
        print("4. 查看排行榜")
        print("5. 退出")
        
        choice = input("请选择功能 (1-5): ").strip()
        
        if choice == "1":
            start_new_game(token)
        elif choice == "2":
            show_user_profile(token)
        elif choice == "3":
            show_user_history(token)
        elif choice == "4":
            show_rankings(token)
        elif choice == "5":
            print("再见！")
            break
        else:
            print("无效选择，请重新输入")

def start_new_game(token):
    """开始新对弈"""
    print("\n=== 开始新对弈 ===")
    
    # 选择颜色
    print("选择你的颜色:")
    print("1. 白棋 (先手)")
    print("2. 黑棋 (后手)")
    color_choice = input("请选择 (1/2): ").strip()
    user_color = "white" if color_choice == "1" else "black"
    
    # 选择难度
    print("选择AI难度:")
    print("1. 简单")
    print("2. 中等")
    print("3. 困难")
    diff_choice = input("请选择 (1/2/3): ").strip()
    difficulty_map = {"1": "easy", "2": "medium", "3": "hard"}
    difficulty = difficulty_map.get(diff_choice, "easy")
    
    # 创建新对弈
    new_game = create_match(token, color=user_color, difficulty=difficulty)
    if not new_game:
        print("创建对弈失败")
        return
    
    game_id = new_game.get("gameId")
    print(f"\n游戏创建成功！游戏ID: {game_id}")
    print(f"你的颜色: {user_color}")
    print(f"AI难度: {difficulty}")
    
    # 开始游戏循环
    play_game_loop(token, game_id, user_color)

def play_game_loop(token, game_id, user_color):
    """游戏循环"""
    while True:
        # 获取游戏状态
        game_details = get_game_details(game_id, token)
        if not game_details:
            print("获取游戏状态失败")
            break
        
        current_player = game_details.get("currentPlayer")
        status = game_details.get("status")
        result = game_details.get("result")
        moves = game_details.get("moves", [])
        
        print(f"\n当前轮到: {current_player}")
        print(f"已走步数: {len(moves)}")
        if moves:
            print(f"最后一步: {moves[-1]}")
        
        # 检查游戏是否结束
        if status == "finished":
            print(f"\n=== 游戏结束 ===")
            if result == "win":
                print("🏆 恭喜你获胜！")
            elif result == "loss":
                print("❌ 你败了，再接再厉！")
            else:
                print("⚖️ 平局！")
            break
        
        # 如果轮到用户
        if current_player == user_color:
            print("\n轮到你走棋了！")
            print("输入走法 (如: e2e4) 或 'resign' 认输或 'back' 返回主菜单:")
            user_input = input(">>> ").strip().lower()
            
            if user_input == 'back':
                print("返回主菜单")
                break
            elif user_input == 'resign':
                print("你选择认输")
                resign_result = resign_game(token, game_id)
                print("游戏结束")
                break
            else:
                # 尝试走棋
                move_result = make_move(token, game_id, user_input)
                if move_result:
                    print(f"你的走法: {user_input}")
                    if move_result.get("aiMove"):
                        print(f"AI应对: {move_result.get('aiMove')}")
                    
                    # 检查游戏结果
                    if move_result.get("result") != "ongoing":
                        result = move_result.get("result")
                        print(f"\n=== 游戏结束 ===")
                        if result == "win":
                            print("🏆 恭喜你获胜！")
                        elif result == "loss":
                            print("❌ 你败了，再接再厉！")
                        else:
                            print("⚖️ 平局！")
                        break
                else:
                    print("走法无效，请重新输入")
        else:
            print("等待AI走棋...")
            import time
            time.sleep(1)  # 等待AI走棋

if __name__ == "__main__":
    play_interactive_game()
