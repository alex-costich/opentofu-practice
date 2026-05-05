# State machine — Scenario C: Support Ticket Classifier
#
# States (7 total — constraint satisfied):
#   1. Validate        Task    → Classify | ValidationFailed
#   2. Classify        Task    → Route    | ValidationFailed
#   3. Route           Task    → Choose   | ValidationFailed
#   4. ChooseBranch    Choice  → TicketUrgent | TicketNormal | ValidationFailed
#   5. TicketUrgent    Succeed
#   6. TicketNormal    Succeed (shared by "normal" AND "low" branches)
#   7. ValidationFailed Fail
#
# The Choice has 3 StringEquals rules (urgent / normal / low) which satisfies
# the "2 or 3 branches" requirement. low maps to TicketNormal to stay at 7
# states (adding TicketLow would make 8).

resource "aws_sfn_state_machine" "ticket_pipeline" {
  name     = "${var.project_name}-pipeline"
  role_arn = aws_iam_role.sfn_exec.arn

  definition = jsonencode({
    Comment = "Support Ticket Classifier — Scenario C"
    StartAt = "Validate"

    States = {

      Validate = {
        Type     = "Task"
        Resource = module.ticket_validate.arn
        Next     = "Classify"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "ValidationFailed"
          }
        ]
      }

      Classify = {
        Type     = "Task"
        Resource = module.ticket_classify.arn
        Next     = "Route"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "ValidationFailed"
          }
        ]
      }

      Route = {
        Type     = "Task"
        Resource = module.ticket_route.arn
        Next     = "ChooseBranch"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "ValidationFailed"
          }
        ]
      }

      ChooseBranch = {
        Type = "Choice"
        Choices = [
          {
            Variable     = "$.severity"
            StringEquals = "urgent"
            Next         = "TicketUrgent"
          },
          {
            Variable     = "$.severity"
            StringEquals = "normal"
            Next         = "TicketNormal"
          },
          {
            Variable     = "$.severity"
            StringEquals = "low"
            Next         = "TicketNormal"
          }
        ]
        Default = "ValidationFailed"
      }

      TicketUrgent = {
        Type = "Succeed"
      }

      TicketNormal = {
        Type = "Succeed"
      }

      ValidationFailed = {
        Type  = "Fail"
        Error = "TicketProcessingError"
        Cause = "A Lambda raised an exception or severity was unrecognised."
      }

    }
  })
}
