# Tasks: Automated CI/CD Pipeline for Hostinger Deployment

**Input**: Design documents from `/specs/007-so-we-need/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/deploy-production.yml, quickstart.md

**Tests**: Tests are NOT included in this implementation as the feature specification does not explicitly request automated testing. Manual verification procedures are documented in quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and prepare for workflow configuration

- [X] T001 Create `.github/workflows/` directory structure at repository root
- [X] T002 [P] Verify existing deployment infrastructure on Hostinger (Docker, docker-compose, /opt/hostaway-mcp directory)

**Checkpoint**: Basic directory structure ready for workflow files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: SSH key generation and GitHub Secrets configuration - MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until GitHub Secrets are configured. User Stories 1 and 2 depend on this phase.

- [ ] T003 Generate Ed25519 SSH key pair for GitHub Actions deployment (local workstation)
- [ ] T004 Add SSH public key to Hostinger VPS `/root/.ssh/authorized_keys` with correct permissions (600)
- [ ] T005 Test SSH connection using generated private key to verify authentication works
- [ ] T006 Configure GitHub repository secret `SSH_PRIVATE_KEY` with full private key content (including headers)
- [ ] T007 [P] Configure GitHub repository secret `SSH_HOST` with value `72.60.233.157`
- [ ] T008 [P] Configure GitHub repository secret `SSH_USERNAME` with value `root`
- [ ] T009 [P] Configure GitHub repository secret `DEPLOY_PATH` with value `/opt/hostaway-mcp`
- [ ] T010 [P] Configure GitHub repository secret `SUPABASE_URL` from Supabase project settings
- [ ] T011 [P] Configure GitHub repository secret `SUPABASE_SERVICE_KEY` from Supabase project settings
- [ ] T012 [P] Configure GitHub repository secret `SUPABASE_ANON_KEY` from Supabase project settings
- [ ] T013 [P] Configure GitHub repository secret `HOSTAWAY_ACCOUNT_ID` from Hostaway account settings
- [ ] T014 [P] Configure GitHub repository secret `HOSTAWAY_SECRET_KEY` from Hostaway API settings
- [ ] T015 Verify all 9 required GitHub Secrets are present in repository settings

**Checkpoint**: Foundation ready - all secrets configured, SSH authentication working. User story implementation can now begin.

---

## Phase 3: User Story 1 - Automated Deployment on PR Merge (Priority: P1) 🎯 MVP

**Goal**: Implement GitHub Actions workflow that automatically triggers on PR merge to main, connects to Hostinger via SSH, and deploys the application

**Independent Test**: Merge a simple code change (e.g., update comment in README.md) to main and verify GitHub Actions workflow triggers within 30 seconds, completes deployment, and production server reflects the change

**Acceptance Criteria**:
- ✅ PR merge to main triggers workflow within 30 seconds (FR-001)
- ✅ Deployment completes within 10 minutes (FR-011)
- ✅ Production server updated with new code (FR-004)

### Implementation for User Story 1

- [X] T016 [US1] Create `.github/workflows/deploy-production.yml` with workflow name and trigger configuration (on push to main + workflow_dispatch)
- [X] T017 [US1] Add concurrency control configuration to prevent race conditions (group: production-deployment, cancel-in-progress: false)
- [X] T018 [US1] Add job definition with ubuntu-latest runner and 10-minute timeout
- [X] T019 [US1] Add checkout step using `actions/checkout@v4` with full history (fetch-depth: 0)
- [X] T020 [US1] Add SSH deployment step using `appleboy/ssh-action@v1.0.0` with secrets for host, username, and key
- [X] T021 [US1] Implement SSH script section: navigate to deploy path using `${{ secrets.DEPLOY_PATH }}`
- [X] T022 [US1] Implement SSH script section: pull latest code from GitHub (git fetch + git reset --hard origin/main)
- [X] T023 [US1] Implement SSH script section: generate `.env` file from GitHub Secrets with correct format
- [X] T024 [US1] Implement SSH script section: set `.env` file permissions to 600 for security
- [X] T025 [US1] Implement SSH script section: stop existing Docker containers (docker compose -f docker-compose.prod.yml down)
- [X] T026 [US1] Implement SSH script section: build new Docker image (docker compose -f docker-compose.prod.yml build --no-cache)
- [X] T027 [US1] Implement SSH script section: start new Docker containers (docker compose -f docker-compose.prod.yml up -d)
- [X] T028 [US1] Add workflow syntax validation using GitHub's workflow editor or `actionlint`
- [ ] T029 [US1] Test workflow using manual trigger (workflow_dispatch) to verify execution without PR merge
- [ ] T030 [US1] Verify workflow completes successfully and production server is updated

**Checkpoint**: At this point, User Story 1 should be fully functional - automatic deployment on PR merge works end-to-end

---

## Phase 4: User Story 2 - Secure Credential Management (Priority: P1)

**Goal**: Ensure all credentials are masked in logs and never exposed in repository or workflow output

**Independent Test**: Trigger deployment and inspect GitHub Actions logs to verify all secret values appear as `***`, check repository for any committed credentials, verify SSH authentication succeeds using stored secrets

**Acceptance Criteria**:
- ✅ SSH key never exposed in logs (FR-006, SC-003)
- ✅ Environment variables masked in workflow output (FR-006, SC-003)
- ✅ No secrets committed to repository (FR-006, SC-003)

### Implementation for User Story 2

- [X] T031 [US2] Review `.github/workflows/deploy-production.yml` for any hardcoded credentials or secrets
- [X] T032 [US2] Verify all secret references use `${{ secrets.NAME }}` syntax for automatic masking
- [X] T033 [US2] Add comments to workflow documenting which secrets are used and why (for audit purposes)
- [X] T034 [US2] Create `.env.example` file (if not exists) documenting required environment variables WITHOUT values
- [X] T035 [US2] Add `.env` to `.gitignore` to prevent accidental commit of production credentials
- [X] T036 [US2] Verify `script_stop: true` in SSH action configuration to fail on first error
- [X] T037 [US2] Verify bash error handling (`set -e`, `set -u`) in deployment script within workflow
- [ ] T038 [US2] Test deployment and inspect workflow logs to confirm all secrets are masked as `***`
- [X] T039 [US2] Search repository history for any committed secrets using `git log -S "SECRET_PATTERN"`
- [X] T040 [US2] Document secret rotation procedure in `specs/007-so-we-need/quickstart.md` (already exists, verify completeness)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - automatic deployment with secure credential management

---

## Phase 5: User Story 3 - Deployment Status Visibility (Priority: P2)

**Goal**: Provide clear deployment status and logs in GitHub Actions UI for troubleshooting

**Independent Test**: Trigger deployment and verify GitHub Actions UI shows step-by-step progress, complete logs are accessible, and deployment status is clearly visible

**Acceptance Criteria**:
- ✅ Real-time deployment progress visible in GitHub Actions (FR-008)
- ✅ Deployment logs accessible for 90 days (FR-009)
- ✅ Failure notifications sent via GitHub Actions UI (FR-008, SC-004)

### Implementation for User Story 3

- [X] T041 [US3] Add step names with clear descriptions to all workflow steps for better visibility
- [X] T042 [US3] Add reporting step at end of workflow to summarize deployment status (success/failure)
- [X] T043 [US3] Add `if: always()` condition to reporting step to ensure it runs even on failure
- [X] T044 [US3] Implement success message with production server URL in reporting step
- [X] T045 [US3] Implement failure message with troubleshooting hints in reporting step
- [X] T046 [US3] Add echo statements in deployment script for key milestones (backup created, build started, etc.)
- [X] T047 [US3] Add timestamp logging to deployment script steps for performance tracking
- [ ] T048 [US3] Test workflow and verify all steps show clear status indicators (✅ success, ❌ failure)
- [ ] T049 [US3] Verify GitHub sends email notification on workflow failure (check user notification settings)
- [X] T050 [US3] Add workflow status badge to repository README.md using GitHub Actions badge syntax

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - deployment with security and full visibility

---

## Phase 6: User Story 4 - Rollback on Deployment Failure (Priority: P2)

**Goal**: Implement backup-before-deploy pattern and automatic rollback on health check failure to prevent production downtime

**Independent Test**: Intentionally break deployment (e.g., introduce syntax error in code), verify previous version is preserved, production server continues running, and deployment failure is logged

**Acceptance Criteria**:
- ✅ Previous version backed up before deployment (FR-007, FR-012)
- ✅ Automatic rollback on health check failure (FR-012, SC-006)
- ✅ Failed deployment logged with error details (FR-009)

### Implementation for User Story 4

- [X] T051 [US4] Add backup creation logic in SSH deployment script before pulling new code
- [X] T052 [US4] Implement timestamped backup directory creation (backups/YYYYMMDD-HHMMSS)
- [X] T053 [US4] Implement backup of current `src/` directory to backup folder
- [X] T054 [US4] Implement backup of current `.env` file to backup folder
- [X] T055 [US4] Implement backup of current Docker image using `docker save` to backup folder
- [X] T056 [US4] Add 10-second sleep after container startup to allow application initialization
- [X] T057 [US4] Implement health check using `curl -f http://localhost:8080/health` after deployment
- [X] T058 [US4] Implement rollback logic if health check fails (stop containers, load backup image, restart)
- [X] T059 [US4] Implement exit code 1 on health check failure to mark workflow as failed
- [X] T060 [US4] Implement cleanup of old backups (keep last 5, delete older) after successful deployment
- [ ] T061 [US4] Test rollback by intentionally breaking health endpoint and verifying automatic recovery
- [ ] T062 [US4] Test rollback by introducing Docker build error and verifying previous version preserved
- [ ] T063 [US4] Verify workflow logs show rollback actions when deployment fails
- [X] T064 [US4] Document manual rollback procedure in `specs/007-so-we-need/quickstart.md` (already exists, verify completeness)

