# Core requirements

Every requirement below is mandatory. In the report, name the requirement each decision satisfies.

## 1. Resilience

Design a resilient architecture.

- Application layers scale independently of each other.
- The design has no single point of failure.
- In the report, identify each single point of failure you removed and the component that replaced it.

## 2. Lower operational overhead

Use managed, cloud-native services so the team stops doing this work by hand:

- routine operating-system patching
- manual scaling

Do not meet this requirement by keeping self-managed virtual machines as the primary design.

## 3. Repeatable deployment

Automate deployment so the same approach can be reused for the servers that are still on premises.

- Define the environment as infrastructure as code.
- Infrastructure as code is the source of truth. Do not build the proof of concept by creating resources by hand in the AWS console.
- The same team must be able to apply the pattern to a later application without designing it again from scratch.

## 4. Remote customers

Improve the experience of customers in remote areas of the country who currently see high latency.

- Name the design choice that improves their experience, such as edge delivery, regional placement, or caching.
- Tie any latency claim to that design choice. Do not claim an improvement the design does not implement.

## 5. Updates with minimal downtime

The architecture must accept application updates and deployments with minimal downtime, and it must scale.

- A change to one layer must ship without rebuilding and redeploying the whole application as one unit.
- Describe how that change ships without taking the whole application offline.

## 6. Cost of the full fleet

Show that the design is cost-efficient for the full set of servers still to be migrated, not only for the one proof-of-concept application.

- Name the main cost drivers.
- Name the controls that keep cost bounded as the pattern is repeated.
- Do not justify cost using only the proof-of-concept footprint.

## Related files

- `pain-points.md` — problems these requirements respond to
- `concept.md` — proof-of-concept scope
- `deliverables.md` — where each requirement must appear
