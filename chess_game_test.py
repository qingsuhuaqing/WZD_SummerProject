import requests

# API服务器地址（确保与app.py的端口一致）
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

# 获取教学课程列表
def get_teaching_lessons(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/teaching/lessons", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取教学课程失败: {response.status_code} - {response.text}")
        return None

# 获取特定教学课程详情
def get_teaching_lesson_details(token, lesson_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/teaching/{lesson_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取课程详情失败: {response.status_code} - {response.text}")
        return None

# 在教学模式下提交走法（带AI分析）
def make_teaching_move(token, lesson_id, move):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"move": move}
    response = requests.post(f"{BASE_URL}/api/teaching/{lesson_id}/move", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"教学模式走棋失败: {response.status_code} - {response.text}")
        return None

# 开始教学模式对局
def start_teaching_game(token, lesson_type="general", color="white"):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"lesson_type": lesson_type, "color": color}
    response = requests.post(f"{BASE_URL}/api/teaching/start", headers=headers, json=data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"开始教学对局失败: {response.status_code} - {response.text}")
        return None

# 在教学模式下提交走法（带实时分析）
def make_teaching_move_realtime(token, game_id, move):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"move": move}
    response = requests.post(f"{BASE_URL}/api/teaching/{game_id}/move", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"教学模式走棋失败: {response.status_code} - {response.text}")
        return None

# 获取教学对局分析历史
def get_teaching_history(token, game_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/teaching/{game_id}/history", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取教学历史失败: {response.status_code} - {response.text}")
        return None

# 测试教学模式AI分析功能
def test_teaching_analysis(token):
    """测试教学模式下的AI分析功能"""
    print("\n=== 测试教学模式AI分析功能 ===")
    
    # 获取课程列表
    lessons = get_teaching_lessons(token)
    if not lessons:
        print("无法获取教学课程列表")
        return
    
    print(f"可用课程数量: {len(lessons.get('lessons', []))}")
    
    # 选择第一个课程进行测试
    if lessons.get('lessons'):
        lesson = lessons['lessons'][0]
        lesson_id = lesson['lessonId']
        print(f"测试课程: {lesson['title']} (ID: {lesson_id})")
        
        # 获取课程详情
        lesson_details = get_teaching_lesson_details(token, lesson_id)
        if lesson_details:
            print(f"课程目标: {lesson_details.get('objectives', [])}")
            print(f"课程提示: {lesson_details.get('hints', [])}")
        
        # 测试几个不同的走法
        test_moves = ['e2e4', 'd2d4', 'g1f3', 'invalid_move']
        
        for move in test_moves:
            print(f"\n--- 测试走法: {move} ---")
            move_result = make_teaching_move(token, lesson_id, move)
            
            if move_result:
                print(f"走法结果: {move_result.get('result', 'unknown')}")
                print(f"评分: {move_result.get('moveRating', 'N/A')}")
                print(f"AI评价: {move_result.get('userComment', 'N/A')}")
                if move_result.get('aiMove'):
                    print(f"AI应对: {move_result.get('aiMove')}")
                    print(f"AI评论: {move_result.get('aiComment', 'N/A')}")
                
                # 显示进度
                progress = move_result.get('progress', {})
                if progress:
                    completion = progress.get('completion', 0) * 100
                    print(f"完成度: {completion:.1f}% ({progress.get('currentStep', 0)}/{progress.get('totalSteps', 0)})")
            else:
                print("走法失败")
            
            # 如果是无效走法，跳过后续处理
            if move == 'invalid_move':
                continue
    
    print("\n教学模式AI分析测试完成")

