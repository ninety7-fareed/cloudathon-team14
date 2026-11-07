# Runbook: ECS service and load balancer (application tier)

Demo runbook written for the Cloudathon proof of concept. Not a production runbook.

## Symptoms

- Load balancer targets unhealthy or draining; alarm counterguide-unhealthy-targets or counterguide-healthy-targets-low in ALARM.
- ECS running count below desired (alarm counterguide-running-tasks-low), or a deployment FAILED / rolled back by the circuit breaker.
- CloudFront returns 502/503/504 and the request log has no new rows.

## Likely causes and next action (a person ships it through CloudFormation)

- **Bad image or crash on start (deployment rolled back):** propose redeploying the last good ImageTag in counterguide-application.
- **Health check failing on /health:** check the container listens on port 8080 and /health returns 200. Propose a fixed image and a stack update.
- **Not enough tasks under load (CPU high):** propose raising MaxTaskCount or lowering TargetCpu in application.yaml.
- **Tasks cannot reach AWS APIs (Bedrock, ECR, Secrets Manager):** check the NAT gateway route in that Availability Zone (network.yaml).

Rolling deployments keep at least 100 percent healthy tasks, so a bad release should roll back without an outage.
