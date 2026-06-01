# 🧠 Local AI Orchestrator — 最简单使用方式

不熟悉命令行也没关系。下载后双击几个文件就能用。

---

## macOS

**第一次使用：**

1. 双击 `修复macOS脚本权限.command`
2. 双击 `1_安装环境.command`
3. 双击 `3_运行体检.command`
4. 双击 `2_启动项目.command`
5. 浏览器会自动打开 `http://localhost:8422`

**或者用图形启动器：**

双击 `打开启动器.command`，然后在窗口里点按钮。

**测试 ChatGPT：**

1. 双击 `4_登录ChatGPT.command`
2. 在弹出的浏览器里登录 ChatGPT
3. 回到命令窗口确认完成
4. 双击 `5_测试ChatGPT.command`

---

## Windows

**第一次使用：**

1. 双击 `1_安装环境.bat`
2. 双击 `3_运行体检.bat`
3. 双击 `2_启动项目.bat`
4. 浏览器会自动打开 `http://localhost:8422`

**或者用图形启动器：**

双击 `打开启动器.bat`，然后在窗口里点按钮。

**测试 ChatGPT：**

1. 双击 `4_登录ChatGPT.bat`
2. 在弹出的浏览器里登录 ChatGPT
3. 回到命令窗口确认完成
4. 双击 `5_测试ChatGPT.bat`

---

## 前提条件

- 已安装 LM Studio 或 Ollama，并加载了模型
- 如果要用 Web AI 功能，需要已安装 Chrome/Edge 浏览器

---

## 常见问题

| 问题                          | 解决                                                |
| ----------------------------- | --------------------------------------------------- |
| macOS 提示"无法打开 .command" | 双击 `修复macOS脚本权限.command`，或右键文件 → 打开 |
| doctor 提示 LM Studio 没启动  | 打开 LM Studio → Developer → Start Server           |
| doctor 提示 Ollama 没启动     | 运行 `ollama serve`，然后 `ollama pull llama3`      |
| Playwright 报错               | 重新双击 `1_安装环境`                               |
| 8422 端口被占用               | 关闭已有终端或重启电脑                              |
| 按钮点不了 / 窗口没反应       | 等上一次任务跑完，或在终端手动执行对应脚本          |
