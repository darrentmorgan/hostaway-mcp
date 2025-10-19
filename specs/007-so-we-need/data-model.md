# Data Model: CI/CD Pipeline Configuration

**Feature**: Automated CI/CD Pipeline for Hostinger Deployment
**Phase**: 1 - Design & Contracts
**Date**: 2025-10-19

## Overview

This feature is primarily configuration-based (GitHub Actions workflows and bash scripts). The "data model" consists of configuration structures and workflow artifacts rather than traditional application data entities.

## Configuration Entities

### 1. GitHub Secrets (Encrypted Storage)

**Purpose**: Store sensitive deployment credentials securely

**Attributes**:
- `SSH_PRIVATE_KEY` (string): Ed25519 private key for Hostinger authentication
- `SSH_HOST` (string): Hostinger server IP address (72.60.233.157)
- `SSH_USERNAME` (string): Server username for SSH connection (root)
- `DEPLOY_PATH` (string): Target deployment directory on server (/opt/hostaway-mcp)
- `SUPABASE_URL` (string): Supabase project URL
- `SUPABASE_SERVICE_KEY` (string): Supabase service role key
- `SUPABASE_ANON_KEY` (string): Supabase anonymous public key
- `HOSTAWAY_ACCOUNT_ID` (string): Hostaway API account ID
- `HOSTAWAY_SECRET_KEY` (string): Hostaway API secret key

**Validation Rules**:
- All secrets MUST be non-empty
- `SSH_PRIVATE_KEY` MUST start with `-----BEGIN OPENSSH PRIVATE KEY-----`
- `SSH_HOST` MUST be valid IP address or hostname
- `DEPLOY_PATH` MUST be absolute path starting with `/`
- URLs MUST use HTTPS protocol (except localhost)

**Relationships**: Used by GitHub Actions workflow to populate deployment environment

**State Transitions**: N/A (static configuration, updated manually via GitHub UI)

---

### 2. Workflow Run (GitHub Actions Execution)

**Purpose**: Track individual deployment execution state

**Attributes**:
- `run_id` (string): Unique identifier for workflow execution
- `status` (enum): Workflow execution status
  - `queued`: Waiting for runner availability
  - `in_progress`: Currently executing deployment steps
  - `completed`: Finished successfully
  - `failed`: Deployment or health check failed
  - `cancelled`: Manual cancellation
- `trigger_event` (string): Event that triggered workflow (push, workflow_dispatch)
- `commit_sha` (string): Git commit hash being deployed
- `started_at` (datetime): Workflow start timestamp
- `completed_at` (datetime): Workflow completion timestamp
- `duration` (integer): Total execution time in seconds
- `conclusion` (enum): Final outcome
  - `success`: Deployment succeeded
  - `failure`: Deployment failed
  - `cancelled`: User cancelled deployment

**Validation Rules**:
- `run_id` MUST be unique
- `commit_sha` MUST be valid Git SHA (40 hex characters)
- `duration` MUST be positive integer
- `completed_at` MUST be after `started_at`

**Relationships**: References Git commit and contains deployment logs

**State Transitions**:
```
queued → in_progress → completed (success/failure/cancelled)
                    ↓
                 cancelled (user action)
```

---

### 3. Deployment Backup (Server Filesystem)

**Purpose**: Preserve previous version for rollback on failure

**Attributes**:
- `backup_id` (string): Timestamp-based identifier (YYYYMMDD-HHMMSS)
- `backup_path` (string): Full filesystem path to backup directory
- `created_at` (datetime): Backup creation timestamp
- `source_commit` (string): Git commit SHA of backed-up version
- `size_bytes` (integer): Total backup size in bytes
- `contains_files` (array of strings): List of backed-up file paths

**Validation Rules**:
- `backup_id` MUST match format YYYYMMDD-HHMMSS
- `backup_path` MUST exist on filesystem
- `size_bytes` MUST be positive integer
- Maximum 5 backups retained (oldest deleted first)

**Relationships**: Created before deployment, restored on deployment failure

**State Transitions**:
```
created → active (current deployment) → archived (superseded by newer deployment)
       → restored (rollback triggered) → active
       → deleted (cleanup after retention limit)
```

---

