PREFLIGHT_QUESTIONS=[
 '项目路径在哪里？','是否允许读取、创建、修改和覆盖项目文件？','是否允许运行终端命令？','是否允许安装依赖？','是否允许启动本地服务？','是否允许操作浏览器？','是否允许操作桌面应用？','是否允许使用剪贴板？','是否允许截图？','是否允许询问外部 AI？','是否允许把截图、报错、项目结构或必要代码片段发给外部 AI？','是否允许多轮自主修复和重试？','是否有不能动的文件或目录？','是否有必须遵守的风格或偏好？'
]
class FullAutonomyPreflight:
    def request(self) -> dict:
        return {"authorization_mode":"full_autonomy", "questions": PREFLIGHT_QUESTIONS}
    def normalize_answers(self, answers: dict) -> dict:
        return {"provided_resources": answers, "confirmed": True}
