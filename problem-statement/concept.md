# Proof of concept

Scope of the build. Stay inside this scope.

## Goal

Migrate and modernize one representative business-critical application into a resilient, cloud-native architecture.

Show that a small team can use automation to speed up both the migration and the modernization.

## Sample application

The sample application is **CounterGuide**, defined in `sample-application.md`.

- Use that file as the source of truth for the application name, the tiers, Guide chat, Shiftlead, the demo, and the assumptions.
- CounterGuide is one three-tier application: web, application, and data.
- The data tier holds the catalog and the request log in a relational database. It also holds two Amazon Bedrock Knowledge Bases. One stores product guides. The other stores operations runbooks.
- Guide chat and Shiftlead are in scope. Both live inside CounterGuide. Do not make either a fourth tier or a second application.
- Do not recreate AnyCompany's full set of retail systems.

## In scope

- One application.
- A cloud-native design, not a copy of the current virtual-machine layout.
- Automation that the same small platform team could run again for later servers.
- A working deployment, not a proposal that exists only as a diagram.

## Out of scope

- Migrating hundreds of virtual machines in this proof of concept.
- A multi-year program plan in place of a working deployment.
- Rebuilding every AnyCompany product or store system.

## Related files

- `core-requirements.md` — required properties of the architecture
- `deliverables.md` — artifacts to produce
- `situation.md` — timeline and team limits
- `sample-application.md` — source of truth for CounterGuide, Guide chat, and Shiftlead
- `pain-points.md` — problems the working solution must address
