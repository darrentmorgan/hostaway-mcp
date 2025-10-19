# Feature Specification: Automated CI/CD Pipeline for Hostinger Deployment

**Feature Branch**: `007-so-we-need`
**Created**: 2025-10-19
**Status**: Draft
**Input**: User description: "So we need to create a CI/CD pipeline and there needs to be an SSH key on our GitHub with all the environment variables stored as secrets. This should trigger when we have a successful pull request merged to main. We should then deploy to hosting. So we need to automate this whole process."

## User Scenarios & Testing

### User Story 1 - Automated Deployment on PR Merge (Priority: P1)

As a developer, when I merge a pull request to the main branch, the system automatically deploys the updated code to the Hostinger production server without manual intervention.

**Why this priority**: This is the core automation that eliminates manual deployment steps, reduces human error, and ensures consistent deployments. Without this, the entire CI/CD pipeline has no value.

**Independent Test**: Can be fully tested by merging a simple code change (e.g., updating a comment) to main and verifying the production server reflects the change within expected timeframe.

**Acceptance Scenarios**:

1. **Given** a pull request has been approved and all tests pass, **When** the PR is merged to main branch, **Then** the deployment workflow automatically triggers within 30 seconds
2. **Given** the deployment workflow has started, **When** code is deployed to Hostinger, **Then** the production server is updated with the new code within 5 minutes
3. **Given** a deployment completes successfully, **When** checking the production health endpoint, **Then** the server reports healthy status with the new version number

---

### User Story 2 - Secure Credential Management (Priority: P1)

As a developer, I can configure deployment credentials (SSH keys, environment variables) once in GitHub repository secrets, and the deployment pipeline uses them securely without exposing sensitive data in logs or code.

**Why this priority**: Security is critical for production deployments. Without secure credential management, the deployment process exposes the production environment to unauthorized access.

**Independent Test**: Can be tested by verifying that deployment logs do not contain plaintext credentials, SSH keys are never committed to the repository, and the deployment successfully authenticates to Hostinger using stored secrets.

**Acceptance Scenarios**:

1. **Given** SSH private key is stored as a GitHub secret, **When** the deployment workflow runs, **Then** it authenticates to Hostinger without exposing the key in logs
2. **Given** environment variables (API keys, database URLs) are stored as GitHub secrets, **When** deployment occurs, **Then** the production server receives the correct configuration without variables appearing in workflow logs
3. **Given** a developer views workflow logs, **When** inspecting deployment output, **Then** all sensitive values are masked with asterisks

---

### User Story 3 - Deployment Status Visibility (Priority: P2)

As a developer, I can view the real-time status of deployment workflows directly in GitHub, including success/failure notifications and access to deployment logs for troubleshooting.

**Why this priority**: Visibility into deployment status enables quick identification and resolution of deployment failures. While important, the deployment can function without enhanced visibility features.

**Independent Test**: Can be tested by triggering a deployment and verifying that GitHub Actions UI shows real-time progress, completion status, and accessible logs.

**Acceptance Scenarios**:

1. **Given** a deployment workflow is running, **When** viewing the GitHub Actions tab, **Then** I can see current deployment progress with step-by-step status
2. **Given** a deployment fails, **When** checking GitHub notifications, **Then** I receive an immediate notification with a link to the failed workflow
3. **Given** a deployment completed (success or failure), **When** viewing the workflow run, **Then** I can access complete logs for all deployment steps

---

### User Story 4 - Rollback on Deployment Failure (Priority: P2)

As a developer, when a deployment fails (build errors, test failures, or deployment errors), the system automatically maintains the previous working version on the production server to prevent downtime.

**Why this priority**: Automatic rollback prevents broken deployments from affecting production users. This is important for reliability but not required for basic deployment functionality.

**Independent Test**: Can be tested by intentionally introducing a deployment failure (e.g., broken Docker build) and verifying the production server continues running the previous version.

**Acceptance Scenarios**:

1. **Given** a deployment fails during the build phase, **When** the workflow detects the failure, **Then** the production server continues running the previous working version
2. **Given** a deployment fails during the Docker container startup, **When** the health check detects the failure, **Then** the workflow preserves the previous container and reports the failure
3. **Given** a failed deployment has been rolled back, **When** checking deployment history, **Then** the failed attempt is logged with error details for debugging

---

### Edge Cases

