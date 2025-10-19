# Implementation Plan: Automated CI/CD Pipeline for Hostinger Deployment

**Branch**: `007-so-we-need` | **Date**: 2025-10-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-so-we-need/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement automated CI/CD pipeline using GitHub Actions that triggers on PR merge to main branch, securely authenticates to Hostinger VPS using SSH keys and environment variables stored in GitHub Secrets, deploys Docker-based Python application with rollback capability, and provides deployment status visibility through GitHub Actions UI. The pipeline will reduce manual deployment time from 15 minutes to 0 and achieve 95% deployment success rate with 99.9% uptime.

## Technical Context

**Language/Version**: YAML (GitHub Actions workflow), Bash scripting
**Primary Dependencies**: GitHub Actions (CI/CD platform), SSH client, Docker, docker-compose
**Storage**: GitHub Secrets (encrypted credential storage), Hostinger VPS filesystem (deployment artifacts and backups)
**Testing**: GitHub Actions workflow validation, deployment verification via health check endpoint
**Target Platform**: GitHub Actions runners (Ubuntu latest), Hostinger VPS (Ubuntu 24.04 with Docker)
**Project Type**: Single project (CI/CD infrastructure)
**Performance Goals**: <10 minute total deployment time (trigger to production verification), <30 second failure detection
**Constraints**: SSH-only access to Hostinger, no additional VPN required, must preserve previous version on failure, zero credential exposure in logs
**Scale/Scope**: Single production environment, ~50-100 deployments per month, Docker-based Python FastAPI application

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Assessment (Pre-Research)

### Principle I: API-First Design
**Status**: ⚠️ NOT APPLICABLE - This feature is infrastructure/CI-CD, not an MCP tool or API endpoint
**Justification**: CI/CD pipeline is deployment automation, not user-facing functionality. No FastAPI endpoints or MCP tools are being created. The feature operates at the DevOps layer, not the application layer.

### Principle II: Type Safety (NON-NEGOTIABLE)
**Status**: ⚠️ PARTIALLY APPLICABLE - YAML and Bash scripts are not statically typed
**Justification**: GitHub Actions workflows use YAML (declarative, no type system). Deployment scripts use Bash (dynamically typed). However, we will:
- Validate workflow syntax using GitHub's workflow validator
- Use ShellCheck for bash script static analysis
- Implement error checking (`set -e`, `set -u`) in all bash scripts
- Test workflows in non-production branches before merging

### Principle III: Security by Default
**Status**: ✅ FULLY COMPLIANT
**Actions**:
- All credentials stored in GitHub Secrets (encrypted at rest)
- SSH private keys never exposed in logs or code
- Environment variables masked in workflow logs
- No secrets committed to repository
- Deployment uses secure SSH connection with key-based authentication
- Failed deployments do not expose sensitive configuration

### Principle IV: Test-Driven Development
**Status**: ✅ ADAPTED FOR CI/CD CONTEXT
**Actions**:
- Workflow syntax validation before merge
- Test deployments in feature branches before production
- Health check verification post-deployment
- Rollback testing with intentional failures
- Deployment log analysis for debugging

### Principle V: Async Performance
**Status**: ⚠️ NOT APPLICABLE - CI/CD workflows are sequential by nature
**Justification**: GitHub Actions workflows execute steps sequentially. Deployment must be ordered: code transfer → build → deploy → verify. Async operations would introduce race conditions. However, we will optimize for:
- Parallel Docker builds where possible
- Efficient file transfer (rsync vs full copy)
- Minimal downtime during deployment

### Overall Assessment (Pre-Research)

**GATE STATUS**: ✅ PASS WITH JUSTIFICATIONS

This feature operates at the infrastructure layer, not the application layer. Constitutional principles designed for API/MCP development are adapted appropriately:
- Security principles fully enforced
- Type safety adapted using validation tools for YAML/Bash
- Testing adapted for CI/CD workflows
- API-First and Async principles not applicable to deployment automation

**Complexity Justification**: Using industry-standard GitHub Actions and Bash scripting for CI/CD. No violations requiring technical debt documentation.

---

### Post-Design Re-Evaluation (After Phase 1)

