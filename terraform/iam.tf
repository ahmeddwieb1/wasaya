resource "aws_iam_role_policy" "s3_policy" {
  name = "test_policy"
  role = aws_iam_role.s3_role.id

  policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:HeadObject",
        "secretsmanager:GetSecretValue"
      ],
        Resource = [
          "arn:aws:s3:::ahmeddwieb-wasaya-media",
          "arn:aws:s3:::ahmeddwieb-wasaya-media/*"
        ]
    }
  ]
})
}

resource "aws_iam_role" "s3_role" {
  name = "s3_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}
# iam.tf (إضافة)

resource "aws_iam_role_policy" "rds_policy" {
  name = "wasaya-rds-policy"
  role = aws_iam_role.s3_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:ListTagsForResource"
        ]
        Resource = [
          aws_db_instance.wasaya.arn
        ]
      }
    ]
  })
}