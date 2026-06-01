# Portable Mode

项目设计为便携模式 — 所有下载内容在项目目录内，删除项目文件夹即可清理。

## Playwright 浏览器路径

本项目使用项目内 Playwright 目录，不使用系统共享缓存：

```
导出：PLAYWRIGHT_BROWSERS_PATH = .playwright-browsers/
```

Chromium 下载到项目根目录下的 `.playwright-browsers/`，不在系统 `~/Library/Caches/` 或 `%LOCALAPPDATA%` 中。

删除 `local-ai-orchestrator/` 文件夹即可删除本项目自己的 Playwright 浏览器、Web AI profile、runtime、测试报告和日志。

## 下载内容

| 路径                    | 说明                                                          | 删除方式                 |
| ----------------------- | ------------------------------------------------------------- | ------------------------ |
| `venv/`                 | Python 虚拟环境                                               | `rm -rf venv`            |
| `.playwright-browsers/` | Playwright Chromium                                           | 删除文件夹或运行清理脚本 |
| `runtime/`              | 运行数据（evidence / logs / test reports / browser profiles） | 删除文件夹或运行清理脚本 |
| `.env`                  | 本地配置                                                      | `rm .env`                |

## 不会下载 / 保留在系统

| 工具            | 位置                      |
| --------------- | ------------------------- |
| Python          | 系统安装路径              |
| Git             | 系统安装路径              |
| LM Studio       | ~/Applications 或系统路径 |
| Ollama          | 系统路径                  |
| Node.js         | 系统安装路径              |
| Codex CLI       | 系统路径                  |
| Claude Code CLI | 系统路径                  |

清理脚本禁止删除这些系统目录。

## 清理

双击 `清理项目缓存.command` 或 `清理项目缓存.bat`

默认删除：

- .playwright-browsers/
- runtime/
- .pytest_cache/
- **pycache**/

不删除：

- venv（Python 虚拟环境）
- .env（配置文件）
- src/ backend/ frontend/（源码）

深度清理：脚本会单独询问是否删除 venv 和 .env。

清理脚本禁止删除：

- ~/Library/Caches/ms-playwright/
- %LOCALAPPDATA%\ms-playwright\
- 任何项目目录外的路径

## 手动完全重置

```bash
rm -rf .playwright-browsers/ runtime/ .pytest_cache/
find . -type d -name __pycache__ -prune -exec rm -rf {} +
# 重新 double-click 1_安装环境
```
