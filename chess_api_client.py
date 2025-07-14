import requests
import openai
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# OpenAI API配置
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')

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

# 获取最近游戏
def get_recent_games(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/games/recent", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取最近游戏失败: {response.status_code} - {response.text}")
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

# 删除用户
def delete_user(token, username):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BASE_URL}/api/user/{username}", headers=headers)
    if response.status_code == 200:
        print(f"用户 {username} 删除成功。")
        return response.json()
    else:
        print(f"删除用户失败: {response.status_code} - {response.text}")
        return None

# 结束所有未完成的对局
def finish_all_unfinished_games(token, username):
    games_info = get_recent_games(token)
    if not games_info or "games" not in games_info:
        print("未获取到棋局列表")
        return
    for game in games_info["games"]:
        # 只处理自己参与且未结束的对局
        if (game["player1_username"] == username or game["player2_username"] == username) and not game["result"]:
            game_id = game["game_id"]
            print(f"结束未完成对局: {game_id}")
            resign_result = resign_game(token, game_id)
            print(f"认输结果: {resign_result}")

if __name__ == "__main__":
    # 用户手动输入用户名和密码
    username = input("请输入用户名: ").strip()
    password = input("请输入密码: ").strip()
    token = get_token(username, password)
    print("Token:", token)

    # 登录失败且用户名不存在时询问是否注册
    if not token:
        print("登录失败，是否注册新用户？(y/n): ", end="")
        choice = input().strip().lower()
        if choice == 'y':
            reg_token = register_user(username, password)
            if reg_token:
                print("注册并登录成功，Token:", reg_token)
                token = reg_token
            else:
                print("无法注册新用户，程序退出。")
                exit(1)
        else:
            print("未注册新用户，程序退出。")
            exit(1)

    if token:
        # 先结束所有未完成对局
        finish_all_unfinished_games(token, username)
        
        # 获取最近游戏
        print("最近游戏:", get_recent_games(token))
        
        # 创建新对弈
        new_game = create_match(token, color="white", difficulty="easy")
        print("新创建的对弈:", new_game)
        
        if new_game:
            game_id = new_game.get("gameId")
            # 获取游戏详情
            print("游戏详情:", get_game_details(game_id, token))
            
            # 测试走棋（如 e2e4）
            move_result = make_move(token, game_id, "e2e4")
            print("走棋结果:", move_result)
            
            # 再次获取游戏详情
            print("走棋后游戏详情:", get_game_details(game_id, token))
            
            # 测试认输
            resign_result = resign_game(token, game_id)
            print("认输结果:", resign_result)
            
            # 再次获取游戏详情
            print("认输后游戏详情:", get_game_details(game_id, token))
        
        # 询问是否删除用户，并二次确认
        print("是否删除当前用户？(y/n): ", end="")
        del_choice1 = input().strip().lower()
        if del_choice1 == 'y':
            print("请再次确认是否删除当前用户？(y/n): ", end="")
            del_choice2 = input().strip().lower()
            if del_choice2 == 'y':
                print("尝试删除当前用户...")
                delete_user(token, username)
            else:
                print("已取消删除用户。")
        else:
            print("未删除用户。")
        
    else:
        print("无法继续操作，未获取到有效令牌。")