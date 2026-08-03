resource "aws_instance" "my_server" {
    ami           = "ami-06468be052a4195a6"
    instance_type = "t3.micro"
    subnet_id     = aws_subnet.public_1.id
    security_groups = [aws_security_group.elwasaya_sg.id]
    key_name      = "main_SSH"
}
resource "aws_eip" "serverIP" {
    instance = aws_instance.my_server.id
}
resource "aws_eip_association" "eip_assoc" {
    instance_id   = aws_instance.my_server.id
    allocation_id = aws_eip.serverIP.id
}

