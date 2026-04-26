# ShopCloud — E-Commerce Platform

> EECE 503Q — DevSecOps, American University of Beirut, Spring 2026

A cloud-native e-commerce platform built with FastAPI microservices, deployed on AWS ECS Fargate, provisioned with Terraform IaC, and automated via GitHub Actions CI/CD.

## Architecture Overview

```
Internet → CloudFront (WAF: CommonRuleSet + SQLi + RateLimit)
              ├── /api/*      → Public ALB → ECS Fargate
              │                                ├── Catalog (FastAPI)
              │                                ├── Cart    (FastAPI + Redis)
              │                                └── Checkout (FastAPI)
              └── /  (static) → S3 (frontend HTML/CSS/JS)

Bastion SSH Tunnel → Internal ALB → Admin Service (Jinja2)
                                    (no public route — defense in depth:
                                     internal scheme + path block at public ALB)

Checkout (sync DB commit) ──response──→ Customer
        └── BackgroundTask ──→ SQS ──→ Lambda ──→ S3 (PDF) ──→ SES (email)
                                          ↓ on failure (4 retries)
                                       SQS DLQ
```

The checkout path is split deliberately: the order is committed to RDS and the
HTTP response is sent **before** the SQS publish runs, so the customer sees
"Order Confirmed" without waiting for PDF + S3 + email. The publish executes as
a FastAPI `BackgroundTask` after `response.send()`, and Lambda processes the
queue out of band.

### AWS Services Used

| Service | Purpose |
|---------|---------|
| ECS Fargate | Microservice containers (catalog, cart, checkout, admin) |
| RDS PostgreSQL 16 | Relational database (Multi-AZ in prod) |
| ElastiCache Redis 7 | Cart session storage (24h TTL) |
| Cognito | Authentication (customer + admin user pools) |
| SQS + Lambda | Async invoice generation pipeline |
| S3 | Static frontend hosting + invoice storage |
| CloudFront | CDN with S3 OAC |
| WAF | Web application firewall (OWASP rules + rate limiting) |
| ECR | Docker image registry (scan on push) |
| Route 53 | DNS management |
| SSM Parameter Store | Secrets and configuration management |

## Project Structure

```
shopCloud/
├── app/                          # Application code
│   ├── shared/                   # Shared modules (config, models, auth, schemas)
│   ├── services/
│   │   ├── catalog/              # Product catalog service
│   │   ├── cart/                 # Shopping cart service (Redis-backed)
│   │   ├── checkout/             # Checkout + orders service
│   │   └── admin/                # Admin panel (Jinja2 templates)
│   ├── entrypoints/              # FastAPI app instances
│   ├── invoice/                  # Lambda function (PDF invoice pipeline)
│   ├── migrations/               # Alembic database migrations
│   ├── scripts/                  # Seed data script
│   ├── tests/                    # Unit tests (pytest)
│   ├── Dockerfile                # Multi-target (6 targets)
│   └── requirements.txt
├── frontend/                     # Static frontend (HTML/CSS/JS)
│   ├── js/                       # config, auth, api, catalog, cart, checkout
│   ├── css/                      # Responsive stylesheet
│   └── *.html                    # 7 pages
├── terraform/                    # Infrastructure as Code
│   ├── modules/                  # 14 reusable modules
│   │   ├── vpc/                  # VPC with 3-tier subnets
│   │   ├── security_groups/      # 8 security groups
│   │   ├── ecr/                  # Container registry
│   │   ├── ecs/                  # ECS cluster + services + auto-scaling
│   │   ├── alb/                  # Application load balancers
│   │   ├── rds/                  # PostgreSQL database
│   │   ├── elasticache/          # Redis cache
│   │   ├── cognito/              # User pools (customer + admin)
│   │   ├── invoice_pipeline/     # SQS + Lambda + S3 + SES
│   │   ├── edge/                 # CloudFront + WAF + Route 53
│   │   ├── bastion/              # Bastion host
│   │   ├── ssm/                  # Parameter Store
│   │   ├── monitoring/           # SNS + CloudWatch alarms + dashboard
│   │   └── security_hardening/   # NACLs + Flow Logs + CloudTrail + GuardDuty + Config + WAF logs
│   ├── main.tf                   # Root module (prod + dev environments)
│   ├── variables.tf
│   ├── outputs.tf
│   └── providers.tf
├── scripts/                      # Deployment scripts
│   ├── deploy.sh                 # ECS deployment
│   └── deploy-frontend.sh        # S3/CloudFront frontend deployment
├── .github/workflows/            # CI/CD
│   ├── dev.yml                   # Dev pipeline (lint → test → deploy)
│   └── prod.yml                  # Prod pipeline (lint → test → plan → deploy)
└── docker-compose.yml            # Local development
```

