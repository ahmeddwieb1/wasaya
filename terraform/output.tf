# output "alb_dns_name" {
#   value = aws_lb.test.dns_name
# }

output "rds_hostname" {
  description = "RDS hostname only"
  value       = aws_db_instance.wasaya.address
}