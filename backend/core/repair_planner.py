from .failure_taxonomy import FailureTaxonomy
class RepairPlanner:
    def __init__(self): self.taxonomy=FailureTaxonomy()
    def plan(self, failure_text: str, goal_contract: dict | None=None, authorization_contract: dict | None=None) -> dict:
        kind=self.taxonomy.classify(failure_text)
        actions={
            'json_parse_failed':['retry_short_prompt','use_json_repair','escalate_to_external_ai'],
            'local_model_uncertain':['reduce_context','ask_external_ai','request_clarification_if_goal_related'],
            'context_overflow':['shrink_context','retrieve_relevant_evidence_only','summarize_tool_results'],
            'tool_result_too_long':['summarize_tool_result','keep_errors_only','retry_with_summary'],
            'external_ai_needed':['choose_external_ai','ask_external_ai','save_answer_as_evidence'],
            'goal_unclear':['create_clarification_session','update_goal_contract'],
            'authorization_missing':['request_capability','create_confirmation_request','update_authorization_contract'],
            'resource_missing':['ask_for_resource','search_alternative_path','stop_if_required_resource_missing'],
            'selector_failed':['retry_with_alternative_selector','fallback_to_desktop_visual','capture_screenshot'],
            'external_ai_failed':['switch_external_ai','fallback_to_api_or_web','request_login'],
            'visual_quality_failed':['ask_visual_model_for_specific_fixes','iterate_design_changes','compare_before_after'],
            'code_failed':['run_code_agent','inspect_logs','apply_minimal_fix','rerun_tests'],
            'network_failure':['retry_with_backoff','switch_tool'],
            'permission_failure':['request_confirmation','stop_if_denied'],
            'tool_failure':['retry','fallback_skill','ask_user_if_blocked'],
        }
        return {'failure_type': kind, 'repair_actions': actions.get(kind, actions['tool_failure']), 'should_retry': kind not in ['permission_failure','authorization_missing'], 'goal_related': kind=='goal_unclear', 'authorization_related': kind=='authorization_missing'}
