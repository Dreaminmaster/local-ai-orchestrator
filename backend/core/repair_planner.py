from .failure_taxonomy import FailureTaxonomy
class RepairPlanner:
    def __init__(self): self.taxonomy=FailureTaxonomy()
    def plan(self, failure_text: str) -> dict:
        kind=self.taxonomy.classify(failure_text)
        actions={
            'login_failure':['ask_user_to_login','reuse_persistent_profile'],
            'network_failure':['retry_with_backoff','switch_tool'],
            'code_failure':['run_code_agent','inspect_logs','apply_minimal_fix'],
            'permission_failure':['request_confirmation','stop_if_denied'],
            'quality_failure':['ask_external_ai_for_review','iterate_changes'],
            'tool_failure':['retry','fallback_skill','ask_user_if_blocked'],
        }
        return {'failure_type': kind, 'repair_actions': actions[kind], 'should_retry': kind!='permission_failure'}
