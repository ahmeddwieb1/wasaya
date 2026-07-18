resource "aws_route_table" "publicRT" {   
  vpc_id = aws_vpc.mainVPC.id
    route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.mainIGW.id
    }
}
resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.publicRT.id
}