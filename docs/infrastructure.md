# Wasaya Infrastructure

## 1. Overview

Wasaya infrastructure is built around AWS, Docker, Terraform, Ansible, and GitLab CI/CD.

The infrastructure is separated into two environments:

* **Development** — a minimal environment centered around a single EC2 instance.
* **Production** — a more structured environment using an Application Load Balancer, Auto Scaling Group, RDS, S3, IAM, and AWS Systems Manager.

The main responsibilities are separated as follows:

| Technology   | Responsibility                                   |
| ------------ | ------------------------------------------------ |
| Terraform    | Provision AWS infrastructure                     |
| Ansible      | Configure EC2 servers                            |
| Docker       | Run application services                         |
| Docker Hub   | Store application images                         |
| GitLab CI/CD | Build and deploy application changes             |
| AWS SSM      | Execute production deployment commands           |
| S3           | Store media and production Compose configuration |
| RDS          | Production MySQL database                        |
| ALB          | Route external traffic to application instances  |
| ASG          | Manage production EC2 capacity                   |

The AWS region currently used by the infrastructure is `eu-west-1`.

---

## 2. Environment Architecture

Wasaya uses separate Terraform roots for development and production:

```text
terraform/
├── dev/
└── prod/
```

The two environments intentionally have different levels of infrastructure.

### Development

Development uses a single public EC2 instance:

```text
Internet
   │
   ▼
EC2
   │
   ├── Backend
   └── Frontend
```

There is no ALB, RDS, private subnet, or Auto Scaling Group in the development Terraform configuration.

### Production

Production uses multiple AWS components:

```text
                         Internet
                            │
                            ▼
                    ┌──────────────┐
                    │     ALB      │
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │              │
                    ▼              ▼
                 EC2/ASG        EC2/ASG
                    │              │
                    └──────┬───────┘
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
                 RDS               S3
```

The production infrastructure is designed around an ALB and an Auto Scaling Group so that application instances can be managed as a group rather than as a single manually managed server.

---

## 3. Terraform

Terraform is the Infrastructure as Code layer of Wasaya.

The project keeps development and production as independent Terraform root modules:

```text
terraform/
├── dev/
│   ├── ec2.tf
│   ├── rtb.tf
│   ├── sg.tf
│   └── vpc.tf
│
└── prod/
    ├── alb.tf
    ├── asg.tf
    ├── ec2.tf
    ├── iam.tf
    ├── output.tf
    ├── rds.tf
    ├── rtb.tf
    ├── s3.tf
    ├── sg.tf
    ├── userdata.sh
    └── vpc.tf
```

There are currently no shared Terraform modules between the environments.

Terraform is responsible for creating the AWS resources and defining their relationships. Server-level configuration is handled separately by Ansible or EC2 user data.

### Responsibility boundary

```text
Terraform
   │
   ├── VPC
   ├── Networking
   ├── Security Groups
   ├── EC2 / Launch Template
   ├── ALB
   ├── Auto Scaling Group
   ├── RDS
   ├── S3
   └── IAM / SSM permissions
```

Terraform state is currently local in the inspected setup. No remote Terraform backend is defined in the repository.

---

# 4. Development Infrastructure

The development environment is intentionally minimal.

## 4.1 VPC

The development environment contains:

* VPC: `11.0.0.0/16`
* One public subnet: `11.0.1.0/24`
* Availability Zone: `eu-west-1a`
* Internet Gateway
* Public route table

Traffic to the internet is routed through the Internet Gateway.

```text
                    Internet
                       │
                       ▼
                 Internet Gateway
                       │
                       ▼
                  Public Subnet
                       │
                       ▼
                    EC2
```

## 4.2 Development EC2

The development environment uses:

* EC2 instance
* Instance type: `t3.micro`
* AMI: `ami-06468be052a4195a6`
* SSH key: `main_SSH`
* Elastic IP
* Public IP assignment

The EC2 instance is the main runtime host for the development environment.

## 4.3 Development Security Group

The development security group allows inbound traffic on:

* TCP `22` — SSH
* TCP `80` — HTTP
* TCP `443` — HTTPS
* TCP `8000` — backend
* TCP `3000` — frontend

Outbound traffic is unrestricted.

The development environment does not contain:

* ALB
* RDS
* NAT Gateway
* private subnets
* production-style Auto Scaling

---

# 5. Production Infrastructure

Production contains the main AWS architecture for Wasaya.

The main components are:

```text
                         Internet
                            │
                            ▼
                         ALB
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
              Backend               Frontend
              :8000                  :3000
                 │                     │
                 └──────────┬──────────┘
                            │
                         EC2 / ASG
                            │
                            ▼
                           RDS
```

S3 is used separately for object storage and deployment configuration.

---

## 5.1 Production VPC

The production Terraform configuration defines:

* VPC: `11.0.0.0/16`
* Public subnet
* Internet Gateway
* Public route table

The current Terraform source references a second production subnet from several resources, including the ALB, ASG, route table, and RDS subnet group.

The intended production topology therefore uses more than one subnet, although the current Terraform source does not completely define that topology.

There are currently no Terraform-managed:

* private subnets
* NAT Gateway
* NAT Instance
* VPC endpoints
* Network ACL resources

---

# 6. Production Security Groups

Production separates network access between the public load balancer, application instances, and database.

## ALB Security Group

The ALB accepts:

```text
Internet
   │
   ├── TCP 80
   └── TCP 443
```

Outbound traffic is unrestricted.

## EC2 Security Group

The EC2 instances accept:

```text
ALB
 │
 ├── TCP 8000 → Backend
 └── TCP 3000 → Frontend
```

SSH on port `22` is also allowed.

The application ports are therefore not directly exposed to the internet through the EC2 security group. Application traffic is expected to come through the ALB.

## RDS Security Group

The database accepts MySQL traffic only from the EC2 security group:

```text
EC2
 │
 └── TCP 3306
        │
        ▼
       RDS
```

This creates a security-group relationship between the application layer and the database layer.

---

# 7. Application Load Balancer

Production uses an internet-facing Application Load Balancer.

The ALB has two target groups.

## Backend Target Group

* Port: `8000`
* Protocol: HTTP
* Health check: `/health`

## Frontend Target Group

* Port: `3000`
* Protocol: HTTP
* Health check: `/`

Both target groups use:

* 30-second health-check interval
* 5-second timeout
* healthy threshold: 2
* unhealthy threshold: 2

## Host-based Routing

The ALB routes traffic according to the requested host:

```text
api.ahmeddwieb.me
        │
        ▼
 Backend Target Group
        │
        ▼
      :8000


wasaya.ahmeddwieb.me
        │
        ▼
 Frontend Target Group
        │
        ▼
      :3000
```

The current Terraform configuration contains an HTTP listener on port `80`.

HTTPS termination is not currently configured through an ACM certificate and HTTPS ALB listener in Terraform.

---

# 8. EC2 and Auto Scaling

Production uses a Launch Template and Auto Scaling Group.

## Launch Template

The Launch Template defines:

* AMI
* `t3.micro` instance type
* SSH key
* EC2 security group
* IAM instance profile
* public IP association
* user data

The Launch Template also receives the RDS hostname from Terraform so that the EC2 bootstrap process can construct the application database configuration.

## Auto Scaling Group

The production ASG is:

```text
Minimum:  1
Desired:  1
Maximum:  4
```

The ASG uses the Launch Template and registers instances with both:

* backend target group
* frontend target group

This means the same EC2 instances can serve both application layers.

The ASG is therefore responsible for the production compute pool while the ALB is responsible for routing traffic to healthy instances.

---

# 9. Production Database

Production uses Amazon RDS with MySQL.

The configured database includes:

* Engine: MySQL
* Version: `8.4`
* Instance class: `db.t3.micro`
* Storage: `20 GB`
* Maximum storage: `100 GB`
* Storage type: `gp3`
* Storage encryption enabled
* Database name: `wasaya`

The application communicates with RDS over MySQL port `3306`.

```text
Application EC2
      │
      │ MySQL :3306
      ▼
   RDS MySQL
```

The database is controlled by its own security group and is intended to be accessed by the application layer rather than directly by external clients.

---

# 10. S3

Wasaya uses an S3 bucket for application storage and deployment configuration.

Bucket:

```text
ahmeddwieb-wasaya-media
```

## Media Storage

The bucket is used for Wasaya media storage.

Public access is blocked through the S3 public access block configuration.

## Temporary Objects