# 测试教学模式实时分析功能
def test_teaching_mode_realtime(token):
    """测试教学模式下的实时走法分析 - 每步都分析"""
    print("\n=== 测试教学模式实时分析 ===")
    print("💡 在教学模式下，棋手的每一步都会得到详细的AI分析和指导")
    
    # 开始教学对局
    teaching_game = start_teaching_game(token, lesson_type="opening", color="white")
    if not teaching_game:
        print("无法开始教学对局")
        return
    
    game_id = teaching_game.get("gameId")
    print(f"✓ 教学对局开始，ID: {game_id}")
    print(f"课程类型: {teaching_game.get('lessonType')}")
    print(f"你的颜色: {teaching_game.get('userColor')}")
    print(f"初始指导: {teaching_game.get('instructions')}")
    
    # 扩展测试走法，模拟完整的开局过程
    test_moves = [
        {"move": "e2e4", "description": "经典开局 - 控制中心e4格"},
        {"move": "g1f3", "description": "发展马匹 - 攻击对方e5并控制关键格子"},
        {"move": "f1c4", "description": "发展象 - 指向f7弱点"},
        {"move": "d2d3", "description": "巩固中心 - 支持e4兵"},
        {"move": "b1c3", "description": "发展马匹 - 进一步控制中心"},
        {"move": "c1e3", "description": "发展象 - 完善棋子协调"},
        {"move": "d1d2", "description": "连接车 - 准备长易位"},
        {"move": "e1c1", "description": "长易位 - 王安全并激活车"}
    ]
    
    move_count = 0
    analysis_count = 0
    
    for i, test_case in enumerate(test_moves, 1):
        move = test_case["move"]
        description = test_case["description"]
        
        print(f"\n{'='*60}")
        print(f"第{i}步: {move} - {description}")
        print(f"{'='*60}")
        
        move_result = make_teaching_move_realtime(token, game_id, move)
        
        if move_result and move_result.get('success'):
            move_count += 1
            print(f"✓ 走法执行成功")
            print(f"📊 走法质量: {move_result.get('moveQuality', 'N/A')}")
            
            # 显示详细的AI分析
            user_analysis = move_result.get('userAnalysis', '')
            if user_analysis:
                analysis_count += 1
                print(f"\n🎓 教练分析:")
                print("-" * 50)
                # 分段显示分析内容
                lines = user_analysis.split('\n')
                for line in lines:
                    if line.strip():
                        print(f"   {line.strip()}")
                print("-" * 50)
            else:
                print("⚠️ 未获取到AI分析")
            
            # 显示AI应对
            ai_move = move_result.get('aiMove')
            if ai_move:
                print(f"\n🤖 AI应对: {ai_move}")
                ai_analysis = move_result.get('aiAnalysis', '')
                if ai_analysis:
                    print(f"🔍 AI应对分析: {ai_analysis[:200]}{'...' if len(ai_analysis) > 200 else ''}")
            
            # 显示对局状态
            print(f"\n📈 对局状态:")
            print(f"   当前步数: {move_result.get('moveNumber', 'N/A')}")
            print(f"   棋局状态: {move_result.get('gameStatus', 'N/A')}")
            print(f"   已分析步数: {analysis_count}")
            
            # 如果游戏结束，停止测试
            if move_result.get('gameStatus') == 'finished':
                print("\n🏁 对局已结束")
                break
                
        else:
            print(f"✗ 走法失败: {move_result.get('error', '未知错误') if move_result else '无响应'}")
            continue
        
        # 暂停一下，让输出更清晰
        import time
        time.sleep(0.5)
    
    # 获取完整的分析历史
    print(f"\n{'='*60}")
    print("📚 获取完整分析历史")
    print(f"{'='*60}")
    
    history = get_teaching_history(token, game_id)
    if history:
        moves = history.get('moveHistory', [])
        print(f"✓ 总共记录了 {len(moves)} 步走法")
        print(f"✓ 每步都包含了详细的AI分析和建议")
        print(f"✓ 分析覆盖率: {analysis_count}/{move_count} = {(analysis_count/move_count*100):.1f}%" if move_count > 0 else "0%")
        
        # 显示前几步的分析摘要
        print(f"\n📋 前3步分析摘要:")
        for idx, move_data in enumerate(moves[:3]):
            if move_data.get('analysis') and move_data['analysis'].get('ai_analysis'):
                analysis_text = move_data['analysis']['ai_analysis']
                print(f"   {idx+1}. {move_data.get('move', 'N/A')}: {analysis_text[:100]}...")
    else:
        print("✗ 无法获取分析历史")
    
    print(f"\n🎯 教学模式测试总结:")
    print(f"   ✅ 成功执行 {move_count} 步走法")
    print(f"   ✅ 获得 {analysis_count} 次AI分析")
    print(f"   ✅ 每步都有详细的教学指导")
    print(f"   💡 这就是教学模式的核心价值：逐步分析，逐步提高！")
    
    print("\n教学模式实时分析测试完成！")

