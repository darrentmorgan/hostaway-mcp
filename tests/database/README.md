# Database Tests

This directory contains SQL-based tests for database functionality, including RLS policies and database functions.

## Prerequisites

- Supabase CLI installed (`brew install supabase/tap/supabase`)
- Local Supabase instance running (`supabase start`)
- pgTAP extension installed (included in Supabase by default)

## Running Tests

### Run All Database Tests

```bash
# From project root
supabase test db
```

### Run Specific Test File

```bash
# Test RLS policies
psql ***REMOVED*** < tests/database/test_rls_policies.sql

# Or with Supabase CLI
supabase db test --file tests/database/test_rls_policies.sql
```

### Run Tests Against Remote Supabase

```bash
# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Run tests
supabase test db --db-url YOUR_DATABASE_URL
```

## Test Files

### test_rls_policies.sql

**Purpose**: Verify Row-Level Security policies enforce multi-tenant isolation

**Test Coverage** (28 tests):

1. **organizations table** (3 tests)
   - User can only see their own organization
   - User cannot see other organizations
   - Cross-org access blocked

2. **organization_members table** (5 tests)
   - Users see own memberships
   - Owners see all org members
   - Members only see own membership
   - Cross-org membership access blocked

3. **hostaway_credentials table** (4 tests)
   - Users see own org credentials
   - Cross-org credential access blocked
   - Members can read credentials

4. **api_keys table** (4 tests)
   - Users see own org API keys
   - Cross-org API key access blocked
   - Members can manage API keys

5. **subscriptions table** (3 tests)
   - Users see own org subscription
   - Cross-org subscription access blocked

6. **usage_metrics table** (3 tests)
   - Users see own org usage metrics
   - Cross-org metrics access blocked

7. **audit_logs table** (4 tests)
   - Users see own org audit logs
   - Cross-org audit log access blocked
   - Members can read audit logs

8. **Multi-user scenarios** (2 tests)
   - Owner and member access patterns
   - Organization isolation verification

**Key Scenarios Tested**:
- ✅ User A cannot access User B's organization data
- ✅ Organization members can only see their org's data
- ✅ Owners have full access to their org
- ✅ Regular members have read access to their org
- ✅ RLS policies enforce organization_id scoping via organization_members join

### test_functions.sql (Coming Soon)

**Purpose**: Test database functions and triggers

**Test Coverage**:
- increment_usage_metrics RPC function
- check_api_key_limit trigger (enforces max 5 keys)
- Concurrent update handling
- Error conditions

## Test Output

Tests use pgTAP framework and output TAP format:

```
ok 1 - User 1 can only see Organization A
ok 2 - User 2 can only see Organization B
ok 3 - User 1 cannot see Organization B
...
1..28
```

## Interpreting Results

- **ok N - description**: Test passed ✅
- **not ok N - description**: Test failed ❌
- **# skip**: Test was skipped
- **# todo**: Test is planned but not yet implemented

## Debugging Failed Tests

If tests fail:

1. Check RLS policies are enabled:
   ```sql
   SELECT tablename, rowsecurity
   FROM pg_tables
   WHERE schemaname = 'public';
   ```

2. Verify test data was created:
   ```sql
   SELECT * FROM organizations;
   SELECT * FROM organization_members;
   ```

3. Check auth context:
   ```sql
   SELECT auth.uid();
   SELECT current_setting('request.jwt.claims', true);
   ```

4. Manually test policy:
   ```sql
   SET LOCAL ROLE authenticated;
   SET LOCAL "request.jwt.claims" TO '{"sub": "user-id-here"}';
   SELECT * FROM organizations; -- Should only show user's org
   ```

## Adding New Tests

1. Create new `.sql` file in `tests/database/`
2. Follow pgTAP conventions:
   ```sql
   BEGIN;
   SELECT plan(N); -- N = number of tests

   -- Your tests here
   SELECT is(actual, expected, 'test description');

   SELECT * FROM finish();
   ROLLBACK;
   ```

3. Add to CI/CD pipeline in `.github/workflows/test.yml`

## CI/CD Integration

Database tests run automatically on PR creation:

```yaml
- name: Run database tests
  run: |
    supabase start
    supabase test db
```

## References

- [pgTAP Documentation](https://pgtap.org/)
- [Supabase Testing Guide](https://supabase.com/docs/guides/cli/testing)
- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