A lifecycle rule applies to objects under:

```text
temp/
```

Incomplete temporary uploads are removed after one day.

## CORS

The bucket allows the application to interact with objects using:

* PUT
* GET
* DELETE

Configured application origins include the local frontend and Wasaya production frontend.

## Deployment Configuration

The same bucket is also used as a configuration channel for production deployment.

GitLab uploads:

```text
docker-compose.prod.yml
```

to:

```text
s3://ahmeddwieb-wasaya-media/docker-compose.yml
```

Production instances retrieve this file during deployment.

This creates a simple configuration flow:

```text
GitLab
   │
   ▼
S3
   │
   ▼
Production EC2
   │
   ▼
docker-compose.yml
```

---

# 11. IAM and Systems Manager

Production EC2 instances use an IAM role and instance profile.

The role provides access required by the application infrastructure, including S3, RDS-related operations, Secrets Manager, and Systems Manager.

The EC2 instances also use:

```text
AmazonSSMManagedInstanceCore
```

This allows GitLab CI/CD to use AWS Systems Manager to execute deployment commands on production instances.

The production deployment flow is therefore:

```text
GitLab
   │
   ▼
AWS CLI
   │
   ▼
Auto Scaling Group
   │
   ▼
EC2 instance IDs
   │
   ▼
AWS Systems Manager
   │
   ▼
EC2
```

---

# 12. Server Provisioning

Wasaya currently has two server configuration mechanisms:

1. Terraform EC2 user data
2. Ansible

They serve different purposes in the current project.

## Terraform User Data

Production user data performs initial instance bootstrap.

One important responsibility is preparing the application configuration from AWS Secrets Manager and constructing the database connection using the RDS hostname.

The general flow is:

```text
New EC2
   │
   ▼
Terraform User Data
   │
   ├── Retrieve configuration
   ├── Prepare /opt/wasaya
   └── Configure application environment
```

## Ansible

Ansible is used for server-level configuration.

The current Ansible role installs and configures Docker-related requirements and prepares the application directory.

---

# 13. Ansible

The Ansible structure is:

```text
ansible/
├── hosts.ini
├── playbook1
└── elwasaya/
    ├── defaults/
    ├── files/
    ├── handlers/
    ├── meta/
    ├── tasks/
    ├── tests/
    └── vars/
```

The inventory currently contains a web host accessed as the Ubuntu user.

## Ansible Provisioning Flow

When the playbook runs, the server is configured approximately as follows:

```text
EC2
 │
 ▼
Ansible
 │
 ├── Install prerequisites
 ├── Configure Docker repository
 ├── Install Docker Engine
 ├── Install Docker Compose plugin
 ├── Enable Docker
 ├── Add Ubuntu user to Docker group
 ├── Create /opt/wasaya
 └── Configure swap
```

The role installs:

* `ca-certificates`
* `curl`
* Docker Engine
* Docker CLI
* containerd
* Docker Buildx
* Docker Compose plugin

It also creates a 1 GB swap file.

---

# 14. Docker Runtime

Docker is the application runtime layer.

The backend image is built from:

```text
python:3.12-slim
```

The image contains:

* Python dependencies
* FastAPI application
* Alembic migrations
* entrypoint script

The backend listens on:

```text
8000
```

The entrypoint performs database migrations before starting Uvicorn.

```text
Container Start
      │
      ▼
Wait
      │
      ▼
Alembic migration
      │
      ▼
Uvicorn
      │
      ▼
0.0.0.0:8000
```

---

# 15. Docker Compose

There are separate Compose definitions for different deployment paths.

## Development Compose

The development Compose configuration runs:

```text
Backend  :8000
Frontend :3000
```

Both services use:

```text
safepulse-network
```

The development Compose file does not define a MySQL service. The database is therefore external to this Compose topology.

## Production Compose

Production Compose also defines:

```text
Backend
Frontend
```

using externally provided images.

The production database is RDS rather than a MySQL container.

## Ansible Compose

The Ansible-managed Compose file represents a different server topology.

It includes:

```text
Backend
   │
   ▼
Local MySQL
```

with a persistent `mysql-data` volume.

The frontend service is currently commented out in that Compose definition.

This means the Ansible Compose definition is primarily a server provisioning/development-oriented topology, while the production Compose definition is based on external AWS infrastructure.

