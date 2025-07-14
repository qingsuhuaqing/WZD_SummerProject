import re
import os

# 检查项目核心文件
core_files = ['app.py', 'analysis_service.py', 'competition_service.py', 'teaching_service.py', 'chess_api_client.py', 'simple_chess_teaching.py']
sensitive_pattern = r'sk-[a-zA-Z0-9]{20,}'

print("🔍 检查核心文件的API密钥安全性...")
all_secure = True

for file in core_files:
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = re.findall(sensitive_pattern, content)
            if matches:
                print(f'⚠️  {file}: 发现硬编码API密钥')
                all_secure = False
            else:
                print(f'✅ {file}: 安全')
    else:
        print(f'❓ {file}: 文件不存在')

if all_secure:
    print("\n🎉 所有核心文件都已安全配置！")
else:
    print("\n⚠️  仍有文件需要修复")
