#!/usr/bin/env bash
set -euo pipefail

# ══════════════════════════════════════════════════════════════
# ShopCloud — One-time AWS GitHub Actions OIDC + IAM Setup
# Idempotent: safe to re-run.
#
# Permissions scope (Option B — scoped, not AdministratorAccess):
#   - PowerUserAccess (all AWS services EXCEPT IAM/Organizations)
#   - Custom inline policy: IAM operations scoped to shopcloud-* names
#   - iam:PassRole scoped to shopcloud-* roles (for ECS task defs)
#
# Usage:  bash setup-cicd.sh <github_user>/<repo_name>
# Example: bash setup-cicd.sh SarmadFarhat/shopcloud
# ══════════════════════════════════════════════════════════════

REPO="${1:-}"
if [[ -z "$REPO" ]]; then
  echo "ERROR: missing argument."
  echo "Usage: bash setup-cicd.sh <github_user>/<repo_name>"
  exit 1
fi

ROLE_NAME="GitHubActionsShopCloud"
SCOPED_POLICY_NAME="ShopCloudCICDIAMScoped"
AWS_REGION="${AWS_REGION:-us-east-1}"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "════════════════════════════════════════════════"
echo "  ShopCloud CI/CD Bootstrap"
echo "  Account: $ACCOUNT_ID  Region: $AWS_REGION"
echo "  GitHub repo: $REPO"
echo "  Permission scope: PowerUser + scoped IAM"
echo "════════════════════════════════════════════════"

# ── 1. OIDC Provider for GitHub Actions ──
echo ""
echo "[1/5] Ensuring GitHub OIDC provider exists..."
PROVIDER_ARN=$(aws iam list-open-id-connect-providers \
  --query "OpenIDConnectProviderList[?contains(Arn,'token.actions.githubusercontent.com')].Arn | [0]" \
  --output text)

if [[ "$PROVIDER_ARN" == "None" || -z "$PROVIDER_ARN" ]]; then
  PROVIDER_ARN=$(aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
    --query "OpenIDConnectProviderArn" --output text)
  echo "  Created: $PROVIDER_ARN"
else
  echo "  Already exists: $PROVIDER_ARN"
fi

# ── 2. Trust Policy ──
echo ""
echo "[2/5] Building trust policy for repo:$REPO ..."
TRUST_FILE="$(pwd)/.cicd-trust.json"
cat > "$TRUST_FILE" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "$PROVIDER_ARN" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
      "StringLike": { "token.actions.githubusercontent.com:sub": "repo:$REPO:*" }
    }
  }]
}
EOF

# ── 3. IAM Role ──
echo ""
echo "[3/5] Creating/updating IAM role $ROLE_NAME ..."
TRUST_PATH_WIN="$(cygpath -w "$TRUST_FILE" 2>/dev/null || echo "$TRUST_FILE")"
if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  echo "  Role exists. Updating trust policy..."
  aws iam update-assume-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-document "file://${TRUST_PATH_WIN}" >/dev/null
else
  aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document "file://${TRUST_PATH_WIN}" \
    --description "GitHub Actions deploys ShopCloud (scoped permissions)" >/dev/null
fi
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query "Role.Arn" --output text)
echo "  Role ARN: $ROLE_ARN"

# ── 4. Attach AWS-managed PowerUserAccess ──
echo ""
echo "[4/5] Attaching PowerUserAccess (all services except IAM/Organizations)..."
aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess >/dev/null
echo "  Attached."