## Local Development

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Git

### Quick Start

```bash
# 1. Start infrastructure (Postgres + Redis)
docker-compose up -d postgres redis

# 2. Run database migrations
docker-compose run --rm migrate

# 3. Seed sample data
docker-compose exec app python -m scripts.seed_data

# 4. Start all services
docker-compose up app admin
```

- **Customer API:** http://localhost:8000
- **Admin Panel:** http://localhost:8001/admin
- **API Health:** http://localhost:8000/health

### API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /api/products | No | List products (paginated) |
| GET | /api/products/search?q= | No | Full-text search |
| GET | /api/products/categories | No | List categories |
| GET | /api/products/{id} | No | Product detail |
| GET | /api/cart | Customer | View cart |
| POST | /api/cart/items | Customer | Add to cart |
| PUT | /api/cart/items/{id} | Customer | Update quantity |
| DELETE | /api/cart/items/{id} | Customer | Remove item |
| POST | /api/checkout | Customer | Place order |
| GET | /api/orders | Customer | Order history |
| GET | /api/orders/{id} | Customer | Order detail |

### Running Tests

```bash
# Create test database
docker-compose exec postgres createdb -U shopcloud shopcloud_test

# Run tests
cd app
DATABASE_URL=postgresql+asyncpg://shopcloud:localdev@localhost:5432/shopcloud_test \
REDIS_URL=redis://localhost:6379 \
pytest tests/ -v
```

## Infrastructure Deployment

### Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.7.0

### Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This provisions both **prod** and **dev** environments:
- **Prod:** 4 ECS services, Multi-AZ RDS, CloudFront + WAF, internal ALB for admin
- **Dev:** Combined service + admin, single-AZ RDS, public ALB

### Deploy Application

```bash
# Deploy all services to dev
./scripts/deploy.sh dev

# Deploy all services to prod
./scripts/deploy.sh prod

# Deploy specific service
./scripts/deploy.sh prod catalog

# Deploy frontend
./scripts/deploy-frontend.sh
```

## CI/CD Pipeline

### Dev Pipeline (`.github/workflows/dev.yml`)
Triggered on push/PR to `dev` branch:
1. **Lint** — ruff check + format
2. **Test** — pytest with Postgres + Redis services
3. **Terraform Validate** — syntax and format check
4. **Build & Deploy** — Docker build, ECR push, ECS update (push to dev only)

### Prod Pipeline (`.github/workflows/prod.yml`)
Triggered on push to `main` branch:
1. **Lint** — ruff check + format
2. **Test** — pytest with Postgres + Redis services
3. **Terraform Plan** — infrastructure change preview
4. **Build & Deploy** — Docker build, ECR push, migrations, ECS update, frontend deploy

## Security

- **Authentication:** AWS Cognito (2 user pools — customer + admin)
- **Network:** 3-tier VPC (public, app, data subnets), 8 security groups, 3 NACLs (defense in depth)
- **Edge:** CloudFront + WAF (OWASP rules, SQLi protection, rate limiting)
- **Admin Isolation:** Internal ALB, accessible only via bastion SSH tunnel
- **Secrets:** SSM Parameter Store (SecureString for passwords)
- **Container Security:** ECR scan-on-push + EventBridge alert on CRITICAL findings
- **Database:** Encrypted at rest, private subnet only, no public access
- **Audit:** CloudTrail (account-wide), VPC Flow Logs (per-env), WAF logs
- **Threat Detection:** GuardDuty (S3 protection), IAM Access Analyzer
- **Compliance:** AWS Config recorder + 9 managed rules

