# Key Rotation Plan
**Date**: October 15, 2025
**Feature**: 005-project-brownfield-hardening

## Summary

Due to potential exposure of credentials in git history, we need to rotate all sensitive credentials.

## Rotation Steps

### 1. Supabase Service Role Key

**Current Status**: ⚠️ EXPOSED in git history
**Impact**: HIGH - Full database access

1. Access Supabase Dashboard > Project Settings > API
2. Click "Reset service key" button
3. Copy new key and update in:
   - Production .env
   - Staging .env
   - All development environments

**Fallback Plan**: If issues occur, old key can be temporarily restored through Supabase Dashboard

### 2. Supabase Anonymous Key

**Current Status**: ⚠️ EXPOSED in git history
**Impact**: MEDIUM - Public API access

1. Access Supabase Dashboard > Project Settings > API
2. Click "Reset anon/public key" button
3. Update key in:
   - Production .env
   - Staging .env
   - All development environments
   - Frontend application configurations

**Note**: Frontend applications will need redeployment with new key.

### 3. Stripe Test Keys

**Current Status**: ⚠️ EXPOSED in git history
**Impact**: LOW - Test environment only

1. Access Stripe Dashboard > Developers > API keys
2. Create new test key pair
3. Archive old test keys
4. Update keys in development and staging environments
5. Update webhook secret if needed

**Note**: No production impact since these are test keys.

### 4. Hostaway API Credentials

**Current Status**: ⚠️ EXPOSED in git history
**Impact**: HIGH - Channel manager access

1. Access Hostaway Dashboard > API Credentials
2. Generate new API key pair
3. Update credentials in:
   - Production .env
   - Staging .env
   - Development environments

**Note**: Brief service interruption expected during key rotation.

## Implementation Order

1. **Staging First**
   - Rotate all keys in staging
   - Verify all functionality
   - Monitor for 24 hours

2. **Production Second**
   - Schedule maintenance window
   - Rotate keys one at a time
   - Verify after each rotation
   - Have rollback plan ready

3. **Development Last**
   - Update all development environments
   - Update documentation
   - Update CI/CD configurations

## Required Service Outage

Expect 5-10 minutes downtime during production key rotation.

## Communication Plan

1. **Before Rotation**
   - Notify all developers
   - Post in #operations Slack channel
   - Update status page
   - Email affected customers

2. **During Rotation**
   - Live updates in #operations
   - Status page updates
   - Monitor support channels

3. **After Rotation**
   - Confirm success in #operations
   - Update status page
   - Send all-clear email

## Prevention Plan

1. **Git Security**
   - Add pre-commit hooks for secret detection
   - Configure GitHub secret scanning
   - Regular security audits

2. **Documentation**
   - Update security guidelines
   - Add key rotation procedures
   - Improve .env.example

3. **Monitoring**
   - Add key expiration monitoring
   - Set up secret scanning alerts
   - Regular security reports

## Additional Actions

1. **Clean Git History**
   - Use BFG Repo-Cleaner to remove secrets
   - Force push after cleanup
   - All developers must re-clone

2. **Security Improvements**
   - Move to secret manager service
   - Implement key rotation schedule
   - Add automated secret detection

## Sign-Off Required

- [ ] Security Team
- [ ] Operations Team
- [ ] Development Team Lead
- [ ] Product Owner

---

**Note**: All keys must be treated as compromised until rotated. Monitor for any unauthorized access attempts.
