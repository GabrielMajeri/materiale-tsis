# Atlas project operations

Deployments are performed by the release engineer after the CI pipeline is
green. A deployment must have a rollback plan and a link to the release
notes. Database migrations run before the new application version receives
traffic.

The service emits structured JSON logs. Every request log includes a
`request_id`; import jobs also include an `import_id`. Production alerts are
based on error rate, queue depth, and the age of the oldest queued import.

The on-call engineer acknowledges a production alert within 15 minutes. If
the error rate remains above 5 percent for 10 minutes, the on-call engineer
rolls back the application unless the incident commander chooses another
documented mitigation.
