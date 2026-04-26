#!/usr/bin/env bash
# Build the invoice + bounce-handler Lambda packages so Terraform can read them
# at refresh/plan time. Runs in CI before `terraform plan` and `terraform apply`,
# and locally on Windows from Git Bash before any local apply.
#
# Native deps (psycopg2-binary, fpdf2 → Pillow) ship as Linux x86_64 wheels,
# so we install them inside a Lambda-compatible Docker image and zip THAT.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INVOICE_DIR="$REPO_ROOT/app/invoice"

# Git Bash on Windows needs Windows paths in docker -v mounts.
host_path() {
  if [ -n "${MSYSTEM:-}" ]; then
    cygpath -w "$1"
  else
    echo "$1"
  fi
}

build_invoice() {
  echo "── Building invoice Lambda ──"
  rm -rf "$INVOICE_DIR/build"
  mkdir -p "$INVOICE_DIR/build"
  cp "$INVOICE_DIR/lambda_function.py" "$INVOICE_DIR/build/"

  local mount_build mount_req
  mount_build="$(host_path "$INVOICE_DIR/build")"
  mount_req="$(host_path "$INVOICE_DIR/requirements.txt")"

  MSYS_NO_PATHCONV=1 docker run --rm --platform linux/amd64 \
    -v "${mount_build}:/var/task" \
    -v "${mount_req}:/var/task/requirements.txt" \
    --entrypoint /bin/bash \
    public.ecr.aws/sam/build-python3.12 \
    -c "pip install -r /var/task/requirements.txt -t /var/task --no-cache-dir"
  echo "→ build/ ready"
}

build_bounce() {
  echo "── Building bounce-handler Lambda ──"
  rm -rf "$INVOICE_DIR/bounce_build"
  mkdir -p "$INVOICE_DIR/bounce_build"
  cp "$INVOICE_DIR/bounce_handler.py" "$INVOICE_DIR/bounce_build/"

  local mount_build
  mount_build="$(host_path "$INVOICE_DIR/bounce_build")"

  MSYS_NO_PATHCONV=1 docker run --rm --platform linux/amd64 \
    -v "${mount_build}:/var/task" \
    --entrypoint /bin/bash \
    public.ecr.aws/sam/build-python3.12 \
    -c "pip install psycopg2-binary==2.9.10 -t /var/task --no-cache-dir"
  echo "→ bounce_build/ ready"
}

build_invoice
build_bounce
echo "── Done. ──"
