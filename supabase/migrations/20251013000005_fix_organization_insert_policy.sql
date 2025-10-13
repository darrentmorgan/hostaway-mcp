-- Migration: 20251013_005_fix_organization_insert_policy.sql
-- Purpose: Add INSERT policies to allow users to create their own organizations
-- Author: Claude Code
-- Date: 2025-10-13

-- Allow users to insert organizations where they are the owner
CREATE POLICY "Users create own organizations" ON organizations
  FOR INSERT
  WITH CHECK (owner_user_id = auth.uid());

-- Allow users to add themselves as organization members
CREATE POLICY "Users create own membership" ON organization_members
  FOR INSERT
  WITH CHECK (user_id = auth.uid());

-- Note: The existing policies handle SELECT/UPDATE/DELETE
-- These new policies specifically allow INSERT for initial organization setup
