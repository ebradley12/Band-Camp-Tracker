# # Security group to allow traffic on the postresql 5432 port
# resource "aws_security_group" "c14-bandcamp-sg" {
#   description = "Allow access to PostgreSQL from anywhere"

#   egress {
#     cidr_blocks = ["0.0.0.0/0"]
#     from_port   = "0"
#     protocol    = "-1"
#     self        = "false"
#     to_port     = "0"
#   }

#   ingress {
#     cidr_blocks = ["0.0.0.0/0"]
#     from_port   = "5432"
#     protocol    = "tcp"
#     self        = "false"
#     to_port     = "5432"
#   }

#   name   = "c14-bandcamp-sg"
#   vpc_id = "vpc-0344763624ac09cb6"
# }

# # The RDS database instance 
# resource "aws_db_instance" "c14-bandcamp-db" {
#   allocated_storage                     = "20"
#   auto_minor_version_upgrade            = "true"
#   availability_zone                     = "eu-west-2c"
#   backup_retention_period               = "7"
#   backup_target                         = "region"
#   backup_window                         = "23:45-00:15"
#   ca_cert_identifier                    = "rds-ca-rsa2048-g1"
#   copy_tags_to_snapshot                 = "false"
#   customer_owned_ip_enabled             = "false"
#   db_name                               = "c14_bandcamp_db"
#   db_subnet_group_name                  = "c14-public-subnet-group"
#   dedicated_log_volume                  = "false"
#   deletion_protection                   = "false"
#   engine                                = "postgres"
#   engine_lifecycle_support              = "open-source-rds-extended-support-disabled"
#   engine_version                        = "16.3"
#   iam_database_authentication_enabled   = "false"
#   identifier                            = "c14-bandcamp-db"
#   instance_class                        = "db.t3.micro"
#   iops                                  = "0"
#   license_model                         = "postgresql-license"
#   maintenance_window                    = "mon:04:11-mon:04:41"
#   max_allocated_storage                 = "0"
#   monitoring_interval                   = "0"
#   multi_az                              = "false"
#   network_type                          = "IPV4"
#   option_group_name                     = "default:postgres-16"
#   parameter_group_name                  = "default.postgres16"
#   performance_insights_enabled          = "true"
#   performance_insights_kms_key_id       = "arn:aws:kms:eu-west-2:129033205317:key/f62d672a-0743-4fd8-acdd-8a434d8fcb7c"
#   performance_insights_retention_period = "7"
#   port                                  = "5432"
#   publicly_accessible                   = "true"
#   skip_final_snapshot                   = "true"
#   storage_encrypted                     = "true"
#   storage_throughput                    = "0"
#   storage_type                          = "gp2"
#   vpc_security_group_ids                = [aws_security_group.c14-bandcamp-sg.id]
#   username                              = var.db_user
#   password                              = var.db_password
# }