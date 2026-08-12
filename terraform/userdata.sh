#!/bin/bash
set -e
# Update package list and install prerequisites
apt-get update -y

# Install Docker
mkdir -p /etc/apt/keyrings
chmod 755 /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod 644 /etc/apt/keyrings/docker.asc

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin unzip curl

# Start Docker
systemctl start docker
systemctl enable docker

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
./aws/install
rm -rf awscliv2.zip aws

# Download and run compose
mkdir -p /opt/wasaya
aws s3 cp s3://ahmeddwieb-wasaya-media/docker-compose.prod.yml /opt/wasaya/docker-compose.yml

#export secret from secret manager
SECRET_JSON=$(aws secretsmanager get-secret-value \
--secret-id wasaya-prod \
--query SecretString \
--output text)
echo "$SECRET_JSON" | jq -r 'to_entries[] | "\(.key)=\(.value)"' > /opt/wasaya/.env

echo "DATABASE_URL=mysql+pymysql://root:rootpassword@${RDS_HOSTNAME}:3306/wasaya" >> /opt/wasaya/.env
echo "BACKEND_BASE_URL=http://api.ahmeddwieb.me" >> /opt/wasaya/.env

cd /opt/wasaya
docker compose pull
docker compose up -d

echo "Setup completed successfully!"