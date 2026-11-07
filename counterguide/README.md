# CounterGuide: application code, web pages, demo content

**Live site:** [https://d6v32wosjtbse.cloudfront.net](https://d6v32wosjtbse.cloudfront.net) (Guide chat, home page). Shiftlead: [https://d6v32wosjtbse.cloudfront.net/platform.html](https://d6v32wosjtbse.cloudfront.net/platform.html).

Deploy and verify steps below.

Everything is deployed from the CloudFormation templates in `design/cloudformation/`. No console-built resources.
Run every command from the repository root. Run these in **AWS CloudShell in us-east-1** (signed in through Workshop Studio), or in the team code server with the workshop credentials. Region must be **us-east-1**.

## What's in this repo

| Folder | What it is |
|---|---|
| `design/cloudformation/` | The five stacks (Fareed) |
| `counterguide/app/` | Application tier container: Flask API on port 8080 (`/health`, `/api/chat`, `/api/products`, `/api/shiftlead`) |
| `counterguide/web/` | Static pages for S3 + CloudFront: `index.html` (Guide chat), `products.html` (product page), `platform.html` (Shiftlead) |
| `counterguide/content/guides/` | Product guides for the product knowledge base (demo documents) |
| `counterguide/content/runbooks/` | Operations runbooks for the Shiftlead knowledge base (demo documents) |

## 0. Setup (about 1 min)

```bash
export AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1
git clone https://github.com/ninety7-fareed/cloudathon-team14.git && cd cloudathon-team14
CF=design/cloudformation
ACCT=$(aws sts get-caller-identity --query Account --output text); echo $ACCT   # must be 231075364174
out() { aws cloudformation describe-stacks --stack-name "$1" --query "Stacks[0].Outputs[?OutputKey=='$2'].OutputValue" --output text; }
```

**Before anything:** in the Bedrock console (us-east-1) → Model access, confirm **Amazon Nova Pro** and **Titan Text Embeddings V2** are enabled.

## 1. Network, repository, knowledge (run together, about 5-10 min)

Use `FoundationModelId=amazon.nova-pro-v1:0` (see "Template notes" below for why).

```bash
aws cloudformation deploy --stack-name counterguide-network    --template-file $CF/network.yaml &
aws cloudformation deploy --stack-name counterguide-repository --template-file $CF/repository.yaml &
aws cloudformation deploy --stack-name counterguide-knowledge  --template-file $CF/knowledge.yaml \
  --capabilities CAPABILITY_NAMED_IAM --parameter-overrides FoundationModelId=amazon.nova-pro-v1:0 &
wait
```

## 2. Upload demo documents and ingest (about 2-3 min)

```bash
aws s3 sync counterguide/content/guides   s3://counterguide-guides-$ACCT/
aws s3 sync counterguide/content/runbooks s3://counterguide-runbooks-$ACCT/
aws bedrock-agent start-ingestion-job --knowledge-base-id $(out counterguide-knowledge ProductKnowledgeBaseId) --data-source-id $(out counterguide-knowledge GuidesDataSourceId)
aws bedrock-agent start-ingestion-job --knowledge-base-id $(out counterguide-knowledge RunbookKnowledgeBaseId) --data-source-id $(out counterguide-knowledge RunbooksDataSourceId)
```

Check: Bedrock console → Knowledge bases → each data source shows **Available / Complete**.

## 3. Build and push the container (about 3-5 min)

Needs Docker (`docker version`). CloudShell or the code server.

```bash
REPO=$(out counterguide-repository RepositoryUri)
aws ecr get-login-password | docker login --username AWS --password-stdin ${REPO%%/*}
docker build --platform linux/amd64 -t $REPO:latest counterguide/app/
docker push $REPO:latest
```

## 4. Application stack (about 10-15 min; Aurora is the slow part)

```bash
aws cloudformation deploy --stack-name counterguide-application --template-file $CF/application.yaml \
  --capabilities CAPABILITY_NAMED_IAM --parameter-overrides FoundationModelId=amazon.nova-pro-v1:0
```

The image must be pushed first, or the ECS service cannot start.

## 5. Web stack and pages (about 5-10 min; CloudFront)

```bash
aws cloudformation deploy --stack-name counterguide-web --template-file $CF/web.yaml
aws s3 sync counterguide/web s3://counterguide-web-$ACCT/
echo "Site: $(out counterguide-web SiteUrl)"
```

## 6. Verify (the demo)

```bash
SITE=$(out counterguide-web SiteUrl)
curl -s $SITE/api/health          # {"app":"ok","database":"ok",...}
curl -s $SITE/api/products | head -c 300
```

Then in a browser at `$SITE`:

1. **Cited battery answer:** Guide chat → "Cited battery answer". Expect BT-NIMH-72, the 15-day battery return window, and `battery-safety.md` / `returns-policy.md` under Documents used.
2. **Kit refuses loose AA:** "Beginner RC kit". Expect real SKUs (truck, BT-NIMH-72, BT-CHG-NIMH) and a refusal to power the truck with loose AA cells.
3. **Out of scope:** "Out-of-scope question". Expect "I couldn't find that in the product guides".
4. **Shiftlead:** platform page → Demo controls → "Record simulated product-page errors" (clearly labelled simulation; no AWS change) → "Why is the product page erroring?". Expect the data tier named, with a proposed next action, and the list of read-only checks it ran. Then "Clear simulated rows".

Take a screenshot of each step as a backup.

## Updating one tier (minimal downtime)

- Front end: `aws s3 sync counterguide/web s3://counterguide-web-$ACCT/` (no other tier changes).
- Guides or runbooks: `aws s3 sync` + `start-ingestion-job` for that knowledge base only.
- Application: build and push a new tag, then redeploy step 4 with `ImageTag=<tag>`. ECS rolls tasks with 100% minimum healthy and rolls back on failure.

## Teardown (after judging)

```bash
aws s3 rm s3://counterguide-web-$ACCT --recursive
aws cloudformation delete-stack --stack-name counterguide-web && aws cloudformation wait stack-delete-complete --stack-name counterguide-web
aws cloudformation delete-stack --stack-name counterguide-application && aws cloudformation wait stack-delete-complete --stack-name counterguide-application
aws s3 rm s3://counterguide-guides-$ACCT --recursive; aws s3 rm s3://counterguide-runbooks-$ACCT --recursive
aws cloudformation delete-stack --stack-name counterguide-knowledge
aws ecr batch-delete-image --repository-name $(out counterguide-repository RepositoryName) --image-ids imageTag=latest
aws cloudformation delete-stack --stack-name counterguide-repository
aws cloudformation delete-stack --stack-name counterguide-network
```
(Versioned buckets may also need old versions removed before the stack deletes them.)

## Template notes (for Fareed)

1. **Model ID.** The templates default to the cross-region profile `us.amazon.nova-pro-v1:0`, but the IAM policies only allow the Nova Pro foundation model in us-east-1. A cross-region profile can route to us-east-2 or us-west-2 and get AccessDenied. Passing `FoundationModelId=amazon.nova-pro-v1:0` (as above) avoids that with no template edit. The app also retries with `amazon.nova-pro-v1:0` if the profile is denied.
2. **Agent alias.** `ShiftleadAlias` routes to `AgentVersion: "1"`. If the knowledge stack fails on the alias because version 1 doesn't exist, remove `RoutingConfiguration`; creating an alias without it creates a version automatically.
3. **Optional, for Shiftlead's sync check.** Add these to the container `Environment` in application.yaml so Shiftlead can see ingestion jobs:
   `GUIDES_DATA_SOURCE_ID` = import `${KnowledgeStackName}-GuidesDataSourceId`, `RUNBOOKS_DATA_SOURCE_ID` = import `${KnowledgeStackName}-RunbooksDataSourceId`. Without them it still reports knowledge-base status.
4. The app creates the `products` and `request_log` tables and seeds the sample catalog on first use. `/health` does not touch the database, so tasks pass health checks while Aurora is still starting.
