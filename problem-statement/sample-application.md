# Sample application

The proof of concept uses one named application: **CounterGuide**.

CounterGuide is a choice for this proof of concept. It is not a real AnyCompany system. AnyCompany's four product categories in `company-overview.md` are facts: electronics, cell phones, hobby equipment, and batteries. The application name, screens, sample products, and documents are assumptions.

## What it is

CounterGuide is the one three-tier business-critical sample application. Two AI capabilities live inside it: **Guide chat** and **Shiftlead**. They are not separate applications and not a fourth tier.

Do not add a fourth tier for either capability.

| Tier | Responsibility |
|---|---|
| Web | Two views of one application: the associate chat, and a platform view for Shiftlead. Call only the application tier. Hold no database password and no model credentials in the browser. |
| Application | The only tier that calls the data tier. It writes the request log. Guide chat retrieves from the product knowledge base and the catalog. Shiftlead calls health, the request log, and the operations knowledge base. |
| Data | Store the catalog and the request log in a relational database. Store product guides and operations runbooks in Amazon S3, each in its own Amazon Bedrock Knowledge Base. |

## Guide chat

Guide chat is the associate-facing chatbot.

- Use an Amazon Bedrock Knowledge Base for battery safety, device care, hobby-equipment setup, and the return window.
- The application tier also lets the chat read the catalog. A request such as "build a beginner RC kit" returns only real SKUs and refuses a combination the safety guide forbids.
- The web tier shows the answer and the documents used. It holds no database password and no model credentials.
- The application tier retrieves from the product knowledge base before it answers. If retrieval finds nothing, say so. Do not answer from the model's general knowledge.
- Keep the guide corpus short enough to ingest during a demo. Do not crawl the public web.

## Shiftlead

Shiftlead is the infrastructure agent for the platform team that runs this application.

- It is an Amazon Bedrock Agent.
- It answers a question such as "the product page is erroring" by reading this application's health, the request log, and the operations knowledge base (the runbooks). It names the tier at fault and the next action.
- It proposes the action. A person still ships the change through infrastructure as code. There is no automatic remediation and no account-wide troubleshooting.
- It troubleshoots the managed stack: the load balancer, the application service, the database, and knowledge-base sync. It does not SSH into virtual machines or patch them.
- The platform view shows that answer. It holds no database password and no model credentials.

## Change boundaries

- A guide update re-ingests the product knowledge base only. It does not redeploy the storefront.
- A runbook update re-ingests the operations knowledge base only. It does not redeploy the storefront.
- A catalog change ships through the application tier and the database. It does not re-ingest either knowledge base.

## Why this stands in for one business-critical application

- Product answers affect a sale. Battery guidance also affects safety, so the application matters to the business.
- A product-page failure stops that sale. Shiftlead names the tier at fault for this application.
- It is three tiers, so the proof of concept can show each tier scaling on its own, a removed single point of failure, and a repeatable deploy.
- The current templates in `templates/app.yaml` are a generic web page, an API call, and a visit counter across a web tier, an application tier, and a database. CounterGuide keeps that three-tier split. The associate chat and the platform view replace that page.
- Guide chat and Shiftlead stay inside CounterGuide. Neither becomes a second application or a fourth tier.

## What the proof of concept proves

- The platform team is small (`situation.md`, `pain-points.md`). Shiftlead is a repeatable way for that team to diagnose this application. Later applications reuse the same agent-and-runbook pattern.
- Remote customers are served by the web tier at the edge (`core-requirements.md`). Shiftlead stays internal.
- Cost stays bounded by scoping the agent to this one application and by reusing the runbook pattern (`core-requirements.md`).

## What a demo shows

The demo has three beats.

1. A cited battery answer. The associate asks which pack is safe and what the return window is. The associate chat shows the answer and the documents used.
2. A kit that refuses an unsafe part. The associate asks for a beginner RC kit. The answer returns real catalog SKUs and refuses loose AA cells when the safety guide forbids that combination.
3. Shiftlead names the tier that failed. Ask why the product page is erroring. The platform view names the tier at fault and the next action. It does not apply the change.

## Assumptions

- CounterGuide stands in for one existing business-critical application. The briefs do not name the real application.
- The catalog holds a handful of sample products, a few per category. It is not AnyCompany's real catalog.
- The product guides and the operations runbooks are written for the demo. They are not official manuals, policies, or production runbooks.
- Guide chat and Shiftlead are in scope. Both stay inside CounterGuide. Neither is a second system or a fourth tier. The product knowledge base does not replace the catalog database.
- The Bedrock model ID is not fixed here. Pick a model that is enabled in the deploy region and record the ID in the report. Treat that ID as an assumption.
- No latency number is claimed for remote customers. The design still has to name the edge choice in `core-requirements.md`.

## Out of scope for CounterGuide

- Checkout, payments, inventory as a full system, or a store locator.
- Training or fine-tuning a foundation model.
- Automatic remediation.
- Account-wide troubleshooting.
- A chatbot answer from general model knowledge when retrieval finds nothing. If retrieval finds nothing, say so.

## Related files

- `concept.md` — proof-of-concept scope
- `company-overview.md` — product categories this catalog uses
- `situation.md` — team limits this agent pattern is meant to fit
- `pain-points.md` — problems the working solution must address
- `core-requirements.md` — mandatory architecture outcomes
- `deliverables.md` — artifacts to produce
