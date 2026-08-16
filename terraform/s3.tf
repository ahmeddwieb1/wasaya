resource "aws_s3_bucket" "wasaya_media" {
    bucket = "ahmeddwieb-wasaya-media"
    force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "wasaya_media" {
  bucket = aws_s3_bucket.wasaya_media.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "wasaya_media" {
  bucket = aws_s3_bucket.wasaya_media.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "GET", "DELETE"]
    allowed_origins = ["http://localhost:3000","https://wasaya.ahmeddwieb.me"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
resource "aws_s3_bucket_lifecycle_configuration" "wasaya_media" {
  bucket = aws_s3_bucket.wasaya_media.id

  rule {
    id = "delete_incomplete_uploads"
    status = "Enabled"

    filter {
      prefix = "temp/"
    }

    expiration {
      days = 1
    }
  }
}