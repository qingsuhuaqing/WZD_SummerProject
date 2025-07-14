# Frontend of DeepChess

### Pages

1. Start page (similar with GITHUB)
2. Home page *
    1. 教学 对弈
    2. 个人中心
3. 个人中心
    1. 个人信息
    2. 历史对局 -》 复盘
    3. 胜率
    4. ai锐评

4. 对弈 -> 执黑 or 执白 -> game page1 -> 结算 -> Home page
5. 教学 -> 选择教学内容 -> game page2 -> 结算 -> Home page
6. 复盘 -> 选择对局 -> game page2 -> 结算 -> Home page
7. game page2
    1. 棋盘
    2. 对局信息
    3. ai comment
8. game page1
    1. 棋盘
    2. 对局信息
9. 结算
    1. 对局信息
    2. ai锐评
    3. 复盘按钮

## API Documentation

### Base URL
```
https://api.deepchess.com/v1
```

### Authentication
Most endpoints require authentication via JWT token in Authorization header:
```
Authorization: Bearer <token>
```

### Common Data Types

#### Move Format
走法使用标准代数记号法(Standard Algebraic Notation)：
- 格式：`{from}{to}` (例如: `e2e4`, `g1f3`)
- from/to: 位置坐标，a-h列，1-8行
- 特殊走法：
  - 王车易位：`e1g1`(白王短易位), `e1c1`(白王长易位)
  - 兵升变：`e7e8q`(升后), `e7e8r`(升车), `e7e8b`(升象), `e7e8n`(升马)
  - 吃过路兵：`e5d6`(正常格式，系统自动识别)

#### Board State Format
棋盘状态使用FEN(Forsyth-Edwards Notation)表示：
- 格式：`{pieces}/{pieces}/.../{pieces} {activeColor} {castling} {enPassant} {halfmove} {fullmove}`
- 示例：`rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`
- pieces: 棋子位置，大写白子，小写黑子
- activeColor: 当前玩家 (w/b)
- castling: 易位权利 (K/Q/k/q)
- enPassant: 过路兵目标格 (-)
- halfmove: 半回合计数
- fullmove: 全回合计数

#### Game Result
- `ongoing`: 对局进行中
- `win`: 用户获胜
- `loss`: 用户失败
- `draw`: 平局
- `lesson_complete`: 教学完成

### Common Error Responses
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {}
  }
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `204`: No Content
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `409`: Conflict
- `422`: Validation Error
- `500`: Internal Server Error

### 1. Start Page
- **GET** `/api/start`  
  描述：检查登录状态并跳转到相应页面  
  认证：否  
  响应：  
    - `302 Redirect` → `/login` (未登录) 或 `/home` (已登录)
    - `500`: 服务器错误

### 2. 身份验证
- **POST** `/api/auth/login`  
  认证：否  
  描述：用户登录，返回JWT token  
  请求体：
  ```json
  {
    "username": "string",  // 用户名，3-20字符，支持字母数字下划线
    "password": "string"   // 密码，6-128字符
  }
  ```
  响应：
  - `200`:
    ```json
    {
      "token": "jwt_token_string",  // JWT token，24小时有效
      "user": {
        "id": "string",         // 用户唯一标识符
        "username": "string"    // 用户名
      }
    }
    ```
  - `401`: 用户名或密码错误
  - `422`: 请求参数验证失败
  
  Set-Cookie: `token=xxx; HttpOnly; Secure; SameSite=Strict; Max-Age=86400`

- **POST** `/api/auth/logout`  
  认证：是  
  描述：用户登出，清除token  
  响应：
  - `204`: 成功登出
  - `401`: 未认证

### 3. Home Page
- **GET** `/api/user/avatar`  
  认证：是  
  描述：获取用户头像图片（Base64编码）  
  响应：
  - `200`:
    ```json
    {
      "avatar": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."  // Base64编码的图片数据
    }
    ```
  - `401`: 未认证
  - `404`: 头像不存在（返回默认头像）

### 4. 个人中心
- **GET** `/api/user/profile`  
  认证：是  
  描述：获取用户个人信息和统计数据  
  响应：
  - `200`:
    ```json
    {
      "id": "string",           // 用户唯一标识符
      "username": "string",     // 用户名
      "email": "string",        // 邮箱地址
      "createdAt": "2023-10-01T12:00:00Z",  // 账户创建时间(ISO 8601)
      "stats": {
        "totalGames": 100,      // 总对局数
        "wins": 60,             // 获胜局数
        "losses": 35,           // 失败局数
        "draws": 5,             // 平局数
        "winRate": 0.60         // 胜率 (0.0-1.0)
      }
    }
    ```
  - `401`: 未认证

