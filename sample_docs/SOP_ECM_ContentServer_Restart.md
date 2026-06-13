# SOP-IT-009: ECM Content Server and Method Server Restart Procedure
Version: 1.4 | Effective: 20-May-2026 | Owner: ECM Operations

## When to Use
Method Server high CPU, hung sessions, or post-patching restarts.

## Restart Order
1. Stop the ECM web application (Tomcat) on app servers.
2. Stop the Java Method Server (JMS).
3. Stop the Content Server (repository service).
4. Verify no server processes remain.
5. Start the Content Server, wait for the repository to accept connections (check the repository log).
6. Start the Method Server, verify ServerApps deployment in the JMS log.
7. Start the web application (Tomcat), validate login and search.

## Validation
Run a test checkin/checkout in the web client and confirm full-text search returns results before closing the change.