### 4. Deployment Log (GitHub Actions Artifacts)

**Purpose**: Record all deployment activities for debugging and audit

**Attributes**:
- `log_id` (string): Unique identifier (workflow run ID + step name)
- `step_name` (string): Deployment step identifier
  - `checkout`: Git checkout
  - `deploy`: SSH deployment execution
  - `health_check`: Post-deployment verification
  - `rollback`: Failure recovery
- `output` (string): Console output from step execution
- `exit_code` (integer): Process exit code (0 = success, non-zero = failure)
- `timestamp` (datetime): Log entry timestamp
- `masked_secrets` (boolean): Whether secrets were masked in output

**Validation Rules**:
- `exit_code` MUST be integer (-128 to 127)
- `output` MUST NOT contain unmasked secret values
- `timestamp` MUST be valid ISO 8601 datetime
- Logs retained for 90 days minimum

**Relationships**: Belongs to Workflow Run, references deployment steps

**State Transitions**: N/A (append-only log)

---

### 5. Health Check Response (HTTP Endpoint)

**Purpose**: Verify successful deployment and application availability

**Attributes**:
- `status` (enum): Health status
  - `healthy`: Application responding correctly
  - `unhealthy`: Application error or timeout
  - `unreachable`: Server not accessible
- `http_status_code` (integer): HTTP response code (200, 500, etc.)
- `response_time_ms` (integer): Response latency in milliseconds
- `version` (string): Application version from health endpoint
- `uptime_seconds` (float): Application uptime
- `timestamp` (datetime): Health check execution time

**Validation Rules**:
- `http_status_code` MUST be valid HTTP code (100-599)
- `response_time_ms` MUST be positive integer
- Status is `healthy` only if `http_status_code` == 200
- `version` MUST match deployed commit SHA (first 7 characters)

**Relationships**: Created after deployment, triggers rollback if unhealthy

**State Transitions**:
```
pending → healthy (200 response) → deployment success
       → unhealthy (5xx response) → rollback triggered
       → unreachable (timeout/network error) → rollback triggered
```

---

## Workflow State Machine

The overall deployment follows this state machine:

```
[PR Merge to main]
       ↓
[Workflow Queued]
       ↓
[Runner Assigned] → [Checkout Code]
       ↓
[Create Backup]
       ↓
[SSH to Server] → [Transfer Code]
       ↓
[Build Docker Image]
       ↓
[Restart Container]
       ↓
[Health Check]
       ├─ Success → [Deployment Complete] → [Cleanup Old Backups]
       └─ Failure → [Rollback to Backup] → [Notify Failure]
```

## Data Retention

| Entity | Retention Period | Storage Location |
|--------|------------------|------------------|
| GitHub Secrets | Indefinite (until manually deleted) | GitHub encrypted storage |
| Workflow Runs | 90 days (GitHub default) | GitHub Actions logs |
| Deployment Backups | Last 5 backups only | Hostinger VPS filesystem |
| Deployment Logs | 90 days | GitHub Actions artifacts |
| Health Check Responses | 90 days (within workflow logs) | GitHub Actions logs |

## Security Considerations

**Sensitive Data**:
- All GitHub Secrets are encrypted at rest
- SSH private key never logged or displayed
- Environment variables masked in workflow outputs
- Health check responses do not contain sensitive data

**Access Control**:
- Only repository collaborators can trigger workflows
- Only admins can modify GitHub Secrets
- Deployment backups accessible only by root user on server
- Workflow logs visible to all repository collaborators

**Audit Trail**:
- All workflow executions logged with user attribution
- Deployment timestamps recorded for compliance
- Failed deployments trigger notifications
- Rollback events logged with reason and timestamp

## Non-Functional Characteristics

**Performance**:
- Workflow execution: <10 minutes end-to-end
- Backup creation: <30 seconds
- Health check: <10 seconds response time
- Rollback: <1 minute to restore previous version

**Reliability**:
- 95% deployment success rate target
- 100% rollback success on failure
- 99.9% uptime during deployments (no user-facing downtime)

**Scalability**:
- Single deployment target (no multi-environment support in scope)
- Concurrency control prevents race conditions
- Backup retention limit prevents disk space exhaustion
