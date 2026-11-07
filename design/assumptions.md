# Assumptions

Each bullet is an assumption or a verified boundary this design relies on.
Verified facts are labeled as verified.
They are not guesses.
Starting numbers in the templates are labeled as starting settings.
They are not measurements.

- Verified fact, not a guess: the deploy account is Workshop Studio account `231075364174`, and the deploy role is `WSParticipantRole/Participant`.
  This was read from the Cloudathon@UH 2026 workshop page on 7 Nov 2026.
- Verified fact, not a guess: the deploy region is `us-east-1`.
  The workshop page says resources should be deployed in `us-east-1`.
  This was read on 7 Nov 2026.
- Verified fact, not a guess: `us-west-2` is only where the pre-provisioned code server already runs.
  The event allows that region for that existing server.
  CounterGuide is not deployed there.
- Verified fact, not a guess: leave instance `i-05d938f2fd93600b3`, named `vscodeserver-CodeServer`, and the `vscodeserver` stack untouched in `us-west-2`.
  CounterGuide resources are not placed in that VPC.
- Verified fact, not a guess: the local AWS CLI default profile is account `375760496131`, user `AdminFareed`.
  That profile is not the workshop account.
  These templates are not deployed with it.
- Assumption: Amazon Nova Pro is the default model for Guide chat and for Shiftlead.
  The workshop model-access section uses Amazon Nova Pro as the example model.
  The template default is the US inference profile `us.amazon.nova-pro-v1:0`.
  Model access is not confirmed enabled in account `231075364174`.
  The ID stays an assumption until that access is enabled.
- Assumption: knowledge-base embeddings use Amazon Titan Text Embeddings V2, model ID `amazon.titan-embed-text-v2:0`, at 1024 dimensions.
  Nova Pro is the chat and agent model.
  It is not the embedding model.
  Embedding access is not confirmed enabled in this account.
- Assumption: Amazon S3 Vectors is available in `us-east-1` for the two knowledge-base indexes.
  The workshop did not name S3 Vectors as blocked.
  Aurora, CloudFront, and CloudFormation were not named as blocked.
- Assumption: CloudFront edge locations are the mechanism that shortens the path for remote customers.
  No latency number was measured.
  The problem statement does not name the remote areas.
- Assumption: `PriceClass_100` still serves customers in the United States from CloudFront edge locations in that price class.
  This is a cost bound.
  It is not a measured latency result.
- Assumption: no custom domain is available for this proof of concept.
  The CloudFront default hostname is acceptable.
  Route 53 and the ACM certificate are created only when a domain name and a hosted zone ID are both supplied.
- Assumption: the CloudFront ACM certificate, when a domain exists, is created in `us-east-1`.
  That is the same region as the deploy region.
  AWS requires a CloudFront certificate to be in `us-east-1`.
- Assumption: CounterGuide stands in for one existing business-critical application.
  The briefs do not name the real application.
- Assumption: the catalog holds a handful of sample products, a few per category.
  It is not AnyCompany's real catalog.
- Assumption: the product guides and the operations runbooks are written for the demo.
  They are not official manuals, policies, or production runbooks.
- Assumption: the product knowledge base does not replace the catalog database.
- Locked behavior, recorded here so it is not treated as optional: Shiftlead's health tools are read-only.
  The agent returns a proposed action.
  A person ships changes through CloudFormation.
- Assumption: this proof of concept's network is dedicated.
  Sharing the VPC with a later application is a later decision.
- Assumption: the problem statement does not specify an identity provider, and this design does not add one.
- Assumption: this design does not assume an application inventory, a dependency map, or a virtual-machine count.
  Those details are absent from the problem statement.
- Estimate, not a quote and not a measurement in this account: a highly available managed stack is about $210–$228 per month in list price if left running.
  The estimate uses public list prices as of 7 Nov 2026.
- Starting settings, not measurements: Aurora capacity 0.5 to 4 ACUs, Fargate 0.5 vCPU and 1 GB per task, CPU target tracking at 50 percent, backup retention 1 day, log retention 14 days, and an Aurora CPU alarm at 90 percent.
  The templates expose these as parameters so a later deploy can change them without a new architecture.
