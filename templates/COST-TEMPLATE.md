---
type: event-template
updated: 2026-11-04 America/Chicago
writer: Claude (original worksheet); Codex (dated pricing, reconciliation and explanations)
status: two saved practice Calculator estimates; manual NAT allowance disclosed; not actual billing
---

# Practice cost estimates and adaptation worksheet

**Current PoC: $124.56/month, repriced November 4, 2026 after the YAML changed to separate web/app tiers.** The earlier $91.67 combined-tier PoC is historical. **Global unchanged: $1,725.69/month.** These are USD practice estimates, not actual bills or tested capacity.

| Scope | Monthly estimate | Evidence |
|---|---:|---|
| Historical combined web/app PoC (superseded for current YAML) | $91.67 | [Saved Calculator](https://calculator.aws/#/estimate?id=6a258b61606c21f324ba15c8208af154a27cb5f5) · [official CSV](../cost-estimates-2026-11-04/poc-calculator.csv) · [official PDF](../cost-estimates-2026-11-04/poc-calculator.pdf) |
| Representative two-region global design | $1,725.69 | [Saved Calculator](https://calculator.aws/#/estimate?id=819d119b3859baca9e003d559f43241940d6aecc) · [official CSV](../cost-estimates-2026-11-04/global-calculator.csv) · [official PDF](../cost-estimates-2026-11-04/global-calculator.pdf) · [JSON](../cost-estimates-2026-11-04/global-calculator.json) |
| **Current separated web/app three-tier PoC** | **$124.56** | [Saved Calculator](https://calculator.aws/#/estimate?id=9ad20f95a907a60771bf41dd9d311cb70f57f744) · [CSV](../cost-estimates-2026-11-04/poc-three-tier/poc-three-tier.csv) · [PDF](../cost-estimates-2026-11-04/poc-three-tier/poc-three-tier.pdf) · [JSON](../cost-estimates-2026-11-04/poc-three-tier/poc-three-tier.json) |

The current PoC and global estimates have $0 upfront in the selected recurring configurations. Global 12-month planning total: **$20,708.28**, with no commitment purchased. Links contain generic practice assumptions, expire after one year per Calculator, and can be read by anyone possessing the link. PDF/JSON export can generate an equivalent additional snapshot URL; use the current three-tier PoC and global rows above as the active references; retain the old PoC link as history.

## 1. How this follows Martinez's guidance

Source: Gerardo's original briefing transcript, `C:\Users\gvera\Downloads\Cloudathon_original (1).txt` (speech-to-text; paraphrased, not treated as an exact quotation).

| What Martinez described | Our preparation choice |
|---|---|
| 23:20-24:37: global architecture, an architecture document, cost analysis, and defending decisions | Keep a full diagram-aligned cost inventory plus a short explanation of drivers and tradeoffs. |
| 43:32-44:29: prepare templates and adapt them to the use case | Preserve the dated estimate and inputs; replace workload/regions/capacity from the event scenario. |
| 46:34-50:07: a large global design, supported by a small top-to-bottom implementation using small machines and architectural layers | Estimate the current small three-tier YAML separately from the much larger logical design; keep prior rehearsal evidence tied to its actual version. Do not deploy the whole diagram merely to demonstrate it. |

The specific regions, instance types, workload, four NATs and separate web/app machines are **our practice selections**, not instructor-mandated quantities or his approval. His example of millions of users is not evidence these selected instances can serve millions. The separate-tier YAML was inspected November 4; no new deployment or rehearsal was independently verified during this pricing update. Three logical layers do not by themselves mandate three separate machines.

## 2. Current three-tier PoC: source match and unchanged assumptions

Source: [network.yaml](../cfn/network.yaml), [app.yaml](../cfn/app.yaml), and Gerardo's November4 update. Source inspection confirms public ALB -> web ASG (2 t3.micro) -> internal ALB/listener8080 -> app ASG (2 t3.micro) -> private RDS. This pricing update did not deploy or test the stack and did not edit the YAML.

Only **EC2 count2->4** and **ALB count1->2** changed from the saved $91.67 estimate; inherited RDS, public IPv4 and transfer configurations were compared against the old export and matched exactly.

- Oregon `us-west-2`, Linux/shared/On-Demand,730h/month; two web +two app **t3.micro** at baseline. No average scale-out allowance.
- **8GB gp3 per instance** remains an assumption because the YAML does not explicitly set the AMI root volume;32GB total. It is not an observed AMI configuration. No paid detailed monitoring or snapshots selected; no surplus CPU credits assumed at this low load.
- Two ALBs, one internet-facing and one internal; **each** retains0.001GB/hour processed payload,0.01 new connections/sec,1-second connection duration,0.01 requests/sec,one rule evaluation/request. Internal ALB uses private addresses, so **three public IPv4 total remains unchanged**:two public ALB +one NAT;zero idle and no public EC2 IPs.
- One shared zonal NAT,1GB/month processing;RDS MySQL **db.t3.micro Single-AZ**,20GB gp3 encrypted,one-day retention in YAML;no additional billable backups assumed. No Proxy,Database Insights or Extended Support.
- Transfer allowances unchanged:1GB/month internet out and1GB billable cross-AZ transfer. Calculator accounts for billable endpoints; do not double quantities again. The added hop may change real traffic, but this requested comparison deliberately keeps allowances fixed.

| Current PoC component | Monthly USD |
|---|---:|
| Four EC2 +assumed root EBS, excluding NAT | $32.93 |
| Two ALBs +low LCUs | $32.86 |
| One shared NAT, unchanged manual rounded allowance | $33.00 |
| RDS instance +storage | $14.71 |
| Three public IPv4 | $10.95 |
| Data transfer | $0.11 |
| **Calculator total** | **$124.56** |

NAT remains in the EC2 **Additional costs** field because of the previously recorded Calculator VPC-form limitation:the export's EC2 line is$65.93 including$33 NAT. The table separates it once, without double counting. Exact NAT rate calculation$32.895 is conservatively rounded to$33, unchanged from the earlier estimate.

**Difference from $91.67: +$32.89/month**, comprising **+$16.47 EC2/EBS** and **+$16.42 ALBs**. Calculator recomputes aggregated amounts rather than doubling the previously rounded line items; this is why the hand estimate$124.57 differs by one cent. It did not add public IPv4 for the internal ALB.

**Requested six-hour formula:** $124.56 x6 /730 = 1.023780821917808219178082192 = **$1.02** (before taxes/account allowances). This scales the monthly traffic allowances too;actual demonstration traffic,partial-hour rounding,CPU credits,retained resources or extra runtime can change the bill. Earlier$0.75/$0.91 six-hour figures belong to the superseded combined-tier PoC.

**Top two budgeted PoC drivers** (almost tied with ALBs$32.86):

- **NAT,$33/month:** restrict it to the timed demonstration and delete it afterwards to reduce billed hours;private instances then lose internet egress until a suitable path is restored.
- **EC2/EBS,$32.93/month:** for disposable practice,one web and one app instance would lower compute/storage costs,with the explicit loss of two-instance resilience in each tier;do not silently use that reduction in the current two-per-tier estimate.

Global verification:the unchanged$1,725.69 export already has **2 web +2 app m6i.large and1 public +1 internal ALB per region**,Oregon and Mumbai. Regions/global design/exports were not edited. The global estimate uses larger instance/storage/workload assumptions than this PoC.

The practice stack still uses HTTP and a throwaway password in user data/PHP. Costing it does not make those shortcuts production-ready.

## 3. Representative global workload and capacity

Source inventory: [GLOBAL-ARCH-TEMPLATE.drawio](GLOBAL-ARCH-TEMPLATE.drawio) and [architecture document](ARCH-DOC-TEMPLATE.md). **Logical design only.** These are steady-state practice assumptions to replace on Saturday:

| Input | Explicit practice assumption |
|---|---|
| Workload | 100,000 monthly active users; 20 million HTTPS viewer requests/month; 2TB = 2,048GB delivered; 80% US edge traffic, 20% India. 99% reads/cacheable requests, 1% writes; 90% cache hit ratio on cacheable requests. Approximately 2,180,000.00 origin requests/month, not measured. |
| Runtime/pricing | Both regions fully provisioned 730h/month, Linux/shared/On-Demand; no RI, Savings Plan, Spot or private discount. No credit balance deducted. |
| Region A, Oregon | 2 web + 2 app **m6i.large**, two AZs, 30GB gp3 each. RDS MySQL **db.m6i.large Multi-AZ DB instance**, one writer + non-readable standby included in the Multi-AZ rate; one selected node, not two charged Multi-AZ nodes. 200GB gp3 and 50GB additional billable backup storage beyond any included allowance. |
| Region B, Mumbai | 2 web + 2 app **m6i.large**, same root storage. Fully provisioned recovery compute, not reduced-capacity standby. **One db.m6i.large Single-AZ asynchronous cross-region read replica**, 200GB gp3 + 50GB extra backup. The faded optional local replica standby is **not selected**. |
| ALBs | Two per region (one public, one internal). A: each processes 0.3GB/hour, 1 request/sec, 0.2 new connections/sec, 5s connections. B: each 0.01GB/hour, 0.01 request/sec, 0.01 new connections/sec, 5s. One rule evaluation/request. These are separate per-hop traffic envelopes, not a benchmark. |
| NAT / public IPv4 | Two zonal NATs per region, same-AZ egress; A processes **50GB total/month (25GB each)**, B **30GB total (15GB each)**, allowing for monitoring/log uploads and third-party egress. Four minimum public IPv4/region: two public ALB addresses + two NAT EIPs; internal ALBs and private EC2 have none. ALB scaling may allocate more addresses. |
| S3 | Each region 100GB content/replica objects +20GB audit/access logs =120GB S3 Standard. Already populated in both regions; initial backfill excluded. A:110k PUT/LIST and 1m GET; B:110k PUT/LIST (includes 10k CRR destination writes) and 10k GET. Ongoing CRR sends 10GB A->B/month; no paid replication time control/metrics. |
| TGW | One TGW/region, **one VPC attachment + one side of peering** per region = four billed attachments total. Each VPC sends 10GB/month through TGW; peering ingress adds no TGW processing. Calculator's flat per-attachment input is an average 5GB across the VPC+peering pair, producing the correct 10GB billed total. RDS managed replication is separate from TGW. |
| Other transfer | A:50GB billable cross-AZ +20GB A->B (10GB RDS +10GB private TGW) +20GB internet. B:10GB billable cross-AZ +10GB B->A TGW +20GB internet. S3's 10GB CRR transfer is in the S3 entry, not counted again here. ALB cross-zone and RDS same-region synchronous-replication transfer exemptions are not re-added as generic transfer. |
| CloudWatch, each region | 40 custom/detailed metrics, 100k GetMetricData metrics requested, 100k other API requests, 10 standard alarm metrics, one dashboard. A:20GB standard application logs +5GB VPC vended logs; B:5GB application +1GB VPC logs. One-month retention; Calculator uses 15% archived-size compression. No paid DB Insights, RUM sessions, canaries or traced requests selected. |
| Secrets/KMS, each region | Two secret copies, 730h each, 10k API calls with cached retrieval; no automatic rotation Lambda selected. Three symmetric customer-managed KMS keys +200k requests; no paid additional key rotations or HSM. Calculator's secret-hour proration is retained. |
| CloudTrail | First management-event trail copy in each region, 1m events each; no Insights/Lake. Content-bucket data events:1.01m A,0.02m B; audit bucket excluded to avoid logging its own delivery. S3 storage/requests priced above, not included free with CloudTrail. |
| Shared edge | One CloudFront PAYG distribution. After allocating its **shared unused** 1TB/10m request allowance once: US819.2GB +8m requests, India204.8GB +2m requests. Upload to origins1GB total (0.8/0.2GB). No flat-rate bundle also charged. AWS-origin->CloudFront delivery is not also entered as regional internet egress. |
| Shared WAF/DNS/TLS | One CloudFront-scope WAF ACL (us-east-1 control plane), two custom rules +two AWS managed groups,20m full requests, within1500WCU; no Bot/Fraud/CAPTCHA/Marketplace. One public Route53 zone +100k non-alias queries; CloudFront alias queries free. Three non-exportable ACM public certificates:CloudFront in us-east-1 and public ALBs in their own regions. No private CA/exportable certificate charges. |

The m6i.large/db.m6i.large choices are costable general-purpose practice sizes, **not proof of throughput**. Validate peak workload, DB connections/storage IOPS, scaling behavior, quotas and recovery targets before defending them as adequate. Region B's nominal compute capacity equals A, but its DB lacks a local Multi-AZ standby. Origin failover does not promote its read-only replica or recover writes.

## 4. Global cost, separated into meaningful components

| Component | Monthly USD |
|---|---:|
| EC2 + root EBS, excluding NAT allowance | $595.78 |
| RDS writer/standby + replica, storage + extra backups | $507.29 |
| Four NATs: manual conservative allowance | $152.00 |
| Four ALBs including LCUs | $71.36 |
| Eight minimum public IPv4 addresses | $29.20 |
| TGW: two VPC and two peering-side attachments + processing | $175.60 |
| Regional + S3 inter-region transfer | $6.65 |
| S3 storage and requests in both regions | $7.26 |
| CloudWatch logs, metrics, APIs, alarms | $46.66 |
| Secrets Manager copies + APIs | $1.72 |
| KMS keys + requests | $7.20 |
| CloudTrail data events | $1.03 |
| CloudFront, once globally | $102.40 |
| CloudFront-scope WAF, once globally | $21.00 |
| Route 53, once globally | $0.54 |
| Non-exportable public ACM certificates | $0.00 |
| **Native Calculator total** | **$1,725.69** |

Displayed component rows are rounded; Calculator sums unrounded inputs. The exported raw CSV reconciles to the displayed total. EC2 lines in the official export **include the manually added NAT allowance**; the table above subtracts it from EC2 and shows it once separately.

Largest drivers: **EC2 +EBS $595.78** and **RDS $507.29**, together **63.92%**. Next are TGW **$175.60** and NAT **$152.00**. NAT is an important easily missed fixed cost, not universally the largest service.

### Calculator limitation: zonal NAT is a supported manual allowance

The VPC NAT form currently requires nonzero settings for an unrelated **Regional NAT Gateway** as well as zonal NAT. Saving the zonal-only configuration fails. [Observed form/error](../cost-estimates-2026-11-04/calculator-nat-limitation.png) and [visible calculations](../cost-estimates-2026-11-04/calculator-nat-limitation.txt) are saved. No fake Regional NAT was added and no validation was bypassed.

Verified rates in the Calculator: Oregon $0.045/gateway-hour and $0.045/GB; Mumbai $0.056/hour and $0.056/GB. The saved EC2 **Additional costs** field supports whole dollars, so the correctly calculated zonal costs are entered conservatively there and labeled in each description:

| Scope | Exact rate-based NAT/month | Included manual allowance |
|---|---:|---:|
| PoC:1 Oregon NAT +1GB | $32.895 | $33 |
| Global A:2 Oregon NATs +50GB | $67.95 | $68 |
| Global B:2 Mumbai NATs +30GB | $83.44 | $84 |

Four global NATs alone have **$147.46 fixed hourly cost/month**. With selected processing, exact global NAT cost is **$151.39**, allowance **$152**, overage from rounding **$0.61**. Initial raw input captures used20GB/region; final CSV/JSON/descriptions and this worksheet supersede those earlier captures.

## 5. Free components, allowances and exclusions

- No separate hourly charge is modeled for VPCs/subnets/route tables/security groups, IGWs, ordinary EC2 Auto Scaling, S3 gateway endpoints, standard IAM/MFA service usage, or CloudFormation managing these AWS resource types. Underlying resources, traffic, optional features and MFA hardware are separate.
- ACM non-exportable public certificates used with integrated services are $0; the Calculator entry records zero exportable certificates, with the three actual non-exportable certificates explained in its description. That entry is an inventory note, not a claim that three free certificates were requested.
- CloudFront's shared allowance is applied **only once** and assumes no other account workload consumed it. CloudTrail's first management copy and Calculator's free dashboards are also reflected. Other account-dependent Free Tier/credits, KMS free requests and the shared internet-egress allowance are not comprehensively reconciled. Regional internet traffic is conservatively entered at gross list pricing. **This is a planning estimate, not a prediction of the net account bill.**
- Basic support assumed; taxes, human operations, domain registration, initial migration/backfill, restore drills/failback, deployment build tools, unexpected autoscaling/CPU surplus credits, retained snapshots, optional replica standby, paid WAF extras and services absent from the selected diagram are excluded. Estimate these if the use case selects them. Alarms are priced; external SMS/email notification systems are not selected here.

## 6. One cheaper alternative with a tradeoff

**One shared NAT per region instead of one per AZ**, with the same total bytes processed, removes two gateway-hours streams and two EIPs. Rate-based fixed saving: **$81.03/month before extra cross-AZ transfer and allowance rounding**. The resulting global budget is roughly $1,645/month; this alternative was calculated locally, not saved as a third Calculator estimate and not implemented.

Tradeoff: egress in that region depends on one AZ/NAT; instances in the other AZ may incur cross-AZ charges and lose outbound access during an AZ failure. It does not preserve the diagram's same-AZ egress availability. Judge decision: retain two NATs where availability justifies the cost; choose the cheaper pattern only when the scenario accepts that compromise. Another obvious cost question is whether two TGWs are justified for only two VPCs; compare simpler connectivity only after confirming its actual requirements.

## 7. What to tell a judge

“We separated the small demonstration from the full design. Our current three-tier Oregon PoC is about $125 for a full month, or $1.02 using monthly cost times six divided by730. Our two-region practice design is about $1,726 a month for the workload we assumed. Compute and the databases are the biggest costs. We included all four NAT gateways, both regions' load balancers and operating services, and counted shared edge services once. A single NAT per region could reduce fixed costs by about $81 a month, but weakens egress availability and can add cross-AZ transfer. We will replace the assumptions with the competition's workload.”

Three practice questions:

1. Why does the PoC cost far less than the global design, and what does the PoC **not** demonstrate?
2. Why are NAT and public IPv4 separate charges, and where are they included in this Calculator export?
3. If the budget is cut, what would you reduce first, what would it save, and what reliability or recovery tradeoff would you accept?

## 8. Adapt on the day and verification record

Replace: business/user/peak request assumptions; region/residency constraints; average and scaled EC2 count; DB size/HA/backups; all traffic paths; actual DR capacity; current rates/account allowances. Update diagram, architecture document, cost and pitch together. Save a new link/export rather than overwriting the dated preparation evidence.

Verified: both public links reopened; PoC scope and global regions/components checked; CSV sums recomputed; global JSON checked; PDF text/selectable links inspected; all five exported PDF pages rendered and visually reviewed (global's fourth page contains only the AWS acknowledgement). Poppler reported Symbol/ArialUnicode fallback warnings; no visible missing text or clipping was observed. The original pass checked then-current source hashes. The later three-tier reprice checked the updated YAML before/after without changing it; global diagram and estimate exports are unchanged. Source captures remain in [dated evidence](../cost-estimates-2026-11-04); final exports take precedence over intermediate captures.

Not verified: actual AWS billing/credits, resource state/teardown, application performance, automatic failover, RTO/RPO, or end-to-end delivery of the proposed global architecture. No AWS resource, account setting, commitment, website or resume changed. No cost claim is instructor approval.

Official references, checked November4,2026: [AWS Calculator](https://calculator.aws/) · [Calculator assumptions](https://aws.amazon.com/calculator/calculator-assumptions/) · [VPC/NAT/IPv4](https://aws.amazon.com/vpc/pricing/) · [EC2](https://aws.amazon.com/ec2/pricing/on-demand/) · [RDS MySQL](https://aws.amazon.com/rds/mysql/pricing/) · [EBS](https://aws.amazon.com/ebs/pricing/) · [TGW](https://aws.amazon.com/transit-gateway/pricing/) · [CloudFront](https://aws.amazon.com/cloudfront/pricing/) · [Route53](https://aws.amazon.com/route53/pricing/) · [ACM](https://aws.amazon.com/certificate-manager/pricing/). The selected-region Calculator calculations and dated exports are the direct price evidence; public-page rate tables may be dynamic.

Original worksheet/template credit:Claude. Diagram reference:CIS3367 Team1. Dated estimates, reconciliation and learning explanation:Codex,November4,2026.

November4 three-tier revision:current PoC link reopened;all five exported subservice rows reconciled (six component lines after separating NAT);CSV/PDF/JSON saved under `poc-three-tier`;one-page PDF text and visual review completed. User-authored architecture change,source inspection and repricing are distinct from a verified deployment.
