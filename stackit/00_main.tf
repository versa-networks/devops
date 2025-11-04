terraform {
  required_providers {
    stackit = {
      source  = "stackitcloud/stackit"
      version = ">=0.50.0"
    }
  }
}

provider "stackit" {
  default_region        = var.default_region
  service_account_token = var.service_account_token
  # service_account_key_path = var.service_account_key_path
  # enable_beta_resources = true
}