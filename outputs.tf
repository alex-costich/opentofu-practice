output "state_machine_arn" {
  description = "ARN of the Step Functions state machine."
  value       = aws_sfn_state_machine.ticket_pipeline.arn
}

output "bucket_name" {
  description = "S3 bucket where classified tickets are stored."
  value       = aws_s3_bucket.tickets.bucket
}
