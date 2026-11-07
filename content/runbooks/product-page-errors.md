# Runbook: product page is erroring (CounterGuide)

Demo runbook written for the Cloudathon proof of concept. Not a production runbook.

CounterGuide has three tiers: web (S3 + CloudFront), application (ECS Fargate behind the load balancer), data (Aurora PostgreSQL + two Bedrock knowledge bases). The product page is /products.html, which calls /api/products, which reads the products table in Aurora.

## Triage order

1. **Request log** (read_request_log). Look at recent rows for /api/products.
   - Status 500 with tier "data" and a database error (for example OperationalError, connection timed out, port 5432): the **data tier** is at fault. Go to the Aurora runbook.
   - Status 502/503/504 at CloudFront with no request-log rows: the request never reached the application. Go to step 2.
   - Rows marked simulated=true come from the demo control. Say that the errors are simulated.
2. **Load balancer target health** (read_load_balancer_target_health). If no targets are healthy, the **application tier** is at fault. Go to the ECS service runbook.
3. **ECS service status** (read_service_status). Running count below desired, or a deployment that is FAILED or rolling back: **application tier**.
4. **Database status** (read_database_status). Cluster or writer not "available", or not reachable from the application: **data tier**.
5. **CloudWatch alarms** (read_cloudwatch_alarms). Any counterguide-* alarm in ALARM confirms the tier above.

## Report format

Name exactly one tier (web, application or data), the evidence, and one next action. The next action is a proposal. A person ships it through CloudFormation. Do not change infrastructure.
