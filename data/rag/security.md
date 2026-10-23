# Atlas project security

Atlas authenticates users with the university identity provider using
OpenID Connect. API access is authorized with project-level roles. The
service must never log access tokens, passwords, or complete request bodies.

Secrets are stored in the deployment platform's secret manager and are
provided to the application as environment variables. They must not be
committed to the repository or placed in a local `.env` file that is shared
with the team.

Security-sensitive changes require review from a member of the security
rotation. Dependencies are scanned weekly, and a critical dependency
vulnerability blocks a release until it is patched or explicitly accepted by
the security owner.
