"""
L3 — route
Writes the enriched ticket JSON to the correct S3 prefix based on
the `severity` field added by the classify Lambda.

Routing map:
  urgent  → s3://<bucket>/urgent/<ticket_id>.json
  normal  → s3://<bucket>/normal/<ticket_id>.json
  low     → s3://<bucket>/low/<ticket_id>.json
"""
import json
import os

import boto3

s3 = boto3.client("s3")

BUCKET      = os.environ["BUCKET_NAME"]
PREFIX_MAP  = {"urgent": "urgent/", "normal": "normal/", "low": "low/"}


def lambda_handler(event, context):
    severity  = event["severity"]
    ticket_id = event.get("ticket_id", "unknown")

    prefix  = PREFIX_MAP.get(severity, "unknown/")
    s3_key  = f"{prefix}{ticket_id}.json"

    s3.put_object(
        Bucket       = BUCKET,
        Key          = s3_key,
        Body         = json.dumps(event, indent=2),
        ContentType  = "application/json",
    )

    return {
        **event,
        "s3_bucket": BUCKET,
        "s3_key":    s3_key,
        "s3_prefix": prefix,
        "routed_by": "route-lambda",
    }
