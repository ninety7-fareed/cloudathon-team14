# Customer pain points

Problems AnyCompany has today. Address every pain point. Do not drop one because it is hard to show in a small proof of concept.

The proof of concept covers one application (`concept.md`). For pains that affect the whole fleet, show the repeatable mechanism that removes the pain, and state what the proof of concept itself proves.

## Licensing and exit

Virtualization licensing costs have risen sharply. AnyCompany must leave the current virtualization platform on an accelerated schedule.

## Team capacity

The team is too small to do these jobs by hand:

- discover application dependencies
- plan migration waves
- rebuild infrastructure

## Application shape

- Components are tightly coupled. A small change requires a rebuild and redeploy of the entire application.
- Scaling is still a manual process.
- The current infrastructure still contains single points of failure.

## Security operations

Operating-system updates and patching are slow. That delay has already caused security incidents.

## Customer experience

Customers in remote areas of the country report high latency. This folder does not name those areas or give latency numbers. Do not invent them. Design for an improvement and state the assumption you used.

## On-premises operations

Maintaining and patching on-premises servers has a high cost and a high operational overhead.

## Related files

- `core-requirements.md` — the outcomes required in response to these pains
- `concept.md` — proof-of-concept scope
- `situation.md` — timeline and team limits
