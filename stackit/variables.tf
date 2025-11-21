# --  variables
variable "organization_id" {
  default = "<org id>"
}

variable "project_id" {
  default = "<project id>"
}

variable "service_account_key_path" {
  default = "<path to service account json file>"
}

variable "service_account_token" {
  default = "<token>"
}

variable "default_region" {
  default = "eu01"
}

variable "flavor" {
  type        = string
  description = ""
  default     = "c2i.16"
}

variable "flavorc2i8" {
  type        = string
  description = ""
  default     = "c2i.8"
}

variable "versa_network_id" {
  default = "<network1-id>"
}

variable "versa_mgmt_network_id" {
  default = "<network2-id>"
}
