from dao import init_db, add_sample_data

if __name__ == "__main__":
    # 初始化数据库（drop_existing=True 表示先清空旧表，推荐开发测试时使用）
    init_db(drop_existing=True)

    # 添加示例数据
    add_sample_data()

    print("✅ MySQL 数据库初始化并填充数据成功！")
