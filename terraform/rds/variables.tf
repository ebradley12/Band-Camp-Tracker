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