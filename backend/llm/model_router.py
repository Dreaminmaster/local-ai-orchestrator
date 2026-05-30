from dataclasses import dataclass
@dataclass
class ModelCapability:
    provider: str
    strengths: list[str]
    supports_vision: bool = False
    supports_code: bool = False
    supports_long_context: bool = False
class ModelRouter:
    def __init__(self):
        self.models={
            'chatgpt': ModelCapability('chatgpt',['general','writing','vision'], True, True, True),
            'claude': ModelCapability('claude',['analysis','architecture','long_context'], False, True, True),
            'deepseek': ModelCapability('deepseek',['code','reasoning','chinese'], False, True, False),
            'gemini': ModelCapability('gemini',['vision','multimodal','long_context'], True, False, True),
        }
    def route(self, task_type: str) -> str:
        if task_type in ['visual','design']: return 'gemini'
        if task_type in ['code','debug']: return 'deepseek'
        if task_type in ['analysis','architecture']: return 'claude'
        return 'chatgpt'