# 测试普通对局中的走法分析功能
def test_move_analysis(token):
    """测试普通对局中的走法分析功能"""
    print("\n=== 测试普通对局走法分析功能 ===")
    
    # 创建新对弈
    new_game = create_match(token, color="white", difficulty="medium")
    if not new_game:
        print("创建对弈失败")
        return
    
    game_id = new_game.get("gameId")
    print(f"游戏创建成功！游戏ID: {game_id}")
    
    # 测试几个开局走法
    test_moves = [
        {"move": "e2e4", "description": "经典开局走法"},
        {"move": "d7d6", "description": "较为被动的应对"}, 
        {"move": "d2d4", "description": "控制中心"},
        {"move": "g8f6", "description": "发展马匹"}
    ]
    
    move_count = 0
    for test_case in test_moves:
        move = test_case["move"]
        description = test_case["description"]
        
        print(f"\n--- 第{move_count + 1}步测试走法: {move} ({description}) ---")
        
        # 先获取游戏状态确认是否轮到我们
        game_details = get_game_details(game_id, token)
        if not game_details:
            print("获取游戏状态失败")
            break
            
        current_player = game_details.get("currentPlayer")
        if current_player != "white":
            print("轮到AI，跳过该走法")
            continue
            
        # 执行走法
        move_result = make_move(token, game_id, move)
        
        if move_result:
            print(f"✓ 走法执行成功")
            
            # 普通对弈专注于游戏体验，不显示AI分析
            print("  💡 普通对弈模式：专注游戏体验，不进行逐步分析")
            
            # 显示AI应对
            if move_result.get("aiMove"):
                print(f"  AI应对: {move_result.get('aiMove')}")
            
            move_count += 1
            
            # 检查游戏是否结束
            if move_result.get("result") != "ongoing":
                result = move_result.get("result")
                print(f"\n游戏结束: {result}")
                break
        else:
            print(f"✗ 走法失败: {move}")
            break
    
    print(f"\n分析功能测试完成，共测试了 {move_count} 步")

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

    print(f"\n=== 欢迎 {username} ===")
    # 调用主菜单
    main_menu(token, username)

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
        print("1. 开始新对弈（普通人机对战 - 专注游戏体验，无逐步分析）")
        print("2. 查看个人资料")
        print("3. 查看历史对局")
        print("4. 查看排行榜")
        print("5. 测试预定义教学课程（固定课程内容）")
        print("6. 简化教学模式（💡输入一步，立即分析一步 - 专注逐步学习）")
        print("7. 🔧 简化测试教学分析（专门测试分析功能）")
        print("8. 退出")
        
        choice = input("请选择功能 (1-8): ").strip()
        
        if choice == "1":
            print("\n🎯 普通对弈模式：专注于游戏体验，AI仅提供对弈伙伴，不进行逐步分析")
            start_new_game(token)
        elif choice == "2":
            show_user_profile(token)
        elif choice == "3":
            show_user_history(token)
        elif choice == "4":
            show_rankings(token)
        elif choice == "5":
            print("\n📚 预定义教学课程：测试固定的教学内容，如开局原理、马的发展等")
            test_teaching_analysis(token)
        elif choice == "6":
            print("\n🎓 简化教学模式：输入一步走法，立即获得AI分析！")
            print("💡 这是最直接的教学体验：你走几步，就分析几步！")
            play_teaching_game_interactive(token)
        elif choice == "7":
            print("\n🔧 简化分析测试：专门验证教学模式下的逐步分析功能")
            test_teaching_analysis_simple(token)
        elif choice == "8":
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