---

# 16. Configuration and Secrets

Wasaya uses several configuration mechanisms depending on the environment.

### Development

Configuration can be supplied through:

```text
.env
```

and GitLab CI variables during deployment.

### Production

Initial production configuration is retrieved from AWS Secrets Manager.

Terraform user data retrieves the secret:

```text
wasaya-prod
```

and writes the resulting configuration to:

```text
/opt/wasaya/.env
```

The RDS hostname is then used to construct the database connection.

The application consumes this environment configuration through its settings layer.

Secrets are not stored as part of the infrastructure documentation.

---

# 17. DNS and Domains

The infrastructure contains references to the following domains:

```text
api.ahmeddwieb.me
wasaya.ahmeddwieb.me
api.dev.ahmeddwieb.me
```

The production ALB uses host-based rules for the main API and frontend domains.

The repository does not contain Terraform-managed DNS records, so DNS ownership and the actual external DNS configuration are outside the infrastructure code currently inspected.

---

# 18. Infrastructure and Deployment Responsibilities

The infrastructure can be understood as a chain of responsibilities:

```text
Terraform
   │
   │ Provision
   ▼
AWS Infrastructure
   │
   │ Configure server
   ▼
Ansible / User Data
   │
   │ Prepare runtime
   ▼
Docker
   │
   │ Run application
   ▼
EC2
   │
   │ Receive traffic
   ▼
ALB
   │
   ▼
Users
```

Production also depends on:

```text
EC2 ───────────────► RDS
 │
 ├─────────────────► S3
 │
 └─────────────────► AWS Systems Manager
```

---

# 19. Infrastructure Lifecycle

A new production environment follows the general lifecycle:

```text
Terraform
    │
    ▼
AWS Resources
    │
    ▼
EC2 Bootstrap
    │
    ▼
Docker Environment
    │
    ▼
Application Deployment
    │
    ▼
ALB
    │
    ▼
Users
```

Application delivery is handled separately by GitLab CI/CD.

The CI/CD system builds the application image, publishes it to Docker Hub, and uses the production deployment mechanism to update running backend containers.

---

# 20. High Availability

Production introduces horizontal capacity through:

* Application Load Balancer
* Auto Scaling Group
* multiple potential EC2 instances
* health checks
* target groups

The architecture allows the ASG to scale from one instance up to four instances.

The ALB continuously evaluates target health and routes traffic to registered healthy targets.

```text
                    ALB
                  /     \
                 ▼       ▼
              EC2 #1   EC2 #2
                 │       │
                 └───┬───┘
                     ▼
                    RDS
```

The current configuration is therefore capable of supporting multiple application instances, while the configured desired capacity is currently one.

---

# 21. Current Infrastructure Status

## Implemented

* AWS infrastructure in `eu-west-1`
* Separate Terraform roots for development and production
* Development VPC
* Development EC2
* Production VPC
* Production ALB
* Production Auto Scaling Group
* Production Launch Template
* Production RDS MySQL
* Production S3 bucket
* IAM roles and instance profile
* AWS Systems Manager integration
* Docker runtime
* Ansible server provisioning
* GitLab-based application deployment
* S3-based production Compose configuration

## Partially Implemented / Transitional

* Production network topology
* Environment parity between Terraform, Ansible, and Compose
* HTTPS termination
* DNS management
* Some server provisioning responsibilities

## Not Currently Implemented in Infrastructure

* Terraform remote state backend
* Terraform CI/CD plan/apply workflow
* CloudWatch infrastructure configuration
* Terraform-managed DNS
* HTTPS ALB listener with ACM certificate
* Automated infrastructure rollback

These items are intentionally kept separate from the core infrastructure description so that the document describes what Wasaya actually runs rather than presenting future infrastructure as already deployed.

---

# 22. Infrastructure Philosophy

The infrastructure follows a separation of responsibilities:

```text
Terraform
    = Infrastructure

Ansible
    = Server Configuration

Docker
    = Application Runtime

GitLab CI/CD
    = Application Delivery

AWS
    = Cloud Platform

S3 / RDS
    = Persistent Services

ALB / ASG
    = Production Availability and Traffic Management
```

This separation allows the application lifecycle and infrastructure lifecycle to evolve independently while keeping the responsibilities of each layer explicit.