Full posture documented in [`docs/security-hardening-report.md`](docs/security-hardening-report.md).

## Environments

| Aspect | Production | Development |
|--------|-----------|-------------|
| VPC CIDR | 10.0.0.0/16 | 10.1.0.0/16 |
| AZs | 2 (us-east-1a, 1b) | 1 (us-east-1a) |
| ECS Services | 4 (catalog, cart, checkout, admin) | 2 (combined, admin) |
| RDS | `db.t3.micro`, Multi-AZ (auto-failover), 1-day automated backups (account-level Free Tier cap; raise to 35 once off Free Tier), deletion protection | `db.t3.micro`, Single-AZ, no backups |
| ElastiCache | `cache.t3.micro` Redis 7 (single node) | `cache.t3.micro` Redis 7 (single node) |
| ALB | Public + Internal | Public only |
| CloudFront + WAF | Yes (CommonRuleSet + SQLi + RateLimit) | No |
| ECR scan-on-push | All 5 repos (catalog, cart, checkout, admin, migrate) | Same repos shared |

## Monitoring & Observability

Phase 3 wires every critical signal into CloudWatch (alarms + dashboard +
Log Insights) and routes pages through a single SNS topic per environment.

### Alarm routing

Each env has one SNS topic (`shopcloud-{env}-alarms`). Ops gets paged via the
email subscription gated on `var.alarm_email` — set it once at the root level:

```bash
terraform apply -var="alarm_email=oncall@yourdomain.com"
```

Dev's topic exists but has no email subscription by design — prod owns the
on-call surface so dev noise doesn't double-page anyone. After apply, AWS
sends a confirmation email; **click the link** or no alarm will ever reach
the inbox.

### Dashboard

A single 15-widget dashboard per env covers service health, ALB latency &
errors, ECS CPU/memory, Lambda, RDS, Redis, SQS, and DLQ depth.

```bash
# Get the direct console URL after apply
terraform output prod_dashboard_url
terraform output dev_dashboard_url
```

The dashboard auto-extends to new ECS services (driven by the
`ecs_services` map in `main.tf`).

### Alarms (38 in prod)

| Tier | Coverage |
|------|---------|
| ECS (per service) | CPU > 80% (10 min), memory > 85%, running tasks < desired |
| ALB | 5xx > 10/5min, 4xx > 50/5min, p99 latency > 2s, unhealthy targets > 0 |
| RDS | CPU > 80%, connections > 50, free storage < 2 GiB, read latency > 20 ms, write > 50 ms, replica lag > 30 s (prod) |
| ElastiCache | CPU > 80%, memory > 85%, evictions > 0, connections > 100 |
| Lambda | Errors > 3/15min, duration > 25s, throttles > 0 |
| SQS DLQ | Any message visible (paged via invoice_pipeline + monitoring topics) |
| NAT Gateway | Packet drops > 10/5min |

### Log Insights queries

Structured JSON logging is in place across all services. Eight saved queries
live in CloudWatch Logs Insights — run them by name from the console:

| Query | Use case |
|---|---|
| `errors-last-hour` | Triage spike of 5xx |
| `slow-requests-p95` | Find endpoints > 1s |
| `auth-failures` | Cognito + JWT rejection patterns |
| `cart-redis-errors` | Cache layer issues |
| `checkout-failures` | Order placement failures |
| `lambda-invoice-errors` | PDF + SES pipeline issues |
| `dlq-replay-trace` | Trace a message that hit the DLQ |
| `admin-access-audit` | Who did what on admin |

Run with:

```bash
aws logs start-query \
  --log-group-name /ecs/shopcloud-prod-checkout \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string "fields @timestamp, @message | filter level='ERROR' | sort @timestamp desc"
```