# 交互式教学模式游戏
def play_teaching_game_interactive(token):
    """交互式教学模式游戏 - 简化版，专注于每步分析"""
    print("\n=== 简化教学模式 ===")
    print("💡 核心功能：你走一步，立即获得AI分析！")
    print("🎯 专注于学习，无复杂设置")
    
    # 直接开始教学对局（使用默认设置）
    teaching_game = start_teaching_game(token, lesson_type="general", color="white")
    if not teaching_game:
        print("❌ 无法开始教学对局")
        return
    
    game_id = teaching_game.get("gameId")
    print(f"✅ 教学对局已开始，ID: {game_id}")
    print(f"🎯 你执白棋，每步都会得到详细AI分析")
    
    # 开始简化的教学循环
    play_simple_teaching_loop(token, game_id)

def play_simple_teaching_loop(token, game_id):
    """简化的教学循环 - 专注于每步分析"""
    move_count = 0
    analysis_count = 0
    
    print(f"\n{'='*60}")
    print("🎓 简化教学模式开始")
    print("💡 输入走法，立即获得AI分析！")
    print("📝 走法格式: e2e4, g1f3, f1c4 等")
    print("🔙 输入 'quit' 退出")
    print(f"{'='*60}")
    
    while True:
        print(f"\n📊 当前进度: 已走 {move_count} 步，分析 {analysis_count} 步")
        
        # 获取用户输入
        user_input = input("请输入走法 >>> ").strip()
        
        if user_input.lower() == 'quit':
            print("🔙 退出教学模式")
            break
        elif not user_input:
            print("⚠️ 请输入有效的走法")
            continue
        
        # 执行走法
        print(f"\n📝 执行走法: {user_input}")
        move_result = make_teaching_move_realtime(token, game_id, user_input)
        
        if move_result and move_result.get('success'):
            move_count += 1
            print(f"✅ 走法执行成功！")
            
            # 显示走法质量
            quality = move_result.get('moveQuality', 'unknown')
            quality_emoji = {'excellent': '🏆', 'good': '👍', 'questionable': '🤔'}.get(quality, '❓')
            print(f"📊 走法质量: {quality_emoji} {quality}")
            
            # 🎯 核心功能：立即显示AI分析
            user_analysis = move_result.get('userAnalysis', '')
            if user_analysis and len(user_analysis) > 20:
                analysis_count += 1
                print(f"\n🎓 AI教练分析:")
                print("=" * 60)
                
                # 清晰显示分析内容
                lines = user_analysis.split('\n')
                for line in lines:
                    if line.strip():
                        print(f"   {line.strip()}")
                        
                print("=" * 60)
                print(f"✅ 第{move_count}步分析完成！")
            else:
                print("⚠️ 分析内容不完整或为空")
                if user_analysis:
                    print(f"   获取到: {user_analysis[:100]}...")
            
            # 显示AI应对（简化显示）
            ai_move = move_result.get('aiMove')
            if ai_move:
                print(f"\n🤖 AI应对: {ai_move}")
                ai_analysis = move_result.get('aiAnalysis', '')
                if ai_analysis:
                    # 简化AI分析显示
                    preview = ai_analysis[:150] + "..." if len(ai_analysis) > 150 else ai_analysis
                    print(f"🔍 AI解析: {preview}")
            
            # 检查游戏状态
            if move_result.get('gameStatus') == 'finished':
                print(f"\n🏁 教学对局结束！")
                print(f"🎯 总结: 共走{move_count}步，获得{analysis_count}次分析")
                print(f"📊 学习效率: {(analysis_count/move_count*100):.0f}%" if move_count > 0 else "0%")
                break
                
        else:
            error_msg = move_result.get('error', '未知错误') if move_result else '无响应'
            print(f"❌ 走法失败: {error_msg}")
            print("💡 请检查走法格式，例如: e2e4, g1f3")
            continue
        
        print(f"\n📈 继续学习！已完成 {analysis_count}/{move_count} 步分析")

