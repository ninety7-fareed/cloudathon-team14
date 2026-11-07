# Situation

Facts that set the timeline and the operating model. Treat every statement in this file as given.

## Deadlines

Two deadlines overlap:

1. AnyCompany's data-center lease expires in Q4 2027.
2. The license for the on-premises virtualization platform renews at several times its previous cost.

Leadership has made both of these decisions:

- Leave the on-premises virtualization platform completely. Do not plan on renewing that license or absorbing the price increase.
- Use the exit to modernize. Do not reproduce the current operating model unchanged in the cloud.

## Team limits

The platform team is small.

- The team cannot migrate hundreds of virtual machines by hand.
- The team cannot staff a multi-year modernization program.
- The team must move quickly and must lower operational overhead.
- Automation and managed services must perform the work this team does not have the headcount to do manually.

## What the solution must assume

Design for that small team:

- Prefer managed, cloud-native services over self-managed servers.
- Prefer automation over work done by hand in the console.
- The proof of concept is a pattern the same team can repeat for the servers that remain. It is not a one-time build.

## Related files

- `company-overview.md` — who AnyCompany is
- `pain-points.md` — current problems
- `concept.md` — what to build now
- `core-requirements.md` — mandatory outcomes
- `deliverables.md` — artifacts to produce
