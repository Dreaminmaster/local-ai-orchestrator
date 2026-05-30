from pydantic import BaseModel
class ModelCapability(BaseModel):
    name: str
    provider: str
    context_window: int
    supports_tools: bool = False
    supports_vision: bool = False
    json_reliability: str = 'medium'
    best_for: list[str] = []
    weak_for: list[str] = []
class ModelCapabilityRegistry:
    def __init__(self): self.models={}
    def register(self, model: ModelCapability): self.models[model.name]=model
    def get(self, model_name: str) -> ModelCapability | None: return self.models.get(model_name)
    def choose_prompt_profile(self, model_name: str) -> str:
        m=self.get(model_name)
        if not m: return 'small_local'
        if m.context_window <= 8192: return 'small_local'
        if m.context_window <= 32768: return 'medium_local'
        return 'strong_remote'
