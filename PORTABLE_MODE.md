# Portable Mode

项目设计为便携模式 — 所有下载内容在项目目录内，删除项目文件夹即可清理。

## 项目下载了什么

| 路径 | 说明 |
|---|---|
| `venv/` | Python 虚拟环境 |
| `.playwright-browsers/` | Playwright Chromium 浏览器 |
| `runtime/` | 运行数据（证据、日志、测试报告、浏览器 profile） |
| `.env` | 配置文件 |

## 不会下载 / 不会删除

| 工具 | 说明 |
|---|---|
| Python | 系统工具，需单独安装 |
| Git | 系统工具，需单独安装 |
| LM Studio | 系统工具，需单独安装 |
| Ollama | 系统工具，需单独安装 |
| Node.js | 系统工具，需单独安装 |

删除项目文件夹只会删除项目自身文件，不会影响系统。

## 安装流程

1. 双击 `1_安装环境.command` — 先运行 doctor 检查，显示缺失项
2. 用户确认后，仅补装项目内缺失的依赖
3. 不自动安装 Python / Git / LM Studio / Ollama

## 安装了什么

```
python3 scripts/doctor.py          # 检查当前状态
python3 scripts/install_missing.py # 只安装项目依赖
```

install_missing.py 只处理：
- venv
- pip requirements
- Playwright Chromium（下载到 .playwright-browsers/）
- .env
- runtime 目录

## 清理

双击 `清理项目缓存.command` 或 `清理项目缓存.bat`

默认删除：
- runtime/
- .playwright-browsers/
- .pytest_cache/
- __pycache__/

不删除：
- venv
- .env
- 源码

深度清理：脚本会询问是否删除 venv 和 .env。

## Playwright 旧路径清理

如果之前用默认路径安装过 Playwright Chromium：

macOS：
```bash
rm -rf ~/Library/Caches/ms-playwright/
```

Windows：
```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\ms-playwright"
```

## 手动完全重置

```bash
# macOS / Linux
rm -rf venv .env runtime .playwright-browsers .pytest_cache
find . -type d -name __pycache__ -prune -exec rm -rf {} +
# 然后重新 双击 1_安装环境.command
```
