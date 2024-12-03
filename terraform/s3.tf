
resource "aws_s3_bucket" "c14-bandcamp-reports" {
  bucket = "c14-bandcamp-reports"
  acl    = "private"

  tags = {
    Name        = "c14-bandcamp-reports"
    Environment = "Production"
  }
}