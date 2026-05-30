from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Any

AuthorizationMode = Literal["standard", "full_autonomy"]

class ExecutionPolicy(BaseModel):
    ask_during_execution: bool = True
    autonomous_retry: bool = False
    autonomous_repair: bool = False
    autonomous_external_ai_query: bool = False
    autonomous_visual_review: bool = False
    autonomous_code_modification: bool = False
    allow_sensitive_upload: bool = False

class AuthorizationContract(BaseModel):
    authorization_mode: AuthorizationMode = "standard"
    granted_capabilities: list[str] = Field(default_factory=list)
    provided_resources: dict[str, Any] = Field(default_factory=dict)
    available_external_ai: list[str] = Field(default_factory=list)
    execution_policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    user_confirmed_authorization: bool = False
    denied_capabilities: list[str] = Field(default_factory=list)
    protected_paths: list[str] = Field(default_factory=list)