**Checkpoint**: All user stories should now be independently functional - complete CI/CD pipeline with automatic rollback

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and security hardening

- [ ] T065 [P] Run ShellCheck on all bash scripts in workflow to catch potential errors
- [X] T066 [P] Validate workflow YAML syntax using GitHub's workflow validator or `actionlint`
- [X] T067 Review quickstart.md and verify all setup steps are accurate and complete
- [ ] T068 Test complete deployment workflow end-to-end following quickstart.md instructions
- [ ] T069 Verify all 12 functional requirements (FR-001 through FR-012) are satisfied
- [ ] T070 Verify all 8 success criteria (SC-001 through SC-008) can be measured
- [ ] T071 [P] Add deployment workflow diagram to documentation (optional enhancement)
- [ ] T072 [P] Schedule first SSH key rotation reminder (90 days from setup)
- [ ] T073 Create test PR to verify automatic deployment workflow triggers on merge
- [ ] T074 Monitor first 3 production deployments for success rate and timing
- [ ] T075 Document any issues encountered during first deployments and update quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS User Stories 1 and 2
- **User Story 1 (Phase 3)**: Depends on Foundational completion - automatic deployment core functionality
- **User Story 2 (Phase 4)**: Depends on Foundational completion AND User Story 1 - adds security verification
- **User Story 3 (Phase 5)**: Depends on User Story 1 completion - adds visibility to existing deployment
- **User Story 4 (Phase 6)**: Depends on User Story 1 completion - adds rollback to existing deployment
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2) - SSH keys and secrets must be configured first
- **User Story 2 (P1)**: Depends on Foundational (Phase 2) - verifies secrets configured in Phase 2
- **User Story 3 (P2)**: Depends on User Story 1 - enhances visibility of existing deployment workflow
- **User Story 4 (P2)**: Depends on User Story 1 - adds safety mechanisms to existing deployment workflow

