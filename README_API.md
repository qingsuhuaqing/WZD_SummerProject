# 国际象棋 API 控制层

这是一个基于Flask的国际象棋应用后端API，提供对弈和教学功能。

## 项目结构

```
xxq_backend/
├── models.py           # 数据模型定义
├── dao.py             # 数据访问对象
├── analysis_service.py # AI分析服务
├── teaching_service.py # 教学服务
├── competition_service.py # 竞技服务
├── app.py             # Flask应用主文件（新增）
├── run_server.py      # 服务器启动脚本（新增）
├── test_api.py        # API测试脚本（新增）
├── requirements.txt   # 依赖列表
├── API.md            # API文档
└── README.md         # 本文件
```

## 功能特性

### 🎯 核心功能
- **对弈模式**: 与AI进行国际象棋对弈
- **教学模式**: 交互式教学课程
- **复盘功能**: 历史对局回放和分析
- **用户管理**: 注册、登录、个人信息管理

### 🔧 技术特性
- **RESTful API**: 符合REST规范的API设计
- **JWT认证**: 安全的用户认证机制
- **国际象棋引擎**: 使用python-chess库处理棋局逻辑
- **AI集成**: 集成OpenAI API进行棋局分析和指导
- **数据库支持**: 完整的棋局数据存储和管理

## 安装和运行

### 1. 环境要求
- Python 3.8+
- MySQL 5.7+
- OpenAI API密钥（可选，用于AI功能）

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 环境变量设置
```bash
# 必需的环境变量
export SECRET_KEY="your-secret-key-here"

# 可选的环境变量
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_MODEL="gpt-3.5-turbo"
```

### 4. 数据库配置
确保MySQL服务运行，并根据`dao.py`中的配置修改数据库连接信息：
```python
DATABASE_URI = "mysql+pymysql://root:password@localhost:3306/chess_db"
```

### 5. 启动服务器
```bash
python run_server.py
```

或者直接运行Flask应用：
```bash
python app.py
```

服务器将在 `http://localhost:5000` 启动。

## API 使用

### 认证
大多数API需要JWT认证。首先注册或登录获取token：

```bash
# 注册
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# 登录
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

### 使用Token
在请求头中包含token：
```bash
curl -X GET http://localhost:5000/api/user/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 主要API端点

#### 用户相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `GET /api/user/profile` - 获取用户信息
- `GET /api/user/avatar` - 获取用户头像
- `GET /api/user/history` - 获取历史对局

#### 对弈模式
- `POST /api/game/match` - 创建新对局
- `GET /api/game/{gameId}` - 获取对局状态
- `POST /api/game/{gameId}/move` - 提交走法
- `POST /api/game/{gameId}/resign` - 认输

#### 教学模式
- `GET /api/teaching/lessons` - 获取教学课程
- `GET /api/teaching/{lessonId}` - 获取课程详情
- `POST /api/teaching/{lessonId}/move` - 教学模式走法

#### 复盘功能
- `GET /api/replay/{gameId}` - 获取复盘数据

## 测试

运行测试脚本：
```bash
python test_api.py
```

## 开发说明

### 代码结构
- `app.py`: Flask应用主文件，包含所有API端点
- `run_server.py`: 服务器启动脚本，处理初始化逻辑
- `test_api.py`: API测试脚本

### 新增功能
1. **JWT认证系统**: 完整的用户认证和授权
2. **游戏状态管理**: 内存中的活跃游戏状态管理
3. **教学课程系统**: 预定义的教学课程和交互式指导
4. **错误处理**: 统一的错误处理和响应格式
5. **API文档兼容**: 完全按照API.md文档实现

### 扩展点
- **AI引擎**: 可以集成更强的国际象棋引擎（如Stockfish）
- **实时通信**: 可以添加WebSocket支持实时对弈
- **更多教学内容**: 扩展教学课程和练习
- **用户系统**: 添加更多用户功能（头像上传、好友系统等）

## 故障排除

### 常见问题
1. **导入错误**: 确保所有依赖都已正确安装
2. **数据库连接**: 检查MySQL服务和连接配置
3. **Chess库**: 如果python-chess安装失败，某些功能会被禁用
4. **OpenAI API**: 没有API密钥时，AI功能将不可用

### 调试模式
服务器以debug模式运行，会显示详细的错误信息。

## 许可证

本项目遵循MIT许可证。

## 贡献

欢迎提交问题和改进建议！
