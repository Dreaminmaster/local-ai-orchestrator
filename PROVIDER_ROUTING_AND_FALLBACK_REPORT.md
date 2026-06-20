# Provider Routing And Fallback Report

## Routing Policies

- Local first
- Best capability
- Fully local
- Manual confirmation

Users can configure web Provider priority, automatic external use, confirmation requirement, and maximum external calls per task.

## Safety Rules

- Disabled, failed, and unconfigured Providers are excluded.
- Fully local mode never chooses web AI.
- Without automatic permission, routing returns manual confirmation instead of silently calling a Provider.
- If no suitable Provider exists, rule fallback remains available.
- No cross-provider live fallback was performed during this sprint.

Validation result: **PASS**