### VPC Flow Logs

| Env | Log group | Retention |
|---|---|---|
| Prod | `/vpc/shopcloud-prod/flow-logs` | 30 days |
| Dev | `/vpc/shopcloud-dev/flow-logs` | 14 days |

Captures `ALL` traffic (accept + reject) for both troubleshooting and
security forensics.

### CloudTrail + GuardDuty + Config

| Resource | Location / ID |
|---|---|
| CloudTrail S3 bucket | `shopcloud-cloudtrail-<account>` (all regions, mgmt events) |
| GuardDuty detector | `terraform output guardduty_detector_id` (S3 protection on) |
| IAM Access Analyzer | `terraform output access_analyzer_arn` (account-level) |
| AWS Config recorder | `shopcloud-recorder` (9 managed rules — see security report §6) |
| WAF log group | `/aws/wafv2/shopcloud-prod` |

These are all **account-wide singletons**, gated in Terraform via
`create_account_singletons = true` on the prod security_hardening module
only — dev does not duplicate them.

### Verification after `terraform apply`

```bash
# 1. Confirm SNS subscription is "Confirmed" (not "PendingConfirmation")
aws sns list-subscriptions-by-topic \
  --topic-arn $(terraform output -raw prod_alarms_topic_arn)

# 2. Trigger a test alarm
aws cloudwatch set-alarm-state \
  --alarm-name shopcloud-prod-orders-dlq-not-empty \
  --state-value ALARM --state-reason "smoke test"

# 3. Open the dashboard
echo $(terraform output -raw prod_dashboard_url)
```

## Rollback Procedures

Three rollback strategies are available, ordered by speed:

### Option 1 — ECS Task Definition Reversion (fastest, ~2 min)

ECS keeps previous task definition revisions. Roll back to the last known-good revision:

```bash
# Find the previous stable revision
aws ecs describe-services --cluster shopcloud-prod --services catalog \
  --query 'services[0].taskDefinition' --output text
# e.g. arn:aws:ecs:us-east-1:123456:task-definition/shopcloud-prod-catalog:5

# Force the service back to the previous revision
aws ecs update-service --cluster shopcloud-prod --service catalog \
  --task-definition shopcloud-prod-catalog:4 --force-new-deployment --no-cli-pager

# Repeat for other affected services (cart, checkout, admin)
aws ecs wait services-stable --cluster shopcloud-prod --services catalog
```

### Option 2 — Git Revert + Re-deploy (~10 min)

Revert the bad commit and let CI/CD rebuild and deploy:

```bash
# Identify the bad commit
git log --oneline -5

# Revert it (creates a new commit, safe for shared branches)
git revert <bad-commit-sha>
git push origin main

# The prod CI/CD pipeline will automatically rebuild and deploy
# Monitor: https://github.com/<org>/shopCloud/actions
```

### Option 3 — Manual ECR Image Rollback (~5 min)

Pull a previous image tag and re-tag it as `latest`:

```bash
ECR_REGISTRY=$(aws ecr describe-repositories --repository-names shopcloud/catalog \
  --query 'repositories[0].repositoryUri' --output text | sed 's|/catalog||')

# List recent image tags
aws ecr describe-images --repository-name shopcloud/catalog \
  --query 'sort_by(imageDetails,&imagePushedAt)[-5:].imageTags' --output table

# Re-tag a known-good image as latest
GOOD_TAG=<previous-commit-sha>
for service in catalog cart checkout admin; do
  docker pull $ECR_REGISTRY/shopcloud/$service:$GOOD_TAG
  docker tag $ECR_REGISTRY/shopcloud/$service:$GOOD_TAG $ECR_REGISTRY/shopcloud/$service:latest
  docker push $ECR_REGISTRY/shopcloud/$service:latest
done

# Force ECS to pick up the new "latest"
for service in catalog cart checkout admin; do
  aws ecs update-service --cluster shopcloud-prod --service $service \
    --force-new-deployment --no-cli-pager
done
```

