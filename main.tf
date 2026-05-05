provider "aws" {
  region = var.aws_region
}

# ── S3 bucket: one prefix per severity ───────────────────────────────────────

resource "aws_s3_bucket" "tickets" {
  bucket        = var.bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "tickets" {
  bucket                  = aws_s3_bucket.tickets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── Lambda functions (one module call per Lambda) ─────────────────────────────

module "ticket_validate" {
  source        = "./modules/lambda_function"
  function_name = "${var.project_name}-validate"
  source_dir    = "${path.module}/lambdas/validate"
  role_arn      = aws_iam_role.lambda_exec.arn
}

module "ticket_classify" {
  source        = "./modules/lambda_function"
  function_name = "${var.project_name}-classify"
  source_dir    = "${path.module}/lambdas/classify"
  role_arn      = aws_iam_role.lambda_exec.arn
}

module "ticket_route" {
  source        = "./modules/lambda_function"
  function_name = "${var.project_name}-route"
  source_dir    = "${path.module}/lambdas/route"
  role_arn      = aws_iam_role.lambda_exec.arn
  environment_variables = {
    BUCKET_NAME = aws_s3_bucket.tickets.bucket
  }
}
