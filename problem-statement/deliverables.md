# Deliverables

Produce all four deliverables. The response is incomplete if any one is missing. The diagram, the report, the deployment, and the presentation must describe the same design.

## 1. Architecture diagram

Create a diagram of the proposed solution.

- Use AWS Architecture Icons for every AWS service on the diagram.
- Author it in [diagrams.net](https://app.diagrams.net) (Draw.io) and save a `.drawio` file.
- Also export a PNG or SVG that can be reviewed without opening the editor.
- Draw only services the solution uses. The diagram must match the deployed proof of concept and the report.

## 2. Report

Write a report that justifies the architecture and the decisions behind it.

- Evaluate the design against the AWS Well-Architected Framework. Cover all six pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, and Sustainability.
- For each decision, cite the core requirement it satisfies (`core-requirements.md`) and the pain point it addresses (`pain-points.md`).
- Include a proposal summary of no more than three pages. The pillar-by-pillar evaluation comes after that summary and is not part of the three-page cap.
- Label assumptions as assumptions. Do not write an assumption as if it were a fact from this folder.

## 3. Working proof of concept

Deploy a functional proof of concept in the AWS environment provided for this work.

- Deploy it from the infrastructure-as-code definition. One-off console edits are not the source of truth.
- Run one simple sample application, modernized as described in `concept.md`.
- Document the commands or pipeline steps a reviewer needs in order to deploy it and to confirm the application works.

## 4. Presentation

Prepare a presentation of the solution for AWS reviewers and industry judges.

- Base it on the diagram, the report, and the running proof of concept.
- Cover the decision, the architecture, how the pain points are addressed, cost at fleet scale, and what the live demo shows.
- Present one design only. Do not introduce a second architecture in the slides.

## Done when

- All four artifacts exist.
- All four artifacts agree with each other.
- Every requirement in `core-requirements.md` is visible in at least one artifact.
- The proof of concept is deployed, and the documented steps show how to verify it.

## Related files

- `concept.md` — scope of the proof of concept
- `core-requirements.md` — mandatory outcomes
- `pain-points.md` — problems the solution must address
- `situation.md` — timeline and team limits
- `company-overview.md` — who AnyCompany is
