#!/usr/bin/env python3
"""
安全性检查脚本 - 检测代码中是否存在硬编码的敏感信息
"""
import os
import re

def check_security():
    """检查代码安全性"""
    print("🔍 开始安全性检查...")
    
    # 需要检查的文件模式
    patterns_to_check = [
        r'\.py$',
        r'\.txt$',
        r'\.md$'
    ]
    
    # 敏感信息模式
    sensitive_patterns = [
        (r'sk-[a-zA-Z0-9]{20,}', 'OpenAI API Key'),
        (r'api_key\s*=\s*["\'][^"\']+["\']', 'API Key'),
        (r'password\s*=\s*["\'][^"\']+["\']', 'Password'),
        (r'secret\s*=\s*["\'][^"\']+["\']', 'Secret'),
        (r'token\s*=\s*["\'][^"\']+["\']', 'Token')
    ]
    
    issues_found = []
    files_checked = 0
    
    # 遍历当前目录
    for root, dirs, files in os.walk('.'):
        # 跳过特定目录
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.env']]
        
        for file in files:
            # 检查文件是否匹配模式
            if any(re.search(pattern, file) for pattern in patterns_to_check):
                file_path = os.path.join(root, file)
                
                # 跳过 .env 文件（这是预期存放敏感信息的地方）
                if file.endswith('.env'):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        files_checked += 1
                        
                        for pattern, description in sensitive_patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                issues_found.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'type': description,
                                    'content': match.group()[:50] + '...' if len(match.group()) > 50 else match.group()
                                })
                except Exception as e:
                    print(f"  ⚠️  无法读取文件 {file_path}: {e}")
    
    print(f"✅ 已检查 {files_checked} 个文件")
    
    if issues_found:
        print(f"\n⚠️  发现 {len(issues_found)} 个潜在安全问题:")
        for issue in issues_found:
            print(f"  📁 {issue['file']}:{issue['line']}")
            print(f"     类型: {issue['type']}")
            print(f"     内容: {issue['content']}")
            print()
        print("🔧 建议：将敏感信息移至 .env 文件并使用环境变量")
    else:
        print("✅ 未发现硬编码的敏感信息")
    
    return len(issues_found) == 0

if __name__ == "__main__":
    is_secure = check_security()
    exit(0 if is_secure else 1)