- **GET** `/api/user/history`  
  认证：是  
  描述：获取用户历史对局列表，支持分页和排序  
  查询参数：
  - `page`: 页码（默认1，最小1）
  - `limit`: 每页数量（默认20，范围1-100）
  - `sort`: 排序方式
    - `date_desc`: 按日期降序（默认）
    - `date_asc`: 按日期升序
    - `result_win`: 只显示获胜对局
    - `result_loss`: 只显示失败对局
    - `result_draw`: 只显示平局
  
  响应：
  - `200`:
    ```json
    {
      "games": [
        {
          "gameId": "string",           // 对局唯一标识符
          "opponent": "string",         // 对手名称（AI或其他玩家）
          "result": "win|loss|draw",    // 对局结果
          "date": "2023-10-01T12:00:00Z",  // 对局开始时间(ISO 8601)
          "duration": 1800,             // 对局持续时间(秒)
          "userColor": "white|black",   // 用户执棋颜色
          "moveCount": 42,              // 总走法数
          "gameType": "match|lesson"    // 对局类型：对弈或教学
        }
      ],
      "pagination": {
        "page": 1,          // 当前页码
        "limit": 20,        // 每页数量
        "total": 100,       // 总记录数
        "totalPages": 5,    // 总页数
        "hasNext": true,    // 是否有下一页
        "hasPrev": false    // 是否有上一页
      }
    }
    ```
  - `401`: 未认证
  - `422`: 查询参数验证失败

- **GET** `/api/user/history/{gameId}`  
  认证：是  
  描述：获取单局详细复盘数据  
  路径参数：
  - `gameId`: 对局ID（必须是用户参与的对局）
  
  响应：
  - `200`:
    ```json
    {
      "gameId": "string",                              // 对局唯一标识符
      "moves": ["e2e4", "e7e5", "g1f3"],             // 走法序列
      "boardStates": [                                 // 对应每步后的棋盘状态
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
      ],
      "timestamps": [                                  // 每步的时间戳
        "2023-10-01T12:00:00Z",
        "2023-10-01T12:01:00Z"
      ],
      "comments": [                                    // 走法评论
        {
          "moveIndex": 0,                              // 走法索引（从0开始）
          "userComment": "开局控制中心",                // 用户评论
          "aiComment": "经典的王兵开局"                 // AI评论
        }
      ]
    }
    ```
  - `401`: 未认证
  - `404`: 对局不存在或无权访问

### 5. 对弈（game page1）
- **POST** `/api/game/match`  
  认证：是  
  描述：创建新的对弈游戏，与AI对局  
  请求体：
  ```json
  {
    "color": "white|black",           // 用户执棋颜色
    "difficulty": "easy|medium|hard"  // AI难度等级
  }
  ```
  参数说明：
  - `color`: 必填，用户选择的棋子颜色
  - `difficulty`: 必填，AI难度
    - `easy`: 简单（约1200 ELO）
    - `medium`: 中等（约1600 ELO）
    - `hard`: 困难（约2000 ELO）
  
  响应：
  - `201`:
    ```json
    {
      "gameId": "string",                    // 新创建的对局ID
      "userColor": "white|black",            // 用户执棋颜色
      "currentPlayer": "white|black",        // 当前轮到的玩家
      "difficulty": "easy|medium|hard",      // AI难度
      "initialBoard": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    }
    ```
  - `401`: 未认证
  - `422`: 请求参数验证失败

- **GET** `/api/game/{gameId}`  
  认证：是  
  描述：获取对局当前状态  
  路径参数：
  - `gameId`: 对局ID
  
  响应：
  - `200`:
    ```json
    {
      "gameId": "string",                         // 对局ID
      "boardState": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
      "moves": ["e2e4", "e7e5"],                 // 已进行的走法
      "currentPlayer": "white|black",             // 当前轮到的玩家
      "userColor": "white|black",                 // 用户执棋颜色
      "status": "ongoing|finished",               // 对局状态
      "result": "ongoing|win|loss|draw",          // 对局结果
      "moveCount": 2,                             // 当前走法数
      "startTime": "2023-10-01T12:00:00Z",       // 对局开始时间
      "lastMoveTime": "2023-10-01T12:01:00Z"     // 最后一步时间
    }
    ```
  - `401`: 未认证
  - `404`: 对局不存在或无权访问

  说明:
  - 对于对弈模式，默认情况下boardState为初始状态
  - 对于对弈模式，默认情况下moves为空数组，表示没有走法，这里这样设计是为了后续/api/teaching/{lessonId}可以复用

- **POST** `/api/game/{gameId}/move`  
  认证：是  
  描述：提交用户走法，返回AI应对  
  路径参数：
  - `gameId`: 对局ID
  
  请求体：
  ```json
  {
    "move": "e2e4"  // 走法，使用标准代数记号法
  }
  ```
  参数说明：
  - `move`: 必填，格式为{from}{to}，如"e2e4"
  - 前端需要验证走法的合法性
  
  响应：
  - `200`:
    ```json
    {
      "userMove": "e2e4",                         // 用户走法
      "aiMove": "e7e5",                           // AI应对走法
      "result": "ongoing|win|loss|draw",          // 对局结果
      "boardState": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
      "moveCount": 2,                             // 当前总走法数
      "isCheck": false,                           // 是否将军
      "isCheckmate": false,                       // 是否将死
      "capturedPiece": null,                      // 被吃的棋子（如果有）
      "evaluation": {                             // AI评估（可选）
        "score": 0.25,                            // 局面评分
        "depth": 12                               // 搜索深度
      }
    }
    ```
  - `400`: 非法走法
  - `401`: 未认证
  - `404`: 对局不存在
  - `409`: 不是用户回合或对局已结束