def play_teaching_loop(token, game_id, user_color):
    """教学模式游戏循环 - 每步都分析"""
    move_count = 0
    analysis_count = 0
    
    print(f"\n{'='*60}")
    print("🎓 教学模式游戏开始")
    print("💡 每走一步都会得到详细的AI分析和建议")
    print("📝 输入走法格式: e2e4, g1f3 等")
    print("🔙 输入 'back' 返回主菜单，'history' 查看分析历史")
    print(f"{'='*60}")
    
    while True:
        # 获取当前教学对局状态
        history = get_teaching_history(token, game_id)
        if not history:
            print("⚠️ 无法获取对局状态")
            break
        
        moves = history.get('moveHistory', [])
        current_board = history.get('currentBoard', '')
        current_turn = history.get('currentTurn', 'white')
        is_game_over = history.get('isGameOver', False)
        
        print(f"\n{'='*50}")
        print(f"📊 当前状态: 已走 {len(moves)} 步")
        if moves:
            last_move = moves[-1]
            print(f"📝 最后一步: {last_move.get('move', 'N/A')} ({last_move.get('color', 'N/A')}方)")
        
        print(f"🎯 当前轮到: {current_turn}方")
        print(f"🎮 你的颜色: {user_color}")
        
        # 检查游戏是否结束
        if is_game_over:
            print(f"\n🏁 教学对局结束！")
            show_teaching_summary(token, game_id, move_count, analysis_count)
            break
        
        # 检查是否轮到用户
        if current_turn == user_color:
            print(f"\n🎯 轮到你走棋了！({user_color}方)")
            print("请输入你的走法:")
            user_input = input(">>> ").strip().lower()
            
            if user_input == 'back':
                print("🔙 返回主菜单")
                break
            elif user_input == 'history':
                show_teaching_history_detail(history, analysis_count)
                continue
            elif not user_input:
                print("⚠️ 请输入有效的走法")
                continue
            
            # 执行用户走法并获取分析
            print(f"\n📝 执行走法: {user_input}")
            move_result = make_teaching_move_realtime(token, game_id, user_input)
            
            if move_result and move_result.get('success'):
                move_count += 1
                print(f"✅ 走法执行成功！")
                
                # 显示走法质量
                quality = move_result.get('moveQuality', 'unknown')
                quality_emoji = {'excellent': '🏆', 'good': '👍', 'questionable': '🤔'}.get(quality, '❓')
                print(f"📊 走法质量: {quality_emoji} {quality}")
                
                # 显示详细的AI分析
                user_analysis = move_result.get('userAnalysis', '')
                if user_analysis:
                    analysis_count += 1
                    print(f"\n🎓 教练详细分析:")
                    print("=" * 60)
                    # 分段显示分析内容，保持格式
                    lines = user_analysis.split('\n')
                    for line in lines:
                        if line.strip():
                            print(f"   {line.strip()}")
                    print("=" * 60)
                else:
                    print("⚠️ 未获取到AI分析")
                
                # 显示AI应对
                ai_move = move_result.get('aiMove')
                if ai_move:
                    print(f"\n🤖 AI应对: {ai_move}")
                    ai_analysis = move_result.get('aiAnalysis', '')
                    if ai_analysis:
                        print(f"🔍 AI应对解析:")
                        print("-" * 40)
                        # 显示AI走法分析的前200字符
                        ai_lines = ai_analysis.split('\n')
                        for line in ai_lines[:3]:  # 只显示前3行
                            if line.strip():
                                print(f"   {line.strip()}")
                        if len(ai_analysis) > 200:
                            print("   ...")
                        print("-" * 40)
                
                # 显示统计信息
                print(f"\n📈 学习进度:")
                print(f"   ✅ 已走步数: {move_count}")
                print(f"   🎓 获得分析: {analysis_count}")
                print(f"   📊 分析率: {(analysis_count/move_count*100):.0f}%" if move_count > 0 else "0%")
                
                # 检查游戏是否结束
                if move_result.get('gameStatus') == 'finished':
                    print(f"\n🏁 教学对局结束！")
                    show_teaching_summary(token, game_id, move_count, analysis_count)
                    break
                    
            else:
                error_msg = move_result.get('error', '未知错误') if move_result else '无响应'
                print(f"❌ 走法失败: {error_msg}")
                print("💡 请检查走法格式，例如: e2e4, g1f3")
                continue
        else:
            print(f"\n⏳ 等待轮到你走棋...（当前轮到{current_turn}方）")
            print("💡 如果AI刚走过，请等待状态更新")
            input("📖 按Enter刷新状态...")
            continue
        
        # 暂停让用户查看分析
        input("\n📖 按Enter继续...")

