from fastapi import APIRouter
from pydantic import BaseModel
from backend.core.agent import create_llm_provider, Agent
from backend.core.goal_contract import GoalContractBuilder
from backend.core.authorization_contract import AuthorizationContractBuilder
from backend.core.dynamic_preflight import DynamicPreflightAnalyzer
from backend.core.clarification_session import ClarificationSessionService, clarification_store
from backend.schemas.goal_contract import GoalContract
from backend.schemas.authorization_contract import AuthorizationContract

router=APIRouter(tags=['contracts'])

class PrepareGoalRequest(BaseModel):
    user_input: str
    goal_mode: str = 'autonomous'
    clarification_answers: str = ''

class ConfirmGoalRequest(BaseModel):
    clarification_session_id: str | None = None
    answers: list[dict] = []
    draft_goal_contract: GoalContract | None = None

class PrepareAuthorizationRequest(BaseModel):
    authorization_mode: str = 'standard'
    provided_resources: dict = {}
    granted_capabilities: list[str] | None = None
    available_external_ai: list[str] = []
    protected_paths: list[str] = []
    preflight_result: dict | None = None

class PreflightRequest(BaseModel):
    user_input: str
    goal_contract: dict | None = None

class StartTaskRequest(BaseModel):
    goal_contract: GoalContract
    authorization_contract: AuthorizationContract

@router.post('/task/prepare-goal')
async def prepare_goal(req: PrepareGoalRequest):
    llm=create_llm_provider()
    if req.goal_mode == 'clarify_first' and not req.clarification_answers:
        prepared=await ClarificationSessionService(llm).prepare(req.user_input, req.goal_mode)
        if prepared.get('needs_clarification'):
            return prepared
    contract=await GoalContractBuilder(llm).build(req.user_input, req.goal_mode, req.clarification_answers)
    return {"needs_clarification": False, "goal_contract": contract.model_dump()}

@router.post('/task/confirm-goal')
async def confirm_goal(req: ConfirmGoalRequest):
    llm=create_llm_provider()
    if req.draft_goal_contract:
        data=req.draft_goal_contract.model_dump(); data['user_confirmed_goal']=True; return data
    if not req.clarification_session_id:
        raise ValueError('clarification_session_id or draft_goal_contract required')
    service=ClarificationSessionService(llm)
    session=service.answer(req.clarification_session_id, req.answers)
    summary=service.summary(session)
    contract=await GoalContractBuilder(llm).build(session.original_input, session.goal_mode, summary)
    data=contract.model_dump(); data['user_confirmed_goal']=True; data['clarification_summary']=summary
    session.status='contract_generated'; clarification_store.update(session)
    return data

@router.post('/task/full-autonomy-preflight')
async def full_autonomy_preflight(req: PreflightRequest):
    return await DynamicPreflightAnalyzer(create_llm_provider()).analyze(req.user_input, req.goal_contract)

@router.post('/task/prepare-authorization')
async def prepare_authorization(req: PrepareAuthorizationRequest):
    caps=req.granted_capabilities
    if not caps and req.preflight_result:
        caps=req.preflight_result.get('required_capabilities')
    return AuthorizationContractBuilder().build(req.authorization_mode, req.provided_resources, caps, req.available_external_ai, req.protected_paths).model_dump()

@router.post('/task/confirm-authorization')
async def confirm_authorization(contract: AuthorizationContract):
    data=contract.model_dump(); data['user_confirmed_authorization']=True; return data

@router.post('/task/start')
async def start_task(req: StartTaskRequest):
    agent=Agent(); events=[]
    async for ev in agent.run_with_contracts(req.goal_contract.model_dump(), req.authorization_contract.model_dump()):
        events.append(ev.to_dict())
    return {"events": events}
