"""Stable product-facing error codes and Chinese guidance."""

from __future__ import annotations


PRODUCT_ERRORS = {
    "LOCAL_MODEL_UNAVAILABLE": {
        "message": "本地模型未连接，已尝试使用规则规划。",
        "next_action": "启动 LM Studio Developer Server，或继续使用基础规则任务。",
    },
    "EXTERNAL_AI_NEED_LOGIN": {
        "message": "外部 AI 需要登录或人工处理。",
        "next_action": "打开 Claude 工作区完成登录或验证，然后点击“我已处理，继续”。",
    },
    "PLAYWRIGHT_BROWSER_MISSING": {
        "message": "项目专用浏览器未安装，网页 AI 暂不可用。",
        "next_action": "查看项目专用浏览器安装说明；基础本地任务仍可继续。",
    },
    "PROJECT_PATH_MISSING": {
        "message": "项目路径不存在或不可访问。",
        "next_action": "重新选择一个有效的项目目录。",
    },
    "SHELL_COMMAND_FAILED": {
        "message": "命令执行失败。",
        "next_action": "查看执行日志和失败输出，再决定是否修复或重试。",
    },
    "REPAIR_NOT_SUPPORTED": {
        "message": "当前错误类型暂不支持自动修复。",
        "next_action": "查看失败原因，手动处理或在 Claude 可用时请求外部建议。",
    },
    "TASK_PAUSED": {
        "message": "任务已暂停，等待用户处理。",
        "next_action": "完成页面登录、验证或其他提示后继续任务。",
    },
    "TASK_SUCCESS": {
        "message": "任务已完成。",
        "next_action": "查看最终报告和证据记录。",
    },
}


def product_error(code: str, *, detail: str = "") -> dict:
    item = PRODUCT_ERRORS.get(
        code,
        {"message": detail or code, "next_action": "查看日志获取更多信息。"},
    )
    return {
        "code": code,
        "message": item["message"],
        "next_action": item["next_action"],
        "detail": detail,
    }

