terraform {
  required_version = ">= 1.8"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  backend "s3" {
    # CAMBIA esto por tu bucket. Lo imprime el output del bootstrap.
    bucket = "demo-cicd-tofu-state-792b3cfb"

    key            = "support-ticket-classifier/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "demo-cicd-tofu-locks"
    encrypt        = true
  }
}