- **POST** `/api/game/{gameId}/resign`  
  认证：是  
  描述：用户认输，结束对局  
  路径参数：
  - `gameId`: 对局ID
  
  响应：
  - `200`:
    ```json
    {
      "result": "loss",                           // 对局结果
      "reason": "resignation",                    // 结束原因
      "finalBoard": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
      "moveCount": 5,                             // 总走法数
      "duration": 300                             // 对局持续时间(秒)
    }
    ```
  - `401`: 未认证
  - `404`: 对局不存在
  - `409`: 对局已结束

### 6. 教学（game page2）
- **GET** `/api/teaching/lessons`  
  认证：是  
  描述：获取所有可用的教学课程列表  
  响应：
  - `200`:
    ```json
    {
      "lessons": [
        {
          "lessonId": "string",                     // 课程唯一标识符
          "title": "string",                        // 课程标题
          "description": "string",                  // 课程描述
          "difficulty": "beginner|intermediate|advanced",  // 难度等级
          "category": "opening|middlegame|endgame", // 课程类型
          "estimatedTime": 15,                      // 预计完成时间(分钟)
          "completionRate": 0.85,                   // 完成率
          "isCompleted": false,                     // 用户是否已完成
          "prerequisites": ["lesson_id_1"]          // 前置课程
        }
      ],
      "categories": [                               // 课程分类统计
        {
          "category": "opening",
          "count": 10,
          "completedCount": 5
        }
      ]
    }
    ```
  - `401`: 未认证

- **GET** `/api/teaching/{lessonId}`  
  认证：是  
  描述：获取特定教学课程的详细信息和初始状态  
  路径参数：
  - `lessonId`: 课程ID
  
  响应：
  - `200`:
    ```json
    {
      "lessonId": "string",                       // 课程ID
      "title": "string",                          // 课程标题
      "description": "string",                    // 详细描述
      "boardState": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
      "moves": ["e2e4", "e7e5"],                 // 预设走法
      "currentPlayer": "white|black",             // 当前轮到的玩家
      "userColor": "white|black",                 // 用户执棋颜色
      "instructions": "string",                   // 教学指导
      "objectives": [                             // 学习目标
        "掌握王兵开局的基本原理",
        "理解中心控制的重要性"
      ],
      "hints": [                                  // 提示信息
        "控制中心是开局的关键",
        "快速发展轻子"
      ]
    }
    ```
  - `401`: 未认证
  - `404`: 教学内容不存在

- **POST** `/api/teaching/{lessonId}/move`  
  认证：是  
  描述：在教学模式下提交走法，获得详细的AI指导  
  路径参数：
  - `lessonId`: 课程ID
  
  请求体：
  ```json
  {
    "move": "e2e4"  // 走法
  }
  ```
  响应：
  - `200`:
    ```json
    {
      "userMove": "e2e4",                         // 用户走法
      "aiMove": "e7e5",                           // AI应对走法
      "result": "ongoing|win|loss|draw|lesson_complete",  // 状态
      "boardState": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
      "userComment": "很好的开局！这步棋控制了中心。",   // 对用户走法的评价
      "aiComment": "经典的应对，保持对称。",           // 对AI走法的说明
      "moveRating": "excellent|good|okay|poor",     // 走法评级
      "alternativeMoves": [                        // 其他可选走法
        {
          "move": "d2d4",
          "comment": "同样控制中心的选择"
        }
      ],
      "nextInstruction": "现在尝试发展马匹",           // 下一步指导
      "progress": {                                // 学习进度
        "currentStep": 3,
        "totalSteps": 10,
        "completion": 0.3
      }
    }
    ```
  - `400`: 非法走法
  - `401`: 未认证
  - `404`: 教学内容不存在

### 7. 复盘
- **GET** `/api/replay/{gameId}`  
  认证：是  
  描述：获取单局完整复盘数据，包含所有走法和棋盘状态  
  路径参数：
  - `gameId`: 对局ID
  
  响应：
  - `200`:
    ```json
    {
      "gameId": "string",                         // 对局ID
      "moves": ["e2e4", "e7e5"],                 // 完整走法序列
      "boardStates": [                            // 每步后的棋盘状态
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
      ],
      "timestamps": [                             // 每步的时间戳
        "2023-10-01T12:00:00Z",
        "2023-10-01T12:01:00Z"
      ],
      "gameInfo": {
        "opponent": "AI_Medium",                  // 对手信息
        "result": "win|loss|draw",                // 对局结果
        "userColor": "white|black",               // 用户执棋颜色
        "duration": 1800,                         // 总时长(秒)
        "startTime": "2023-10-01T12:00:00Z",     // 开始时间
        "endTime": "2023-10-01T12:30:00Z",       // 结束时间
        "totalMoves": 42,                         // 总走法数
        "gameType": "match|lesson",