### Database Rollback

If a migration caused the issue, roll back with Alembic:

```bash
# Run inside the ECS task or locally with DB access
alembic downgrade -1
```

## Operational Notes

### Deployed Endpoints (prod, account 519718528172, us-east-1)

| Surface | URL |
|---|---|
| Storefront + API (CloudFront) | `https://d3w3kfhcnfq6gy.cloudfront.net` |
| Public API ALB (origin) | `sc-prod-alb-1798766792.us-east-1.elb.amazonaws.com` |
| Internal admin ALB | `internal-sc-prod-internal-...elb.amazonaws.com` (VPC-only, reach via bastion SSH tunnel) |
| Static frontend bucket | `shopcloud-static-20260418190509873000000002` |
| Invoice bucket | `shopcloud-prod-invoices-519718528172` |

### Invoice Lambda

The Lambda at `shopcloud-prod-invoice` ships native deps (`psycopg2-binary`,
`fpdf2` → Pillow). Because Terraform's `archive_file` only zips files (it
doesn't run `pip install`), the `invoice_pipeline` module includes a
`null_resource.lambda_build` provisioner that runs:

```bash
docker run --platform linux/amd64 public.ecr.aws/sam/build-python3.12 \
  pip install -r requirements.txt -t /var/task
```

into `app/invoice/build/` before `archive_file` zips that directory. The
provisioner re-runs whenever `lambda_function.py` or `requirements.txt`
changes (`filesha256` triggers).

### Invoice DLQ inspection

```bash
# Depth check
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/519718528172/shopcloud-prod-orders-dlq \
  --attribute-names ApproximateNumberOfMessages

# Look at recent Lambda errors
aws logs tail /aws/lambda/shopcloud-prod-invoice --since 30m --filter-pattern ERROR

# Redrive DLQ → main queue once root cause is fixed
aws sqs start-message-move-task \
  --source-arn arn:aws:sqs:us-east-1:519718528172:shopcloud-prod-orders-dlq
```

### SES sandbox (known constraint)

The AWS account is in SES sandbox mode (verified by
`aws ses get-send-quota` → `Max24HourSend: 200`). Only emails to verified
identities (`sarmad.farhat2017@gmail.com`, `hasan.nasrallah23@gmail.com`,
`rasha_alannan@live.com`) can receive invoices.

**A production-access request was submitted to AWS Trust & Safety on
2026-04-22 and denied on 2026-04-23.** The reason given was account
maturity, not project quality:

> "Due to some limiting factors on your account currently, you are not
> eligible to send SES messages in US East (N. Virginia) region. You will
> need to show a pattern of use of other AWS services and a consistent
> paid billing history to gain access to this function. Please open a
> new case after you have a successful billing cycle and additional use
> of other AWS services."

This is AWS's standard auto-denial for accounts under ~30 days old without
sustained billing history — independent of the technical merits of the
request. The full bounce / complaint pipeline (SNS → Lambda → email
suppression in RDS) is implemented and exercised end-to-end against the
verified addresses; it will continue to function unchanged once the
account ages out of the restriction. **Re-apply 30–60 days after the
first paid billing cycle.**

Demo and grading flows are unaffected: customer Cognito accounts are
created with the verified addresses, so every order in the demo produces
a real invoice email.

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), asyncpg, redis-py
- **Database:** PostgreSQL 16 (JSONB, TSVECTOR full-text search)
- **Cache:** Redis 7
- **Frontend:** Vanilla HTML/CSS/JS (no build step)
- **IaC:** Terraform 1.7+ (14 modules)
- **Observability:** CloudWatch (alarms, dashboard, Log Insights), SNS, X-Ray-ready structured JSON logs
- **Security tooling:** WAF, GuardDuty, AWS Config, CloudTrail, IAM Access Analyzer, VPC Flow Logs, ECR scan
- **CI/CD:** GitHub Actions
- **Containers:** Docker multi-target builds, ECS Fargate
