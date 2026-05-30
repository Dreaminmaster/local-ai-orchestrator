class PromptProfile:
    def __init__(self, name: str, max_context_chars: int, strict_json: bool, reasoning_depth: str, allow_long_planning: bool):
        self.name=name; self.max_context_chars=max_context_chars; self.strict_json=strict_json; self.reasoning_depth=reasoning_depth; self.allow_long_planning=allow_long_planning
PROMPT_PROFILES={
    'small_local': PromptProfile('small_local',8000,True,'low',False),
    'medium_local': PromptProfile('medium_local',16000,True,'medium',True),
    'strong_remote': PromptProfile('strong_remote',60000,False,'high',True),
}