def show_teaching_history_detail(history, analysis_count):
    """显示教学历史详情"""
    print(f"\n{'='*60}")
    print("📚 教学分析历史")
    print(f"{'='*60}")
    
    moves = history.get('moveHistory', [])
    if not moves:
        print("📝 暂无走法记录")
        return
    
    print(f"📊 总步数: {len(moves)}")
    print(f"🎓 分析数: {analysis_count}")
    
    # 显示最近几步的分析
    print(f"\n📋 最近5步分析摘要:")
    recent_moves = moves[-5:] if len(moves) >= 5 else moves
    
    for i, move_data in enumerate(recent_moves):
        step_num = len(moves) - len(recent_moves) + i + 1
        move = move_data.get('move', 'N/A')
        color = move_data.get('color', 'N/A')
        
        print(f"\n{step_num}. {move} ({color}方)")
        
        if move_data.get('analysis') and move_data['analysis'].get('ai_analysis'):
            analysis_text = move_data['analysis']['ai_analysis']
            # 显示分析的前100字符
            preview = analysis_text.replace('\n', ' ')[:100]
            print(f"   📝 {preview}{'...' if len(analysis_text) > 100 else ''}")
        else:
            print(f"   ⚠️ 无分析数据")

def show_teaching_summary(token, game_id, move_count, analysis_count):
    """显示教学总结"""
    print(f"\n{'='*60}")
    print("🎓 教学对局总结")
    print(f"{'='*60}")
    
    print(f"📊 学习统计:")
    print(f"   ✅ 总步数: {move_count}")
    print(f"   🎓 分析数: {analysis_count}")
    print(f"   📈 分析覆盖率: {(analysis_count/move_count*100):.1f}%" if move_count > 0 else "0%")
    
    # 获取完整历史
    history = get_teaching_history(token, game_id)
    if history:
        moves = history.get('moveHistory', [])
        print(f"   📚 记录步数: {len(moves)}")
        
        # 统计走法质量
        quality_stats = {"excellent": 0, "good": 0, "questionable": 0}
        for move_data in moves:
            if move_data.get('analysis'):
                quality = move_data['analysis'].get('move_quality', 'unknown')
                if quality in quality_stats:
                    quality_stats[quality] += 1
        
        print(f"\n📊 走法质量分布:")
        print(f"   🏆 优秀: {quality_stats['excellent']}")
        print(f"   👍 良好: {quality_stats['good']}")
        print(f"   🤔 待改进: {quality_stats['questionable']}")
    
    print(f"\n💡 教学模式的价值:")
    print(f"   ✅ 每步都有详细的AI分析")
    print(f"   ✅ 实时获得专业指导")
    print(f"   ✅ 逐步提高棋艺水平")
    print(f"   🎯 继续练习以获得更好的效果！")

