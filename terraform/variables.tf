variable "db_user" {
  description = "S3 database user name"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "password for the S3 database user"
  type        = string
  sensitive   = true
}

variable "db_sec_group_id" {
  description = "security group id for the S3 database"
  type        = string
  sensitive   = true
}