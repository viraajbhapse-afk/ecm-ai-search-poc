# SOP-IT-002: RHEL Server Patch Management
Version: 2.1 | Effective: 15-Jan-2026 | Owner: IT Infrastructure

## Purpose
Standard process for applying Red Hat security advisories (RHSA) to RHEL 9 servers.

## Patch Cycle
- Critical CVEs (CVSS >= 9.0): patch within 7 days
- High (CVSS 7.0-8.9): within 30 days
- Medium/Low: quarterly patch window

## Process
1. Review RHSA advisories every Monday.
2. Raise a Change Request (CR) and obtain CAB approval for production servers.
3. Patch DEV -> UAT -> PROD with minimum 3 business days soak time per environment.
4. Reboot windows: Friday 22:00-02:00 GST only.
5. Post-patch validation: services up, application smoke test, kernel version verified.
