# ---------------------------------------------------------------------------
# GitHub Actions CI role (OIDC) — deploys the Lambda code from CI.
# ---------------------------------------------------------------------------
# The OIDC identity provider itself is account-global and lives in shared-infra;
# apply shared-infra first, then this role just references it via a data source.
# No long-lived AWS keys in GitHub: the workflow exchanges a short-lived OIDC
# token for temporary creds scoped to exactly the verbs below.
#
# Trust is scoped to one repo and to the main branch only.

variable "github_repo" {
  description = "GitHub repo (owner/name) whose main-branch workflows may assume the CI role"
  type        = string
  default     = "lichfiet/opgd-backend"
}

data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

data "aws_iam_policy_document" "ci_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # main branch only
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "ci" {
  name                 = "ci-opgd-backend-${var.environment}"
  description          = "GitHub Actions CI role for ${var.github_repo} (deploys Lambda code)"
  assume_role_policy   = data.aws_iam_policy_document.ci_trust.json
  max_session_duration = 3600

  tags = {
    Name        = "OPGD CI Role"
    Environment = var.environment
    Project     = "On Point Garage Doors"
  }
}

# Least privilege: push code to this project's Lambda and run the post-deploy
# smoke test. No create/delete, no IAM, no access to other functions.
data "aws_iam_policy_document" "ci_permissions" {
  statement {
    sid    = "DeployLambdaCode"
    effect = "Allow"
    actions = [
      "lambda:UpdateFunctionCode",
      "lambda:PublishVersion",
      "lambda:GetFunction",
      "lambda:GetFunctionConfiguration",
      "lambda:InvokeFunction",
    ]
    resources = [aws_lambda_function.api.arn]
  }
}

resource "aws_iam_role_policy" "ci" {
  name   = "ci-opgd-backend-permissions"
  role   = aws_iam_role.ci.id
  policy = data.aws_iam_policy_document.ci_permissions.json
}

output "ci_role_arn" {
  description = "ARN of the CI role. Set as role-to-assume in the GitHub Actions workflow."
  value       = aws_iam_role.ci.arn
}

# ---------------------------------------------------------------------------
# CI role for the opgd-web repo — deploys the static site build to S3/CloudFront.
# ---------------------------------------------------------------------------
# Lives here (not in opgd-web) because opgd-web has no Terraform of its own;
# this repo owns all OPGD infrastructure including the site bucket/distribution.

variable "github_web_repo" {
  description = "GitHub repo (owner/name) for the web frontend"
  type        = string
  # NOTE: the repo's actual name on GitHub is onpointgaragedoors (renamed from
  # opgd-web; the old remote URL still redirects). OIDC sub claims use the real
  # name, so the trust policy must too.
  default = "lichfiet/onpointgaragedoors"
}

data "aws_iam_policy_document" "web_ci_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_web_repo}:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "web_ci" {
  name                 = "ci-opgd-web-${var.environment}"
  description          = "GitHub Actions CI role for ${var.github_web_repo} (deploys static site)"
  assume_role_policy   = data.aws_iam_policy_document.web_ci_trust.json
  max_session_duration = 3600

  tags = {
    Name        = "OPGD Web CI Role"
    Environment = var.environment
    Project     = "On Point Garage Doors"
  }
}

data "aws_iam_policy_document" "web_ci_permissions" {
  statement {
    sid       = "ListSiteBucket"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.site.arn]
  }

  statement {
    sid    = "SyncSiteObjects"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
    ]
    resources = ["${aws_s3_bucket.site.arn}/*"]
  }

  statement {
    sid     = "InvalidateCdn"
    effect  = "Allow"
    actions = ["cloudfront:CreateInvalidation", "cloudfront:GetInvalidation"]
    # CloudFront IAM supports per-distribution resource ARNs for invalidations.
    resources = [aws_cloudfront_distribution.site.arn]
  }
}

resource "aws_iam_role_policy" "web_ci" {
  name   = "ci-opgd-web-permissions"
  role   = aws_iam_role.web_ci.id
  policy = data.aws_iam_policy_document.web_ci_permissions.json
}

output "web_ci_role_arn" {
  description = "ARN of the web CI role. Set as role-to-assume in opgd-web's GitHub Actions workflow."
  value       = aws_iam_role.web_ci.arn
}
