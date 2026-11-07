# Requirements trace

This file maps the locked CounterGuide design in `architecture.md` to the mandatory outcomes and the pain points.
The design is one three-tier application.
Guide chat and Shiftlead stay inside it.
Deploy region `us-east-1` and account `231075364174` were verified from the Cloudathon@UH 2026 workshop page on 7 Nov 2026.

## 1. Resilience

Application layers scale independently.
CloudFront and S3 serve the web tier.
The Fargate service scales by target tracking.
Aurora Serverless v2 scales in ACUs.
A scale-out of tasks does not add a NAT gateway and does not replace the front end.

Single points of failure this design removes:

- Single NAT gateway.
  `templates/network.yaml` creates one NAT gateway, and both private route tables use it.
  `design/cloudformation/network.yaml` creates two NAT gateways, one in each Availability Zone.
  Each Fargate route table uses the NAT gateway in its own zone.
- Single-AZ database.
  `templates/app.yaml` sets `MultiAZDatabase` default `false` on one RDS MySQL instance.
  `design/cloudformation/application.yaml` creates an Aurora PostgreSQL Serverless v2 writer in the first Availability Zone and a reader in the second.
- One EC2 instance serving a tier.
  The current template already sets Auto Scaling minimum size to 2, and it still serves each tier from EC2 instances.
  The web tier is now S3 and CloudFront, which removes the instance.
  The application tier is the ECS Fargate service `counterguide` with at least two tasks and availability zone rebalancing.
  The load balancer keeps sending traffic to the remaining healthy task if one task fails.
- Tightly coupled redeploy.
  `templates/app.yaml` bakes the page and the API into instance user data in one stack.
  The locked change boundaries are separate.
  `web.yaml` publishes the storefront.
  The Fargate service rolls out an application change at minimum healthy percent 100.
  A catalog change is a write to Aurora through the application tier.
  `knowledge.yaml` re-ingests one knowledge base at a time.

The load balancer spans both public subnets, so one subnet does not own the entry to the application tier.

## 2. Lower operational overhead

The primary compute is ECS Fargate.
The template creates no EC2 instance, no AMI, and no user-data package install.
The routine operating model does not patch a guest operating system.
Aurora Serverless v2 is the database, with capacity bounded by minimum and maximum ACUs.
Target tracking on `ECSServiceAverageCPUUtilization` replaces manual scaling of the application tier.
S3 and CloudFront replace the web Auto Scaling group, so there is no web server fleet to patch.
Shiftlead reads health and proposes an action.
It does not SSH, and it does not patch a virtual machine.

## 3. Repeatable deployment

AWS CloudFormation is the source of truth.
The templates are `design/cloudformation/network.yaml`, `repository.yaml`, `knowledge.yaml`, `application.yaml`, and `web.yaml`.
Resources are not created by hand in the console as the source of truth.
The network stack deploys before the application stack.
The knowledge stack deploys before the application stack and does not contain the web tier.
The repeatable unit for a later application is the application service, the database schema, and two knowledge bases.
This proof of concept keeps a dedicated VPC.
A later application does not get a second NAT pair unless a later decision gives it a separate VPC.
The same team applies the pattern by deploying those templates again, with new names, rather than designing the three tiers again.

## 4. Remote customers

The edge choice is CloudFront in front of the static associate chat.
Assumption: CloudFront edge locations are the mechanism.
No latency number is claimed.
The distribution price class is `PriceClass_100`.
Assumption: United States edge locations in that price class still serve customers in remote areas of the country.
WAF is attached for filtering.
It is not the latency mechanism.
Shiftlead is the platform view for the team.
It is not the remote-customer path.
The API path `/api/*` is also on the same distribution, so the browser talks to CloudFront rather than to a regional load balancer name.

## 5. Updates with minimal downtime

A front-end change is an object write to the web bucket.
Fargate tasks keep serving.
An application change is an ECS rolling deployment.
`MinimumHealthyPercent` is 100 and `MaximumPercent` is 200.
The load balancer drains a task only after a replacement task is healthy.
Aurora and CloudFront stay up during that rollout.
A guide re-ingest runs against the product knowledge base in `knowledge.yaml`.
It does not replace the storefront.
A runbook re-ingest runs against the operations knowledge base only.
A catalog change ships through the application tier and Aurora only.
The service scales by target tracking without a redeploy of the web tier or a change to the NAT gateways.

## 6. Cost of the full fleet

The main cost drivers are two NAT gateways, public IPv4 addresses, the load balancer, Aurora minimum ACUs, Fargate, and two knowledge bases.
The control for the fleet is the repeatable unit: one application service, one database schema, and two knowledge bases.
The NAT pair belongs to the network stack.
This proof of concept does not create a second NAT pair for CounterGuide's web tier, and a later application does not get its own NAT pair unless a later decision creates another VPC.
S3 Vectors keeps each knowledge base off a dedicated OpenSearch Serverless collection.
Estimate, not a quote and not a measurement in this account: about $210–$228 per month in public list price as of 7 Nov 2026 if a highly available managed stack is left running.
That estimate is for the shape of the stack, not a bill from account `231075364174`.

## Pain points

### Licensing and exit

The application tier runs on Fargate and the database runs on Aurora Serverless v2.
The web tier runs on S3 and CloudFront.
The proof of concept leaves the on-premises virtualization platform for this one application.
It does not migrate the rest of the fleet in this design.
The same CloudFormation pattern is what a later server uses instead of a new virtual machine.

### Team capacity

The platform team defines the environment in the five templates.
The team does not rebuild the three tiers by hand for the next application.
Shiftlead plus the operations runbooks is the repeatable way to diagnose this application.
The agent is scoped to CounterGuide.
Dependency discovery and migration-wave planning for hundreds of virtual machines stay out of this proof of concept.
The mechanism this proof of concept shows is the application pattern and the agent-and-runbook pattern.

### Application shape

Tight coupling is removed by the change boundaries in `architecture.md`.
`web.yaml`, the Fargate service, Aurora, and `knowledge.yaml` ship separately.
Manual scaling is removed by Fargate target tracking and by Aurora Serverless v2 capacity.
The single points of failure named in requirement 1 are removed by two NAT gateways, the Aurora writer and reader, S3 plus CloudFront, the two-task Fargate service, and the separate deploy paths.

### Security operations

Fargate removes routine guest OS patching from the operating model.
The Amazon Linux launch templates and user-data installs in `templates/app.yaml` are the pattern this replaces.
The task role denies ECS service updates, load balancer changes, RDS changes, CloudFormation, IAM, and SSM sessions.
Shiftlead cannot apply a patch.
A person ships the change in CloudFormation.

### Customer experience

CloudFront is the edge delivery path for the associate chat.
Assumption: edge locations are the mechanism.
No latency number and no remote-area name are invented.
The API for that chat is on the same distribution.

### On-premises operations

Fargate, Aurora Serverless v2, S3, CloudFront, and Bedrock carry host maintenance, capacity changes, and request serving for this application.
The proof of concept shows that operating model once.
The templates are what the same small team runs for a later application.

## Related files

- `architecture.md` — locked design and template names
- `assumptions.md` — verified account and region, and the remaining assumptions
- `../problem-statement/core-requirements.md` — the six requirements
- `../problem-statement/pain-points.md` — the pains mapped above
- `../templates/network.yaml` — single NAT pattern this design replaces
- `../templates/app.yaml` — EC2 and single-AZ database default this design replaces
