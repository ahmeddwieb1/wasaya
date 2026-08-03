output "elastic_ip" {
    value = aws_eip.serverIP.public_ip
}
