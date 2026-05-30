from fastapi import APIRouter
from pydantic import BaseModel
from backend.core.agent import create_llm_provider, Agent
from backend.core.goal_contract import GoalContractBuilder
from backend.core.authorization_contract import AuthorizationContractBuilder
from backend.core.full_autonomy_preflight import FullAutonomyPreflight
from backend.schemas.goal_contract import GoalContract
from backend.schemas.authorization_contract import AuthorizationContract

router=APIRouter(tags=['contracts'])

class PrepareGoalRequest(BaseModel):
    user_input: str
    goal_mode: str = 'autonomous'
    clarification_answers: str = ''

class PrepareAuthorizationRequest(BaseModel):
    authorization_mode: str = 'standard'
    provided_resources: dict = {}
    granted_capabilities: list[str] | None = None
    available_external_ai: list[str] = []
    protected_paths: list[str] = []

class StartTaskRequest(BaseModel):
    goal_contract: GoalContract
    authorization_contract: AuthorizationContract

@router.post('/task/prepare-goal')
async def prepare_goal(req: PrepareGoalRequest):
    return (await GoalContractBuilder(create_llm_provider()).build(req.user_input, req.goal_mode, req.clarification_answers)).model_dump()

@router.post('/task/confirm-goal')
async def confirm_goal(contract: GoalContract):
    data=contract.model_dump(); data['user_confirmed_goal']=True; return data

@router.get('/task/full-autonomy-preflight')
async def full_autonomy_preflight(): return FullAutonomyPreflight().request()

@router.post('/task/prepare-authorization')
async def prepare_authorization(req: PrepareAuthorizationRequest):
    return AuthorizationContractBuilder().build(req.authorization_mode, req.provided_resources, req.granted_capabilities, req.available_external_ai, req.protected_paths).model_dump()

@router.post('/task/confirm-authorization')
async def confirm_authorization(contract: AuthorizationContract):
    data=contract.model_dump(); data['user_confirmed_authorization']=True; return data

@router.post('/task/start')
async def start_task(req: StartTaskRequest):
    agent=Agent()
    events=[]
    async for ev in agent.run_with_contracts(req.goal_contract.model_dump(), req.authorization_contract.model_dump()):
        events.append(ev.to_dict())
    return {"events": events}