### Implementation Order

**Sequential (Recommended)**:
1. Phase 1: Setup → Phase 2: Foundational
2. Phase 3: User Story 1 (core deployment) ✅ **MVP STOPS HERE**
3. Phase 4: User Story 2 (security verification)
4. Phase 5: User Story 3 (visibility enhancements)
5. Phase 6: User Story 4 (rollback safety)
6. Phase 7: Polish

**Parallel Opportunities (if team has capacity)**:
- After Phase 2 completes: User Story 2 can proceed in parallel with User Story 1 (both just verify secrets)
- After User Story 1 completes: User Stories 3 and 4 can proceed in parallel (different sections of workflow)

### Within Each Phase

**Phase 2 (Foundational)**: Tasks T007-T014 marked [P] can run in parallel (different secrets)
**Phase 3 (User Story 1)**: Tasks must run sequentially (all modify same workflow file)
**Phase 4 (User Story 2)**: Tasks must run sequentially (review and verify existing workflow)
**Phase 5 (User Story 3)**: Tasks must run sequentially (enhance existing workflow)
**Phase 6 (User Story 4)**: Tasks must run sequentially (add to existing SSH script in workflow)
**Phase 7 (Polish)**: Tasks T065-T066 and T071-T072 marked [P] can run in parallel

---

