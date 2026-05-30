from backend.schemas.authorization_contract import AuthorizationContract, ExecutionPolicy

CAPABILITY_PRESETS={
 'standard':['read_files','operate_browser','take_screenshots','ask_external_ai'],
 'full_autonomy':['read_files','write_files','run_shell','install_dependencies','start_local_services','operate_browser','operate_desktop','use_clipboard','take_screenshots','ask_external_ai','share_diagnostics_with_external_ai','modify_code','autonomous_retry','autonomous_repair']
}

class AuthorizationContractBuilder:
    def build(self, authorization_mode: str='standard', provided_resources: dict | None=None, granted_capabilities: list[str] | None=None, available_external_ai: list[str] | None=None, protected_paths: list[str] | None=None) -> AuthorizationContract:
        caps=granted_capabilities or CAPABILITY_PRESETS.get(authorization_mode, CAPABILITY_PRESETS['standard'])
        full=authorization_mode=='full_autonomy'
        return AuthorizationContract(
            authorization_mode=authorization_mode,
            granted_capabilities=caps,
            provided_resources=provided_resources or {},
            available_external_ai=available_external_ai or [],
            execution_policy=ExecutionPolicy(
                ask_during_execution=not full,
                autonomous_retry=full,
                autonomous_repair=full,
                autonomous_external_ai_query=full and 'ask_external_ai' in caps,
                autonomous_visual_review=full and 'take_screenshots' in caps,
                autonomous_code_modification=full and 'modify_code' in caps,
            ),
            user_confirmed_authorization=full,
            protected_paths=protected_paths or [],
        )
