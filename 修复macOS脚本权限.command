#!/bin/bash
cd "$(dirname "$0")"
chmod +x *.command
chmod +x scripts/*.sh
echo "✅ 权限已修复。现在可以双击 1_安装环境.command"
read -n 1 -s -r -p "按任意键退出..."
