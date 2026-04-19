#!/usr/bin/env bash
# ShopCloud — DevOps/Infra commits (~17 commits)
# Run by: YOU (Rasha)
#
# This is the FIRST script that runs. It bootstraps the repo locally,
# creates the devops/infra commits, and pushes to GitHub.
#
# Usage:
#   1. cd /c/Users/sarma/OneDrive/Desktop/shopCloud
#   2. git config user.name  "Rasha Alannan"        (or whatever you want shown)
#   3. git config user.email "rasha_alannan@live.com"  (must match your GitHub email)
#   4. bash commit-devops.sh
#   5. git remote add origin https://github.com/ralphnasr/DevOps.git
#   6. git branch -M main
#   7. git push -u origin main

set -e
cd "$(dirname "$0")"

# ── 1. Initialize repo ──
git init
git add .gitignore
git commit -m "chore: initialize repository with .gitignore"

# ── 2. Phase 1 deliverables ──
git add ShopCloud_Phase1_Report.pdf \
  shopcloud_diagram_bottom.png \
  shopcloud_diagram_top.png \
  shopcloud_final_architecture.png \
  generate_diagram.py \
  generate_report.py \
  presentation_guide.txt
git commit -m "docs: add Phase 1 report, architecture diagrams, and generator scripts"

# ── 12. Docker + requirements ──
git add app/Dockerfile \
  app/.dockerignore \
  app/requirements.txt \
  docker-compose.yml
git commit -m "build: add multi-target Dockerfile, docker-compose, and requirements"

# ── 14. Terraform modules (all 12) ──
git add terraform/modules/vpc/ \
  terraform/modules/security_groups/ \
  terraform/modules/ecr/ \
  terraform/modules/ecs/ \
  terraform/modules/alb/ \
  terraform/modules/rds/ \
  terraform/modules/elasticache/ \
  terraform/modules/cognito/ \
  terraform/modules/invoice_pipeline/ \
  terraform/modules/edge/ \
  terraform/modules/bastion/ \
  terraform/modules/ssm/
git commit -m "infra: add 12 Terraform modules (vpc, sg, ecr, ecs, alb, rds, redis, cognito, invoice, edge, bastion, ssm)"

# ── 15. Terraform root configuration ──
git add terraform/main.tf \
  terraform/variables.tf \
  terraform/outputs.tf \
  terraform/providers.tf \
  terraform/locals.tf \
  terraform/data.tf
git commit -m "infra: add Terraform root config with prod and dev environment wiring"

# ── 16. CI/CD pipelines + deploy scripts ──
git add .github/workflows/dev.yml \
  .github/workflows/prod.yml \
  scripts/deploy.sh \
  scripts/deploy-frontend.sh
git commit -m "ci: add GitHub Actions pipelines (dev + prod) and deployment scripts"

# ── 17. README ──
git add README.md
git commit -m "docs: add comprehensive README with architecture, usage, and rollback procedures"

# ── 19. Audit fix: Terraform security + connectivity ──
git add terraform/modules/ecs/main.tf \
  terraform/modules/ecs/variables.tf \
  terraform/modules/ecs/outputs.tf \
  terraform/modules/ssm/outputs.tf \
  terraform/modules/alb/main.tf \
  terraform/modules/security_groups/main.tf \
  terraform/modules/invoice_pipeline/outputs.tf \
  terraform/modules/cognito/main.tf \
  terraform/modules/cognito/variables.tf \
  terraform/main.tf
git commit -m "infra: wire SSM secrets to ECS tasks, add HTTPS listener, scope IAM, fix ElastiCache SG, parameterize Cognito URLs"

# ── 25. Phase 2 deploy readiness fixes ──
git add terraform/outputs.tf \
  terraform/modules/edge/main.tf \
  terraform/main.tf \
  terraform/locals.tf
git commit -m "fix(infra): export Cognito + edge outputs for deploy-frontend.sh, fix WAF inline-block syntax, terraform fmt"

