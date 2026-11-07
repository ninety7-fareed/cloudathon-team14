# Architectural assessment

This assessment reviews the locked CounterGuide design. It does not change the CloudFormation templates and it does not add a feature.

Five reviews read the same briefs and templates: infrastructure, application, security, data, and delivery. They agree on the current shape. Conflicts below are wording or leftover files, not competing designs.

## Findings from the project documents

Documented facts:

- AnyCompany runs IT in third-party colocation on an on-premises virtualization platform. The data-center lease ends in Q4 2027. Virtualization licensing renews at several times the previous cost. The platform team is small and cannot hand-migrate hundreds of virtual machines.
- The briefs name no application inventory, dependency map, virtual-machine count, database engine, or identity system.
- This proof of concept is one application, CounterGuide, in three tiers. Guide chat and Shiftlead stay inside it.
- The locked target is Workshop Studio account `231075364174`, role `WSParticipantRole/Participant`, region `us-east-1`. The local CLI profile is account `375760496131`, user `AdminFareed`, and is not the target. Instance `i-05d938f2fd93600b3` in `us-west-2` is the workshop code server and stays untouched.
- The source of truth is `design/cloudformation/`: network, repository, knowledge, application, and web. `templates/network.yaml` and `templates/app.yaml` are an older EC2 and MySQL pattern. They are not deployed for CounterGuide.
- The web tier is a private S3 bucket behind CloudFront and WAF. `/api/*` is not cached and forwards to the load balancer. The application tier is one Fargate service. The data tier is Aurora PostgreSQL Serverless v2 (writer and reader) plus two Bedrock Knowledge Bases. Shiftlead is read-only and proposes an action a person ships with CloudFormation.
- These stacks have not been deployed. The diagram, the Well-Architected report, the presentation, and the reviewer command list in `deliverables.md` are not in the repo yet.

## Assumptions about legacy infrastructure

These are not in the briefs. They are not facts.

- The colocation estate includes Active Directory, Group Policy, file servers, DNS, DHCP, or a VPN.
- The virtualization platform is a named product such as VMware or Hyper-V.
- The unnamed business application uses a known database engine. MySQL in `templates/app.yaml` is the old workshop pattern, not evidence of the on-premises engine.
- This proof of concept must reach systems that remain on premises.
- “Shiftlead stays internal” means a private network. The reviews treat it as the platform-team audience and a read-only feature boundary. Both views share the public CloudFront hostname. No identity provider is specified.

## Migration challenges and dependencies

This proof of concept deploys a sample application. It does not cut over a live colocation workload. The catalog, guides, and runbooks are written for the demo.

Dependencies that do matter:

- Deploy only as the participant role in `231075364174` / `us-east-1`, and only when a deploy is authorized. The templates reject another account or region. They do not check the role name.
- Stack order: network, repository, and knowledge can be created first. Push the container image. Then create the application stack. Then create the web stack. Leave `templates/` undeployed.
- Fargate has no public IP. Image pull, Secrets Manager, Bedrock, and CloudWatch use the NAT gateway in that task’s Availability Zone. S3 object traffic uses the gateway endpoint. Data subnets have no internet route.
- Nova Pro (`us.amazon.nova-pro-v1:0`) and Titan Text Embeddings V2 are assumptions until model access is enabled. The Nova Pro ID is a US inference profile, so inference can run in another US region even though the stacks exist only in `us-east-1`.
- The catalog and request-log schema is not in the repo. The application tier is expected to create those tables. Do not treat the old MySQL `visits` table as the schema.
- Physical names are fixed to CounterGuide (`counterguide-task`, secret `counterguide/origin-verify`, and similar). A second copy in this account needs new names. Export names follow the stack name. Physical names do not.
- Aurora deletion protection is off, backup retention defaults to one day, and stack delete removes the cluster.

## How the reviews resolved conflicts

| Topic | Resolution |
|---|---|
| Who the browser calls | The browser calls CloudFront only. `/api/*` reaches the load balancer. The web tier holds no database password and no model credentials. |
| Shiftlead “stays internal” | Keep one public distribution. Do not add Entra ID, Active Directory, a VPN, or a private path in this proof of concept. |
| Where the data tier lives | One data tier. Aurora is in the application stack. The two knowledge bases are in the knowledge stack. Stacks are deploy units. A catalog write does not re-ingest. A re-ingest does not redeploy the storefront. |
| Database engine | Aurora PostgreSQL only. Do not keep the old RDS MySQL template beside it. |
| Empty retrieval | The container must say so and must not call the model when retrieval returns nothing. IAM does not enforce that rule. |
| No single point of failure | Report what this design removes relative to the old templates: one shared NAT, a single-AZ database default, an EC2 instance as the tier, and one redeploy of the whole application. What remains is one Aurora writer, one load balancer in two subnets, and per-zone NAT. Do not add a second region for this proof of concept. |
| Remote customers | CloudFront `PriceClass_100` is the edge choice for the static views and the single hostname. `/api/*` is uncached and ends in `us-east-1`. Do not claim a latency number. |
| Deliverables versus the repo | The five templates and the design notes are the architecture. They are not the diagram, the report, the presentation, or a running deployment. |

## Scalability and future integrations

The pattern that can be repeated is one application service, one database schema, and two knowledge bases on this VPC. A later application does not get its own NAT pair unless a later decision gives it another VPC.

Guide chat and Shiftlead share one Fargate service, so they deploy and scale together. A rolling deploy keeps at least one healthy task. The web and application contract is the `/api/*` prefix. That body has to stay compatible while old and new tasks overlap.

Leave these for a later phase. Do not build them now.

- Hybrid connectivity, a private on-premises link, and workforce sign-in such as Microsoft Entra ID.
- Interface endpoints for Bedrock, ECR, Secrets Manager, and CloudWatch.
- A deployment pipeline, multi-account promotion, and drift detection.
- Longer Aurora retention, deletion protection, a second database user that can only read the request log, and separate knowledge-base roles.
- A second application, more channels, or more agents.

## Immediate notes, still inside this scope

These do not add a product. They are not implemented by this assessment.

- Say the edge path and the uncached API path the way the infrastructure review states them. Do not claim a shorter model round trip.
- Enforce the empty-retrieval refusal in the application container when that container is written.
- When a deploy is authorized, use only `design/cloudformation/`, in the order above, from the participant role. Publish the front end as objects. Re-ingest guides and runbooks as separate person-run steps.
- Still owed by `deliverables.md`: a diagrams.net diagram, a Well-Architected report, a presentation, reviewer commands, and a running proof of concept. Those describe this design. They do not change it.

## Related files

- `architecture.md` — locked design
- `assumptions.md` — verified boundaries and assumptions
- `requirements-trace.md` — requirements and pain points mapped to components
- `application-idea.md` — what CounterGuide is
- `../problem-statement/sample-application.md` — source of truth for behavior
- `../problem-statement/deliverables.md` — artifacts still to produce
