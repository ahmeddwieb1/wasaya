# resource "aws_launch_template" "example" {
#   name_prefix   = "web-"
#   image_id      = "ami-06468be052a4195a6"
#   instance_type = "t3.micro"
#   key_name      = "main_SSH"
#   network_interfaces {
#     associate_public_ip_address = true
#     security_groups = [aws_security_group.ec2_sg.id]
#   }
#
#   iam_instance_profile {
#     name = aws_iam_instance_profile.s3_profile.name
#   }
#   user_data = base64encode(file("${path.module}/userdata.sh"))
# }

resource "aws_instance" "my_server" {
    ami           = "ami-06468be052a4195a6"
    instance_type = "t3.micro"
    subnet_id     = aws_subnet.public_1.id
    security_groups = [aws_security_group.elwasaya_sg.id]
    key_name      = "main_SSH"
    user_data = base64encode(templatefile("${path.module}/userdata.sh", {
      RDS_HOSTNAME = aws_db_instance.wasaya.address
    }))
}
resource "aws_eip" "serverIP" {
    instance = aws_instance.my_server.id
}
resource "aws_eip_association" "eip_assoc" {
    instance_id   = aws_instance.my_server.id
    allocation_id = aws_eip.serverIP.id
}
resource "aws_iam_instance_profile" "s3_profile" {
  name = "s3_profile"
  role = aws_iam_role.s3_role.name
}