# ── 26. Single-command deploy wrapper ──
git add deploy.sh
git commit -m "feat(deploy): add root deploy.sh wrapping terraform apply + service deploy + frontend per master plan §14"

# ── 27. Automated rollback workflow + prod smoke test ──
git add .github/workflows/rollback.yml \
  .github/workflows/prod.yml
git commit -m "ci: add rollback workflow (manual dispatch) and post-deploy smoke test + auto-rollback on failure in prod.yml"

# ── 38. Audit: kill dev fallbacks + close Terraform deployability gaps ──
git add app/shared/config.py \
  app/shared/auth.py \
  app/services/checkout/service.py \
  app/entrypoints/catalog.py \
  app/entrypoints/admin.py \
  app/entrypoints/checkout.py \
  app/entrypoints/cart.py \
  app/entrypoints/combined.py \
  frontend/js/auth.js \
  app/tests/conftest.py \
  app/tests/test_admin.py \
  app/tests/test_cart.py \
  app/scripts/seed_data.py \
  terraform/modules/ecs/main.tf \
  terraform/modules/ecs/variables.tf \
  terraform/modules/ecs/outputs.tf \
  terraform/modules/cognito/variables.tf \
  terraform/variables.tf \
  terraform/main.tf \
  terraform/providers.tf \
  terraform/terraform.tfvars.example \
  .gitignore \
  .github/workflows/prod.yml \
  .github/workflows/dev.yml \
  scripts/deploy.sh \
  deploy.sh
git commit -m "audit: kill dev fallbacks + close Terraform deployability gaps — hard-fail in prod when Cognito/SQS/config missing (config validate_prod on startup, auth guards for customer+admin pools, SQS publish), frontend dev-login locked to localhost, Terraform migrate task def + ECR repo + Cognito callback wiring + S3 remote backend + tfvars template, CI/CD builds migrate image and runs migrations via aws ecs run-task with exit-code check, root deploy.sh uses two-phase apply to inject real CloudFront domain into Cognito; 32/32 tests still pass"

# ── 40. CI/CD: GitHub Actions OIDC + scoped IAM bootstrap ──
git add setup-cicd.sh \
  .gitignore
git commit -m "ci: add setup-cicd.sh (idempotent OIDC + scoped IAM bootstrap for GitHub Actions); allow terraform.tfvars in private repo"

# ── 41. Ops scripts: hourly Cognito JWT refresh ──
git add refresh-token.cmd
git commit -m "chore(ops): add refresh-token.cmd to mint a fresh Cognito IdToken for ModHeader-based admin browsing over SSH tunnel"

# ── 46. Invoice Lambda: package native deps + widen invoice_url to TEXT ──
git add terraform/modules/invoice_pipeline/main.tf \
  app/migrations/versions/004_widen_invoice_url.py \
  app/shared/models.py
git commit -m "fix(invoice): bundle Lambda deps via Docker pip-install (terraform null_resource) and widen orders.invoice_url to TEXT (migration 004) — presigned S3 URLs exceeded VARCHAR(500)"

# ── 47. Audit fix: prod RDS HA + snapshots + README reconciliation ──
git add terraform/main.tf \
  README.md
git commit -m "fix(infra+docs): enable prod RDS Multi-AZ + 35-day backups + deletion_protection (was false/0 — violated project HA requirement); reconcile README with deployed state and document invoice BackgroundTask + DLQ ops"

# ── 48. Ops scripts: pause/resume prod between demo sessions ──
git add scripts/pause-prod.sh \
  scripts/resume-prod.sh
git commit -m "ops: add pause-prod.sh / resume-prod.sh — scale ECS to 0 + stop RDS between demos to cut idle burn (idempotent; resume waits for RDS available + ECS stable + 200 OK smoke test)"

# ── Catch terraform.tfvars + any leftover (must be in private repo!) ──
git add -A
git diff --cached --quiet || git commit -m "chore: include terraform.tfvars and remaining untracked files for CI/CD"

echo ""
echo "== DevOps commits done =="
git log --oneline | head -20