## Parallel Example: Foundational Phase (GitHub Secrets)

```bash
# Configure all GitHub Secrets in parallel (different secrets, no dependencies):
Task: "Configure GitHub repository secret SSH_HOST with value 72.60.233.157"
Task: "Configure GitHub repository secret SSH_USERNAME with value root"
Task: "Configure GitHub repository secret DEPLOY_PATH with value /opt/hostaway-mcp"
Task: "Configure GitHub repository secret SUPABASE_URL from Supabase project settings"
Task: "Configure GitHub repository secret SUPABASE_SERVICE_KEY from Supabase project settings"
Task: "Configure GitHub repository secret SUPABASE_ANON_KEY from Supabase project settings"
Task: "Configure GitHub repository secret HOSTAWAY_ACCOUNT_ID from Hostaway account settings"
Task: "Configure GitHub repository secret HOSTAWAY_SECRET_KEY from Hostaway API settings"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only - Core Deployment)

**Goal**: Get basic automated deployment working as quickly as possible

1. Complete Phase 1: Setup (T001-T002) - 15 minutes
2. Complete Phase 2: Foundational (T003-T015) - 30-45 minutes
   - Generate SSH keys
   - Configure all GitHub Secrets
3. Complete Phase 3: User Story 1 (T016-T030) - 60-90 minutes
   - Create workflow file
   - Implement deployment steps
   - Test deployment
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Merge test PR to main
   - Verify workflow triggers
   - Verify deployment succeeds
   - Verify production server updated
5. **MVP COMPLETE** - Basic automated deployment functional

**Total MVP Time**: 2-3 hours

**MVP Success Criteria**:
- ✅ PR merge to main triggers deployment
- ✅ Deployment completes within 10 minutes
- ✅ Production server updated with new code
- ✅ Zero manual deployment steps required

### Incremental Delivery (Add Remaining User Stories)

**After MVP is validated and working:**

6. Add User Story 2 (T031-T040) - Security verification - 30 minutes
   - Verify secret masking
   - Test credential security
7. Add User Story 3 (T041-T050) - Visibility enhancements - 30-45 minutes
   - Add status reporting
   - Improve logging
   - Add status badge
8. Add User Story 4 (T051-T064) - Rollback safety - 45-60 minutes
   - Implement backup creation
   - Implement health checks
   - Implement rollback logic
   - Test failure scenarios
9. Complete Phase 7 (T065-T075) - Final polish - 30-45 minutes
   - Validation and testing
   - Documentation review

**Total Complete Implementation Time**: 4-6 hours

### Value Delivery Timeline

- **Hour 2-3**: MVP (User Story 1) - Manual deployments eliminated ✅
- **Hour 3-4**: Add security verification (User Story 2) - Credential safety confirmed ✅
- **Hour 4-5**: Add visibility (User Story 3) - Troubleshooting capability improved ✅
- **Hour 5-6**: Add rollback safety (User Story 4) - Production stability guaranteed ✅

### Parallel Team Strategy

If multiple developers available:

1. **Developer A**: Complete Foundational phase (T003-T015) - SSH and secrets setup
2. **Once Foundational complete:**
   - **Developer A**: User Story 1 (T016-T030) - Core deployment workflow
   - **Developer B**: User Story 2 (T031-T040) - Security verification (can start after secrets configured)
3. **Once User Story 1 complete:**
   - **Developer A**: User Story 4 (T051-T064) - Rollback implementation
   - **Developer B**: User Story 3 (T041-T050) - Visibility enhancements
4. **Both developers**: Polish phase together (T065-T075)

**Parallel Team Time**: 3-4 hours total

---

## Task Count Summary

- **Phase 1 (Setup)**: 2 tasks
- **Phase 2 (Foundational)**: 13 tasks (8 parallelizable)
- **Phase 3 (User Story 1 - P1)**: 15 tasks
- **Phase 4 (User Story 2 - P1)**: 10 tasks
- **Phase 5 (User Story 3 - P2)**: 10 tasks
- **Phase 6 (User Story 4 - P2)**: 14 tasks
- **Phase 7 (Polish)**: 11 tasks (4 parallelizable)

**Total Tasks**: 75 tasks
**Parallelizable Tasks**: 12 tasks (16%)
**MVP Tasks (Setup + Foundational + US1)**: 30 tasks (40%)

---

## Validation Checklist

### User Story 1 Validation (MVP)
- [ ] Workflow appears in GitHub Actions tab
- [ ] Workflow triggers within 30 seconds of PR merge
- [ ] Workflow completes in < 10 minutes
- [ ] Production server reflects merged code changes
- [ ] Health endpoint returns 200 OK
- [ ] No manual deployment steps required

### User Story 2 Validation (Security)
- [ ] Workflow logs show `***` for all secret values
- [ ] No credentials in repository (git log search clean)
- [ ] SSH authentication succeeds using GitHub Secrets
- [ ] .env file created on server with correct values
- [ ] .env file has 600 permissions

### User Story 3 Validation (Visibility)
- [ ] GitHub Actions UI shows step-by-step progress
- [ ] All workflow steps have clear names
- [ ] Success/failure status clearly visible
- [ ] Complete logs accessible in GitHub UI
- [ ] Email notification received on failure
- [ ] Status badge in README.md updates correctly

### User Story 4 Validation (Rollback)
- [ ] Backup created before each deployment
- [ ] Backup contains src/, .env, and Docker image
- [ ] Health check runs after deployment
- [ ] Rollback triggers on health check failure
- [ ] Production server restored to previous version on failure
- [ ] Old backups cleaned up (only 5 retained)
- [ ] Manual rollback procedure documented and tested

---

## Notes

- All tasks modify `.github/workflows/deploy-production.yml` or configure GitHub Secrets via GitHub UI
- No application source code (`src/`) changes required
- Existing deployment infrastructure (Docker, docker-compose) on Hostinger is used as-is
- Workflow uses existing `docker-compose.prod.yml` and assumes `/opt/hostaway-mcp` deployment path
- Health check endpoint `/health` must exist in application (dependency from spec.md)
- Tasks are ordered for sequential execution within each phase
- Marked [P] tasks can run in parallel if team capacity allows
- Each user story phase ends with a checkpoint for independent validation
- MVP can be deployed after just User Story 1 (30 tasks, 2-3 hours)
- Avoid: hardcoding credentials, skipping secret masking validation, committing .env files
- Testing philosophy: Manual verification via quickstart.md procedures (no automated tests requested)
