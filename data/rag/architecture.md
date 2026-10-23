# Atlas project architecture

Atlas is a small service that imports software-project events and exposes a
read-only reporting API. The service is split into an API process and a
background worker. The API process validates requests and reads from the
database; the worker processes imports asynchronously.

The production deployment uses PostgreSQL 16. Local development may use
SQLite, but SQLite is not supported for the production deployment. Import
jobs are placed on a Redis-backed queue. The API is stateless, so multiple API
instances can run behind a load balancer.

The repository is organized as `src/atlas/api`, `src/atlas/worker`, and
`tests/`. The API and worker share domain types from `src/atlas/domain`.