- What happens when GitHub Actions is down or unavailable during a PR merge?
- How does the system handle concurrent PR merges to main (race conditions)?
- What happens when the Hostinger server is unreachable during deployment?
- How does the system handle partial deployments (code uploaded but container failed to start)?
- What happens when environment secrets are missing or malformed?
- How does the system handle deployment timeouts (server taking too long to respond)?
- What happens when the SSH key expires or becomes invalid?
- How does the system handle disk space issues on the Hostinger server?

## Requirements

### Functional Requirements

- **FR-001**: System MUST trigger deployment workflow automatically when a pull request is merged to the main branch
- **FR-002**: System MUST authenticate to Hostinger server using SSH key stored in GitHub repository secrets
- **FR-003**: System MUST transfer all required environment variables from GitHub secrets to the production server during deployment
- **FR-004**: System MUST build Docker container image on Hostinger server using the deployed code
- **FR-005**: System MUST verify deployment success by checking the production server health endpoint
- **FR-006**: System MUST mask all sensitive values (SSH keys, API keys, passwords) in workflow logs
- **FR-007**: System MUST preserve the previous working version if deployment fails
- **FR-008**: System MUST send deployment status notifications (success or failure) via GitHub Actions UI
- **FR-009**: System MUST store deployment logs for at least 90 days for troubleshooting
- **FR-010**: System MUST prevent deployments when required GitHub secrets are missing or invalid
- **FR-011**: System MUST complete full deployment cycle (trigger to production verification) within 10 minutes
- **FR-012**: System MUST support rollback to the previous deployment if the new deployment fails health checks

### Key Entities

- **Deployment Workflow**: Automated process triggered by PR merge events containing steps for code transfer, building, and deployment verification
- **GitHub Secrets**: Encrypted storage for sensitive deployment credentials including SSH private key, environment variables, and server connection details
- **Deployment Target**: Hostinger production server at specified IP address running Docker containers for the application
- **Health Check**: Verification endpoint that confirms successful deployment and application availability
- **Deployment Log**: Record of all deployment activities including timestamps, status, and error messages
- **Previous Version Backup**: Preserved copy of the working deployment used for rollback in case of failures

## Success Criteria

### Measurable Outcomes

- **SC-001**: Developers can merge a PR to main and see the changes live on production within 10 minutes without manual intervention
- **SC-002**: 95% of deployments complete successfully without requiring manual intervention or rollback
- **SC-003**: Zero sensitive credentials are exposed in deployment logs or repository code
- **SC-004**: Deployment failures are detected and reported within 30 seconds of occurrence
- **SC-005**: System maintains 99.9% uptime during deployments (no user-facing downtime from deployment process)
- **SC-006**: Failed deployments preserve the previous working version 100% of the time
- **SC-007**: Developers can troubleshoot failed deployments using workflow logs without needing server access
- **SC-008**: Time spent on manual deployments is reduced from 15 minutes to 0 minutes per deployment

## Assumptions

- GitHub Actions is available and has sufficient runner capacity for deployment workflows
- Hostinger server has Docker and docker-compose installed and configured
- The main branch is protected and requires pull request reviews before merging
- Deployment requires only SSH access to Hostinger (no additional VPN or network requirements)
- The application uses Docker containers for deployment (as indicated by existing docker-compose.prod.yml)
- Standard GitHub Actions runners have network access to the Hostinger server IP address
- The Hostinger server has adequate disk space for storing deployment backups
- Environment variables stored in GitHub secrets are kept up-to-date by the development team

## Dependencies

- **External Service**: GitHub Actions must be operational for automated deployments
- **Infrastructure**: Hostinger VPS server must be accessible via SSH on standard port 22
- **Configuration**: Docker and docker-compose must be pre-installed on Hostinger server
- **Security**: SSH key pair must be generated with appropriate permissions (private key in GitHub, public key on Hostinger)
- **Existing Code**: deploy-to-hostinger-secure.sh script provides foundation for deployment steps
- **Application**: Health check endpoint (/health) must be available for deployment verification

## Out of Scope

- Setting up multi-environment deployments (staging, QA, etc.) - only production deployment
- Automated database migrations as part of deployment pipeline
- Performance testing or load testing in CI/CD pipeline
- Blue-green or canary deployment strategies
- Automated security scanning or vulnerability assessment
- Infrastructure as Code (IaC) for provisioning Hostinger server
- Monitoring and alerting system integration beyond deployment notifications
- Custom deployment approval workflows or manual deployment gates
