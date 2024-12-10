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

variable "db_name" {
  description = "Name of the database"
  type        = string
}

variable "db_host" {
  description = "Database host endpoint"
  type        = string
}

variable "db_port" {
  description = "Port for the database connection"
  type        = string
  default     = "5432"
}