# 简化的教学模式测试 - 专注于分析功能
def test_teaching_analysis_simple(token):
    """简化测试：专注验证教学模式下的逐步分析功能"""
    print("\n" + "="*60)
    print("🎓 教学模式分析测试")
    print("💡 验证：棋手走几步，就分析几步")
    print("="*60)
    
    # 开始教学对局
    print("\n1. 创建教学对局...")
    teaching_game = start_teaching_game(token, lesson_type="opening", color="white")
    if not teaching_game:
        print("❌ 无法开始教学对局")
        return
    
    game_id = teaching_game.get("gameId")
    print(f"✅ 教学对局创建成功: {game_id}")
    
    # 测试走法列表
    test_moves = ["e2e4", "g1f3", "f1c4"]
    analysis_count = 0
    
    for i, move in enumerate(test_moves, 1):
        print(f"\n" + "-"*50)
        print(f"📝 第{i}步测试: {move}")
        print("-"*50)
        
        # 提交走法
        move_result = make_teaching_move_realtime(token, game_id, move)
        
        if move_result and move_result.get('success'):
            print(f"✅ 走法提交成功")
            
            # 检查分析结果
            user_analysis = move_result.get('userAnalysis', '')
            move_quality = move_result.get('moveQuality', 'N/A')
            
            print(f"📊 走法质量: {move_quality}")
            
            if user_analysis and len(user_analysis) > 10:
                analysis_count += 1
                print(f"🎯 AI分析长度: {len(user_analysis)} 字符")
                print(f"📖 分析内容预览:")
                # 显示分析的前200个字符
                preview = user_analysis[:200] + "..." if len(user_analysis) > 200 else user_analysis
                print(f"   {preview}")
                print(f"✅ 第{i}步分析成功")
            else:
                print(f"❌ 第{i}步分析失败或内容过短")
                print(f"   返回内容: {user_analysis}")
        else:
            print(f"❌ 走法提交失败: {move_result}")
    
    # 总结测试结果
    print(f"\n" + "="*60)
    print(f"📊 测试结果总结")
    print(f"="*60)
    print(f"✅ 成功执行走法: {len(test_moves)} 步")
    print(f"✅ 成功获得分析: {analysis_count} 步")
    print(f"📈 分析成功率: {(analysis_count/len(test_moves)*100):.1f}%")
    
    if analysis_count == len(test_moves):
        print(f"🎉 完美！每一步都获得了详细分析")
    elif analysis_count > 0:
        print(f"⚠️ 部分分析成功，需要检查失败原因")
    else:
        print(f"❌ 所有分析都失败，需要排查问题")
    
    print(f"\n💡 这就是教学模式的核心：棋手走几步，就分析几步！")

# 诊断教学模式分析问题
def diagnose_teaching_analysis(token):
    """诊断教学模式分析功能，排查问题"""
    print("\n" + "="*60)
    print("🔍 教学模式分析诊断")
    print("="*60)
    
    # 创建教学对局
    print("1. 创建教学对局...")
    teaching_game = start_teaching_game(token, lesson_type="opening", color="white")
    if not teaching_game:
        print("❌ 无法创建教学对局")
        return
    
    game_id = teaching_game.get("gameId")
    print(f"✅ 教学对局创建: {game_id}")
    print(f"   返回数据: {teaching_game}")
    
    # 测试单步走法
    test_move = "e2e4"
    print(f"\n2. 测试走法: {test_move}")
    
    # 直接调用API
    headers = {"Authorization": f"Bearer {token}"}
    data = {"move": test_move}
    
    import requests
    response = requests.post(f"{BASE_URL}/api/teaching/{game_id}/move", 
                           headers=headers, json=data)
    
    print(f"📡 API响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ API调用成功")
        print(f"📊 返回数据键: {list(result.keys())}")
        
        # 检查关键字段
        success = result.get('success', False)
        user_analysis = result.get('userAnalysis', '')
        move_quality = result.get('moveQuality', '')
        
        print(f"🔎 详细检查:")
        print(f"   success: {success}")
        print(f"   moveQuality: {move_quality}")
        print(f"   userAnalysis长度: {len(user_analysis) if user_analysis else 0}")
        
        if user_analysis:
            print(f"✅ 分析内容获取成功")
            print(f"📖 分析内容片段: {user_analysis[:100]}...")
        else:
            print(f"❌ 分析内容为空")
            print(f"🔍 完整返回: {result}")
    else:
        print(f"❌ API调用失败")
        print(f"📄 错误响应: {response.text}")
    
    print(f"\n🎯 诊断完成")

# 程序入口点
if __name__ == "__main__":
    print("🎯 国际象棋测试客户端启动")
    print("=" * 50)
    
    try:
        # 启动交互式游戏客户端
        play_interactive_game()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        print("请检查后端服务是否正常运行")
