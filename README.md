# Support Ticket Classifier

**AWS Academy Data Engineering — Module 12, Scenario C**  
Universidad Autónoma de Guadalajara

---

## What this pipeline does

This pipeline simulates the automatic triage system of a customer support department. When a support ticket arrives, instead of a human agent deciding how urgent it is, the pipeline classifies it in seconds and stores it in the right queue on S3.

The classification combines two signals: a **numeric priority score** (0–100, supplied by the ticketing frontend) and **keyword analysis** of the free-text description. This hybrid approach prevents two common failure modes — a high-score administrative ticket being treated as a crisis, and a genuinely urgent ticket with a moderate score being ignored because the customer forgot to set the priority.

### The three Lambdas

**`validate`** is the gatekeeper. It checks that `priority_score` is a number in the 0–100 range, that `description` is non-empty, and that a `customer` field is present. Any ticket that fails these checks triggers the Step Function's Fail state immediately, preventing bad data from reaching downstream systems.

**`classify`** determines severity. It starts from the numeric score:

- score ≥ 70 → base level is `urgent`
- score 40–69 → base level is `normal`
- score < 40 → base level is `low`

It then scans the description for escalating keywords (`urgent`, `down`, `outage`, `crash`, `not working`, etc.) and raises the level by one step per hit. Conversely, de-escalating keywords (`question`, `how to`, `feature request`, etc.) lower the level by one step. The final severity is clamped to the `[low, normal, urgent]` range.

**`route`** writes the fully enriched ticket JSON to the correct S3 prefix: `urgent/`, `normal/`, or `low/`. It adds `s3_bucket`, `s3_key`, and `s3_prefix` fields to the event before returning it, so downstream consumers always know exactly where the file landed.

### Step Function (7 states, 1 Choice, 3 branches)

```
Validate → Classify → Route → ChooseBranch
                                   ├─ severity == "urgent" → TicketUrgent (Succeed)
                                   ├─ severity == "normal" → TicketNormal (Succeed)
                                   └─ severity == "low"    → TicketNormal (Succeed)
                                   (any error at any step) → ValidationFailed (Fail)
```

The state count is exactly 7 (constraint: max 7). The Choice has 3 `StringEquals` rules.  `low` shares the `TicketNormal` Succeed terminal to stay within the limit, which is correct because the S3 routing (the observable side effect) has already happened inside the Route Lambda.

---

## How to deploy

```bash
# 1. Edit backend.tf — replace the bucket name with your bootstrap output
# 2. If your bucket name conflicts, change var.bucket_name in variables.tf

tofu init
tofu apply
```

## How to test

```bash
SFN=$(tofu output -raw state_machine_arn)

# Urgent ticket
aws stepfunctions start-execution --state-machine-arn $SFN \
  --input "$(cat tests/test_urgent.json)"

# Normal ticket
aws stepfunctions start-execution --state-machine-arn $SFN \
  --input "$(cat tests/test_normal.json)"

# Low ticket
aws stepfunctions start-execution --state-machine-arn $SFN \
  --input "$(cat tests/test_low.json)"

# Invalid ticket (should land in Fail state)
aws stepfunctions start-execution --state-machine-arn $SFN \
  --input "$(cat tests/test_invalid.json)"

# Verify S3 routing
aws s3 ls --recursive "s3://$(tofu output -raw bucket_name)/"
```

## Clean up

```bash
tofu destroy   # removes all resources including the S3 bucket (force_destroy = true)
```

## Folder structure

```
support-ticket-classifier/
├── backend.tf                        # Remote state (S3 + DynamoDB lock)
├── main.tf                           # Provider + S3 bucket + 3 Lambda modules
├── iam.tf                            # Lambda role + Step Functions role
├── step_function.tf                  # State machine definition (7 states)
├── variables.tf
├── outputs.tf
├── modules/
│   └── lambda_function/
│       └── main.tf                   # Reusable Lambda module
├── lambdas/
│   ├── validate/lambda_function.py   # L1 — input validation
│   ├── classify/lambda_function.py   # L2 — severity classification
│   └── route/lambda_function.py      # L3 — S3 routing
├── tests/
│   ├── unit/test_lambdas.py          # pytest unit tests (no AWS needed)
│   ├── test_urgent.json
│   ├── test_normal.json
│   ├── test_low.json
│   └── test_invalid.json
└── .github/
    └── workflows/deploy.yml          # CI/CD: unit tests → plan/apply → smoke tests
```

## Constraints checklist

| Constraint | How it is satisfied |
|---|---|
| Exactly 3 Lambdas | `validate`, `classify`, `route` |
| Exactly 1 Choice state | `ChooseBranch` with 3 `StringEquals` rules |
| ≥ 1 Fail state | `ValidationFailed` |
| ≥ 1 Succeed state | `TicketUrgent`, `TicketNormal` |
| ≤ 7 total states | Exactly 7 |
| `tofu apply` only | No console clicks, no manual CLI resource creation |
| `tofu destroy` cleans everything | S3 has `force_destroy = true`; CloudWatch log groups are explicit resources |
| Folder structure matches class | `modules/lambda_function/`, `lambdas/`, etc. |
| No extra services | Only Lambda + Step Functions + S3 (no SNS, SQS, DynamoDB, API GW) |
| Each Lambda receives full event and adds fields | All three use `{**event, ...new_fields}` pattern |
