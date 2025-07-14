#!/usr/bin/env python3
"""
国际象棋 API 服务器启动脚本
"""
import os
import sys
from app import app, db
from dao import init_db, add_sample_data

def setup_environment():
    """设置环境变量"""
    # 设置默认环境变量
    if not os.getenv('SECRET_KEY'):
        os.environ['SECRET_KEY'] = 'your-secret-key-change-in-production'
    
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  警告: 未设置 OPENAI_API_KEY 环境变量，AI功能将不可用")
    
    if not os.getenv('OPENAI_MODEL'):
        os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'

def initialize_database():
    """初始化数据库"""
    try:
        print("🔄 正在初始化数据库...")
        init_db(drop_existing=False)  # 不删除现有数据
        print("✅ 数据库初始化完成")
        
        # 检查是否需要添加示例数据
        if not db.get_user_by_username('admin'):
            print("🔄 正在添加示例数据...")
            add_sample_data()
            print("✅ 示例数据添加完成")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    print("🏁 启动国际象棋 API 服务器...")
    
    # 设置环境
    setup_environment()
    
    # 初始化数据库
    initialize_database()
    
    # 启动服务器
    print("🚀 服务器启动中...")
    print("📍 API地址: http://localhost:5000")
    print("📖 API文档: 查看 API.md")
    print("🛑 按 Ctrl+C 停止服务器")
    
    try:
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            use_reloader=False  # 避免重复初始化
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
