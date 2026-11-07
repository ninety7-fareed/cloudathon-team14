# Runbook: knowledge base sync (data tier)

Demo runbook written for the Cloudathon proof of concept. Not a production runbook.

## Symptoms

- Guide chat answers "I couldn't find that in the product guides" for questions the guides do cover.
- Knowledge-base status is not ACTIVE, or the last ingestion job FAILED or never ran.

## Likely causes and next action

- **Documents uploaded but not ingested:** start an ingestion job for that data source only (product-guides or operations-runbooks). This does not redeploy the storefront.
- **Ingestion FAILED:** check the embedding model access (Titan Text Embeddings V2) in us-east-1 and the knowledge-base role in knowledge.yaml. Propose fixes through a CloudFormation update.
- **Wrong or outdated guide:** upload the corrected document to the guides bucket and re-ingest. Catalog data is not affected.
