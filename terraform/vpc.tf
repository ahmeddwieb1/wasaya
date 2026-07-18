provider "aws" {
  region = "us-east-1"
}
resource "aws_vpc" "mainVPC" {
  cidr_block = "10.0.0.0/16"
}
resource "aws_subnet" "public_1" {
  vpc_id     = aws_vpc.mainVPC.id
  cidr_block = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone = "us-east-1a"
}
resource "aws_internet_gateway" "mainIGW" {
  vpc_id = aws_vpc.mainVPC.id
}
