# ECR repository to store the reports docker image
resource "aws_ecr_repository" "c14-bandcamp-reports-ecr" {
  name                 = "c14-bandcamp-reports-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ECR policy to only keep the most recent image upload
resource "aws_ecr_lifecycle_policy" "c14-bandcamp-reports-ecr-lifecycle-policy" {
  repository = aws_ecr_repository.c14-bandcamp-reports-ecr.name

  policy = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Keep only the most recently uploaded 3 images",
            "selection": {
                "tagStatus": "any",
                "countType": "imageCountMoreThan",
                "countNumber": 3
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF
}
