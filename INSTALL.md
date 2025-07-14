# 🔧 环境配置安装指南

## 📋 安装步骤

### 1. 安装依赖包
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的配置
```

### 3. 环境变量说明

在 `.env` 文件中配置以下变量：

```bash
# OpenAI API 配置 (必需)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1

# Flask 安全密钥 (推荐修改)
SECRET_KEY=your-secret-key-change-in-production

# Stockfish 引擎路径 (根据实际安装路径修改)
STOCKFISH_PATH=D:\stockfish\stockfish-windows-x86-64-avx2.exe
```

### 4. 启动服务

```bash
# 方式1: 直接启动
python app.py

# 方式2: 使用启动脚本
python run_server.py
```

### 5. 验证配置

```bash
# 运行安全性检查
python check_core_security.py

# 测试基本功能
python -c "from app import app; print('✅ 配置成功！')"
```

## ⚠️ 安全提醒

1. **绝对不要**将包含真实API密钥的 `.env` 文件提交到版本控制系统
2. `.env` 文件已自动加入 `.gitignore`，确保不会被意外提交
3. 在生产环境中，请使用强密码作为 `SECRET_KEY`
4. 定期检查代码中是否有硬编码的敏感信息

## 🔍 检查工具

- `check_security.py` - 全面的安全性检查
- `check_core_security.py` - 核心文件API密钥检查

## 🚀 快速测试

```bash
# 测试API服务器
curl http://localhost:8000/

# 测试用户注册
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```
