# Application idea

## Working title

The application is **CounterGuide**.

The name, the screens, the sample products, and the documents are assumptions. AnyCompany's four product categories are facts: electronics, cell phones, hobby equipment, and batteries.

## The problem it stands in for

CounterGuide stands in for one business-critical retail application. The briefs do not name the real application.

The platform team is small. AnyCompany is moving off its on-premises virtualization platform. This proof of concept modernizes that one application. It does not migrate the rest of the estate.

## The idea

CounterGuide is one three-tier application. Two AI capabilities live inside it: **Guide chat** and **Shiftlead**. They are not two products and not a fourth tier.

## Guide chat

Guide chat is the associate-facing chatbot.

An Amazon Bedrock Knowledge Base holds battery safety, device care, hobby setup, and returns. Guide chat can also read the catalog, so a beginner RC kit returns only real SKUs and refuses a combination the safety guide forbids. The browser shows the answer and the documents used. If retrieval finds nothing, the chat says so.

## Shiftlead

Shiftlead is an Amazon Bedrock Agent for the platform team that runs this application.

It reads this application's health, the request log, and a runbook knowledge base. It names the tier at fault and proposes the next action. A person ships the change with CloudFormation. There is no automatic remediation and no account-wide troubleshooting.

## The three tiers

- **Web.** Two views of one application: the associate chat, and a platform view for Shiftlead. The browser calls only the application tier.
- **Application.** The only tier that calls data. It writes the request log. Both capabilities go through this tier.
- **Data.** The catalog database, the request log, and two knowledge bases: product guides and operations runbooks.

## The three-beat demo

1. A cited battery answer. The associate asks which pack is safe and what the return window is. The chat shows the answer and the documents used.
2. A kit that refuses loose AA cells. The associate asks for a beginner RC kit. The answer returns real catalog SKUs and refuses loose AA cells when the safety guide forbids that combination.
3. Shiftlead names the failed tier. Ask why the product page is erroring. The platform view names the tier at fault and the next action. It does not apply the change.

## What we are not building

- Checkout, payments, full inventory, or a store locator.
- Model training.
- Automatic remediation.
- A second application.

`sample-application.md` is the detailed source of truth for this idea.
