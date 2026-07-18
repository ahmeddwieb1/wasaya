resource "aws_instance" "my_server" {
    ami           = "ami-0b6d9d3d33ba97d99"
    instance_type = "t3.micro"
    subnet_id     = aws_subnet.public_1.id
    security_groups = [aws_security_group.linkin_sg.id]
    key_name      = "main_SSH"
}
resource "aws_eip" "serverIP" {
    instance = aws_instance.my_server.id
}
resource "aws_eip_association" "eip_assoc" {
    instance_id   = aws_instance.my_server.id
    allocation_id = aws_eip.serverIP.id
}

output "elastic_ip" {
    value = aws_eip.serverIP.public_ip
}