**Date**: 2025-10-19
**Artifacts Reviewed**: research.md, data-model.md, contracts/*, quickstart.md

### Principle I: API-First Design
**Status**: ✅ CONFIRMED NOT APPLICABLE
**Design Evidence**: Workflow contract (contracts/deploy-production.yml) implements GitHub Actions YAML structure, not API endpoints. No OpenAPI specifications or MCP tool definitions generated. Design confirms DevOps/infrastructure focus.

### Principle II: Type Safety
**Status**: ✅ ENHANCED COMPLIANCE
**Design Evidence**:
- Workflow contract includes schema validation comments for all required secrets
- Secret validation contract (contracts/github-secrets-schema.md) defines strict typing rules for all configuration entities
- Data model (data-model.md) specifies validation rules for all workflow entities
- Bash scripts use strict error handling (`set -e`, `set -u`, `script_stop: true`)
- Type-safe state machines defined for Workflow Run, Deployment Backup, and Health Check entities
**Improvement**: Design added stricter validation than initially planned

### Principle III: Security by Default
**Status**: ✅ FULLY COMPLIANT - VALIDATED
**Design Evidence**:
- GitHub Secrets contract documents encryption, masking, and access control
- Workflow contract shows automatic secret masking in all steps
- Data model specifies `.env` file permissions (600)
- Security considerations section added to data model
- Quickstart includes security checklist and key rotation procedures
- No hardcoded credentials in any contract
**Validation**: All 9 security requirements from spec satisfied in design

### Principle IV: Test-Driven Development
**Status**: ✅ FULLY COMPLIANT - VALIDATED
**Design Evidence**:
- Quickstart includes test deployment procedures (manual trigger, test PR)
- Workflow contract includes health check verification step
- Test rollback procedure documented
- Deployment validation checklist in quickstart
- Failure scenarios documented in troubleshooting section
**Validation**: TDD adapted for CI/CD context with comprehensive testing strategy

### Principle V: Async Performance
**Status**: ✅ CONFIRMED NOT APPLICABLE - OPTIMIZED
**Design Evidence**:
- Workflow contract shows sequential steps with timeout enforcement (10 min)
- Data model specifies performance targets (<10 min total, <30s backup, <1m rollback)
- Research document includes timing breakdown and optimization strategies
- Concurrency control prevents race conditions while queuing deployments
**Validation**: Sequential execution required for deployment, but optimized for performance

### Post-Design Overall Assessment

**GATE STATUS**: ✅ PASS - DESIGN STRENGTHENS INITIAL ASSESSMENT

**Key Findings**:
1. **Type Safety**: Design added more validation than initially planned through contracts and data model validation rules
2. **Security**: All security measures documented and validated in contracts
3. **Testing**: Comprehensive test strategy defined in quickstart with specific procedures
4. **Performance**: Specific timing targets defined and optimization strategies documented

**Design Quality**: All Phase 1 artifacts (research, data model, contracts, quickstart) align with constitutional principles where applicable. No technical debt introduced.

**Complexity Status**: No increase in complexity beyond initial assessment. Industry-standard GitHub Actions patterns used consistently.

**Ready for Phase 2**: ✅ YES - Design artifacts complete and compliant

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
.github/
└── workflows/
    └── deploy-production.yml      # Main deployment workflow (NEW)

.github/                            # GitHub-specific configuration
└── actions/                        # Custom reusable actions (if needed)
    └── deploy-to-hostinger/        # Composite action for deployment (OPTIONAL)

deploy-to-hostinger-secure.sh       # Existing deployment script (REFERENCE)

docker-compose.prod.yml             # Existing production Docker config (REFERENCE)

Dockerfile.prod                     # Existing production Dockerfile (REFERENCE)

.env.example                        # Existing env var template (REFERENCE)
```

**Structure Decision**: Single project with CI/CD infrastructure

This feature adds GitHub Actions workflow configuration to the existing repository. The primary artifact is `.github/workflows/deploy-production.yml` which orchestrates the deployment using existing deployment scripts (deploy-to-hostinger-secure.sh) and Docker configurations. No changes to application source code (`src/`) are required.

**Key Files**:
- `.github/workflows/deploy-production.yml` - GitHub Actions workflow (new)
- `deploy-to-hostinger-secure.sh` - Existing deployment script (reference/modify)
- `docker-compose.prod.yml` - Existing Docker config (reference only)
- GitHub repository secrets - Configuration (not files, managed via GitHub UI)

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
