# SOP-IT-001: Oracle Database Backup Procedure
Version: 3.2 | Effective: 01-Mar-2026 | Owner: IT Infrastructure

## Purpose
Defines the standard procedure for nightly RMAN backups of production Oracle databases.

## Schedule
- Full RMAN backup: every Sunday 02:00 GST
- Incremental Level 1: Monday-Saturday 02:00 GST
- Archive log backup: every 4 hours
- Retention: 35 days on disk, 12 months on tape

## Procedure
1. Verify FRA (Fast Recovery Area) usage is below 80% before backup window.
2. RMAN executes via scheduled job DBBKP_PROD on the backup server.
3. On completion, the job emails status to dba-team@example.com.
4. Failed backups must be re-run within 6 hours and logged in the ITSM tool as a P3 incident.

## Escalation
Two consecutive failures escalate to the DBA on-call manager.
