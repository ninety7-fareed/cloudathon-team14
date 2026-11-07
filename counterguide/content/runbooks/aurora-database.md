# Runbook: Aurora database (data tier)

Demo runbook written for the Cloudathon proof of concept. Not a production runbook.

## Symptoms

- Request-log rows with status 500, tier "data", and errors such as OperationalError, "connection timed out", "could not connect to server" or "too many connections".
- Database status shows the cluster or writer not "available", or reachableFromApplication = no.

## Likely causes and next action (a person ships it through CloudFormation)

- **Writer failing over or rebooting:** Aurora promotes the reader in the second Availability Zone automatically. Wait 1-2 minutes and recheck. No change needed if it recovers.
- **Capacity exhausted (CPU alarm counterguide-aurora-cpu in ALARM, or too many connections):** propose raising MaxAcu in counterguide-application (application.yaml parameter) through a CloudFormation stack update.
- **Security group change blocked port 5432:** propose restoring the AppToDb ingress rule in application.yaml through a stack update. Never open the database to the internet.
- **Secret rotated and tasks hold an old password:** propose a new ECS deployment through a CloudFormation update so tasks read the current secret.

Do not modify the database by hand in the console.