# ── 5. Custom IAM scoped policy ──
echo ""
echo "[5/5] Creating/updating scoped IAM policy ($SCOPED_POLICY_NAME) ..."
SCOPED_POLICY_FILE="$(pwd)/.cicd-scoped-policy.json"
cat > "$SCOPED_POLICY_FILE" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ManageShopcloudRoles",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:UpdateRole",
        "iam:UpdateAssumeRolePolicy",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "iam:TagRole",
        "iam:UntagRole",
        "iam:ListInstanceProfilesForRole",
        "iam:CreateInstanceProfile",
        "iam:DeleteInstanceProfile",
        "iam:AddRoleToInstanceProfile",
        "iam:RemoveRoleFromInstanceProfile",
        "iam:GetInstanceProfile",
        "iam:ListRoleTags",
        "iam:CreateServiceLinkedRole"
      ],
      "Resource": [
        "arn:aws:iam::*:role/shopcloud-*",
        "arn:aws:iam::*:role/aws-service-role/*",
        "arn:aws:iam::*:instance-profile/shopcloud-*"
      ]
    },
    {
      "Sid": "ManageShopcloudPolicies",
      "Effect": "Allow",
      "Action": [
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:GetPolicy",
        "iam:CreatePolicyVersion",
        "iam:DeletePolicyVersion",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions",
        "iam:TagPolicy",
        "iam:UntagPolicy"
      ],
      "Resource": "arn:aws:iam::*:policy/shopcloud-*"
    },
    {
      "Sid": "PassShopcloudRoles",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::*:role/shopcloud-*"
    },
    {
      "Sid": "ReadOnlyIAM",
      "Effect": "Allow",
      "Action": [
        "iam:ListRoles",
        "iam:ListPolicies",
        "iam:ListAccountAliases",
        "iam:GetAccountSummary",
        "iam:ListPolicyTags",
        "iam:ListOpenIDConnectProviders"
      ],
      "Resource": "*"
    }
  ]
}
EOF

POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${SCOPED_POLICY_NAME}"
SCOPED_PATH_WIN="$(cygpath -w "$SCOPED_POLICY_FILE" 2>/dev/null || echo "$SCOPED_POLICY_FILE")"
if aws iam get-policy --policy-arn "$POLICY_ARN" >/dev/null 2>&1; then
  echo "  Policy exists. Creating new version..."
  VERSIONS=$(aws iam list-policy-versions --policy-arn "$POLICY_ARN" --query "Versions[?!IsDefaultVersion].VersionId" --output text)
  for v in $VERSIONS; do
    aws iam delete-policy-version --policy-arn "$POLICY_ARN" --version-id "$v" >/dev/null 2>&1 || true
  done
  aws iam create-policy-version \
    --policy-arn "$POLICY_ARN" \
    --policy-document "file://${SCOPED_PATH_WIN}" \
    --set-as-default >/dev/null
else
  aws iam create-policy \
    --policy-name "$SCOPED_POLICY_NAME" \
    --policy-document "file://${SCOPED_PATH_WIN}" \
    --description "ShopCloud CI/CD: IAM management scoped to shopcloud-* resources" >/dev/null
fi

aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn "$POLICY_ARN" >/dev/null
echo "  Policy attached."

rm -f "$TRUST_FILE" "$SCOPED_POLICY_FILE"

echo ""
echo "════════════════════════════════════════════════"
echo "  AWS side: COMPLETE"
echo "════════════════════════════════════════════════"
echo ""
echo "Role:    $ROLE_ARN"
echo "Trusts:  GitHub repo $REPO (any branch, any workflow)"
echo "Grants:  PowerUserAccess + scoped IAM for shopcloud-* resources"
echo ""
echo "════════════════════════════════════════════════"
echo "  Now do the GitHub side:"
echo "════════════════════════════════════════════════"
echo ""
echo "1. Create the repo at https://github.com/new"
echo "   Owner: $(echo $REPO | cut -d'/' -f1)"
echo "   Name:  $(echo $REPO | cut -d'/' -f2)"
echo "   Visibility: Private (recommended)"
echo "   Do NOT initialize with README/license/.gitignore"
echo ""
echo "2. Initialize and push from this folder:"
echo "   cd $(pwd)"
echo "   git init"
echo "   git add ."
echo "   git commit -m \"chore: initial commit\""
echo "   git branch -M main"
echo "   git remote add origin https://github.com/$REPO.git"
echo "   git push -u origin main"
echo ""
echo "3. Add this secret to GitHub:"
echo "   URL:   https://github.com/$REPO/settings/secrets/actions/new"
echo "   Name:  AWS_ROLE_ARN"
echo "   Value: $ROLE_ARN"
echo ""
echo "4. Watch the first workflow run at:"
echo "   https://github.com/$REPO/actions"
echo ""
