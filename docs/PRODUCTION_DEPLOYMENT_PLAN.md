# Production Deployment Plan: AWS + Supabase

**Application**: Recipe Management System  
**Architecture**: FastAPI Backend + React Frontend  
**Database**: Supabase (PostgreSQL)  
**Target Cloud**: AWS  
**Date**: 2025-12-02

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Infrastructure Components](#infrastructure-components)
5. [Step-by-Step Deployment](#step-by-step-deployment)
6. [Environment Configuration](#environment-configuration)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Security & Compliance](#security--compliance)
9. [Monitoring & Logging](#monitoring--logging)
10. [Backup & Disaster Recovery](#backup--disaster-recovery)
11. [Cost Estimation](#cost-estimation)
12. [Post-Deployment Checklist](#post-deployment-checklist)

---

## Overview

### Current Stack
- **Backend**: FastAPI (Python) with SQLModel
- **Frontend**: React + Vite + TypeScript
- **Database**: Supabase PostgreSQL (managed)
- **Auth**: JWT tokens
- **Migrations**: Alembic

### Production Stack
- **Database**: Supabase Cloud (PostgreSQL)
- **Backend**: AWS ECS Fargate (containerized)
- **Frontend**: AWS S3 + CloudFront
- **API Gateway**: AWS Application Load Balancer (ALB)
- **Secrets**: AWS Secrets Manager
- **CI/CD**: GitHub Actions + AWS CodePipeline
- **Monitoring**: CloudWatch + X-Ray
- **Domain**: Route 53

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Users                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS
                         │
         ┌───────────────▼────────────────┐
         │     AWS CloudFront (CDN)       │
         │  (Frontend: React App)         │
         └───────────────┬────────────────┘
                         │
         ┌───────────────▼────────────────┐
         │   AWS S3 (Static Assets)       │
         │   - index.html                 │
         │   - JS/CSS bundles             │
         └────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    API Requests                             │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────▼────────────────┐
         │   AWS Route 53 (DNS)           │
         │   api.yourdomain.com           │
         └───────────────┬────────────────┘
                         │
         ┌───────────────▼────────────────┐
         │   AWS ALB (Load Balancer)      │
         │   - SSL/TLS termination        │
         │   - Health checks              │
         └───────────────┬────────────────┘
                         │
         ┌───────────────▼────────────────┐
         │   AWS ECS Fargate              │
         │   ┌─────────────────────────┐  │
         │   │ FastAPI Backend         │  │
         │   │ (Container)             │  │
         │   └─────────────────────────┘  │
         │   - Auto-scaling               │
         │   - High availability          │
         └───────────────┬────────────────┘
                         │
         ┌───────────────▼────────────────┐
         │   Supabase PostgreSQL          │
         │   (Managed Database)           │
         └────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Supporting Services                      │
├─────────────────────────────────────────────────────────────┤
│  AWS Secrets Manager (Environment Variables)                │
│  AWS CloudWatch (Logging & Metrics)                         │
│  AWS X-Ray (Distributed Tracing)                            │
│  AWS S3 (Backup Storage)                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### 1. AWS Account Setup
- [ ] AWS Account with billing enabled
- [ ] AWS CLI installed and configured
- [ ] IAM user with appropriate permissions
- [ ] AWS credentials configured (`aws configure`)

### 2. Supabase Setup
- [ ] Supabase project created
- [ ] Production database URL obtained
- [ ] API keys (anon + service role) obtained
- [ ] Database migrations ready

### 3. Codebase Preparation
- [ ] All tests passing
- [ ] Docker images tested locally
- [ ] Environment variables documented
- [ ] Production-ready configuration

### 4. Domain & SSL
- [ ] Domain name registered (optional: Route 53)
- [ ] SSL certificate (AWS Certificate Manager)

---

## Infrastructure Components

### 1. Supabase (Database)

**Status**: ✅ Already configured (managed service)

**Configuration**:
- Use production Supabase project
- Connection pooling enabled
- Automatic backups configured
- Network security rules set

**Required Information**:
```
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT_ID].supabase.co
SUPABASE_KEY=[anon/public key]
SUPABASE_SERVICE_KEY=[service_role key]
```

**Migration Strategy**:
```bash
# Before deployment, run migrations on production DB
cd backend
export DATABASE_URL="<production-db-url>"
uv run alembic upgrade head
```

---

### 2. Backend: AWS ECS Fargate

**Why Fargate**: Serverless containers, no EC2 management, auto-scaling

#### Step 1: Create Dockerfile

**File**: `backend/Dockerfile`

```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/')"

# Run application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Step 2: Create ECS Task Definition

**File**: `backend/deployment/ecs-task-definition.json`

```json
{
  "family": "recipe-api-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "recipe-api",
      "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/recipe-api:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:recipe-api/database-url"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:recipe-api/secret-key"
        },
        {
          "name": "SUPABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:recipe-api/supabase-url"
        },
        {
          "name": "SUPABASE_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:recipe-api/supabase-key"
        },
        {
          "name": "SUPABASE_SERVICE_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:recipe-api/supabase-service-key"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:recipe-api/openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/recipe-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/ || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

---

### 3. Frontend: S3 + CloudFront

#### Step 1: Update Vite Config for Production

**File**: `frontend/vite.config.ts` (production build)

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable in production
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
        },
      },
    },
  },
  // Update API URL for production
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || 'https://api.yourdomain.com'),
  },
})
```

#### Step 2: Create CloudFront Distribution

**Configuration**:
- Origin: S3 bucket (static website hosting)
- Viewer Protocol: Redirect HTTP to HTTPS
- Default Root Object: `index.html`
- Error Pages: Return `index.html` for 404 (SPA routing)
- Cache Policy: Optimize for React SPA
- Origin Request Policy: None (S3 static)

#### Step 3: Update API Client for Production

**File**: `frontend/src/lib/api-client.ts`

```typescript
// Use environment variable or default to production API
const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }
  // ... rest of the code
}
```

---

### 4. Application Load Balancer (ALB)

**Configuration**:
- **Type**: Application Load Balancer
- **Scheme**: Internet-facing
- **Listeners**:
  - HTTPS (443) → ECS service
  - HTTP (80) → Redirect to HTTPS
- **Target Group**: ECS Fargate service (port 8000)
- **Health Check**: `GET /api/v1/` (200 OK)
- **SSL Certificate**: ACM certificate (your domain)

---

### 5. AWS Secrets Manager

**Secrets to Store**:

1. **DATABASE_URL**: Supabase PostgreSQL connection string
2. **SECRET_KEY**: Strong random JWT secret (256-bit)
3. **SUPABASE_URL**: Supabase project URL
4. **SUPABASE_KEY**: Supabase anon/public key
5. **SUPABASE_SERVICE_KEY**: Supabase service role key
6. **OPENAI_API_KEY**: OpenAI API key

**Create Secrets**:
```bash
aws secretsmanager create-secret \
  --name recipe-api/database-url \
  --secret-string "postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres"

aws secretsmanager create-secret \
  --name recipe-api/secret-key \
  --secret-string "$(openssl rand -hex 32)"

# Repeat for other secrets...
```

---

## Step-by-Step Deployment

### Phase 1: Infrastructure Setup

#### 1.1 Create VPC and Networking

```bash
# Create VPC with public and private subnets
aws cloudformation create-stack \
  --stack-name recipe-api-vpc \
  --template-body file://deployment/cloudformation/vpc.yaml \
  --region us-east-1
```

**File**: `deployment/cloudformation/vpc.yaml` (simplified)

```yaml
Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
  
  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: us-east-1a
  
  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: us-east-1b
  
  InternetGateway:
    Type: AWS::EC2::InternetGateway
  
  NatGateway:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt ElasticIP.AllocationId
      SubnetId: !Ref PublicSubnet1
```

#### 1.2 Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name recipe-api \
  --region us-east-1

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

#### 1.3 Create Secrets in Secrets Manager

```bash
# Database URL
aws secretsmanager create-secret \
  --name recipe-api/database-url \
  --description "Supabase PostgreSQL connection string" \
  --secret-string "$DATABASE_URL"

# JWT Secret Key (generate strong key)
SECRET_KEY=$(openssl rand -hex 32)
aws secretsmanager create-secret \
  --name recipe-api/secret-key \
  --description "JWT secret key for authentication" \
  --secret-string "$SECRET_KEY"

# Supabase credentials
aws secretsmanager create-secret \
  --name recipe-api/supabase-url \
  --secret-string "$SUPABASE_URL"

aws secretsmanager create-secret \
  --name recipe-api/supabase-key \
  --secret-string "$SUPABASE_KEY"

aws secretsmanager create-secret \
  --name recipe-api/supabase-service-key \
  --secret-string "$SUPABASE_SERVICE_KEY"

# OpenAI API Key
aws secretsmanager create-secret \
  --name recipe-api/openai-api-key \
  --secret-string "$OPENAI_API_KEY"
```

#### 1.4 Create IAM Roles

**ECS Task Execution Role** (for pulling images, secrets):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:recipe-api/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

**ECS Task Role** (for application permissions):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### Phase 2: Backend Deployment

#### 2.1 Build and Push Docker Image

```bash
cd backend

# Build Docker image
docker build -t recipe-api:latest .

# Tag for ECR
docker tag recipe-api:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/recipe-api:latest

# Push to ECR
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/recipe-api:latest
```

#### 2.2 Create ECS Cluster

```bash
aws ecs create-cluster \
  --cluster-name recipe-api-cluster \
  --region us-east-1
```

#### 2.3 Register Task Definition

```bash
aws ecs register-task-definition \
  --cli-input-json file://deployment/ecs-task-definition.json \
  --region us-east-1
```

#### 2.4 Create ECS Service

```bash
aws ecs create-service \
  --cluster recipe-api-cluster \
  --service-name recipe-api-service \
  --task-definition recipe-api-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:ACCOUNT_ID:targetgroup/recipe-api-tg/xxx,containerName=recipe-api,containerPort=8000" \
  --region us-east-1
```

#### 2.5 Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name recipe-api-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx \
  --scheme internet-facing \
  --type application \
  --region us-east-1

# Create target group
aws elbv2 create-target-group \
  --name recipe-api-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx \
  --target-type ip \
  --health-check-path /api/v1/ \
  --health-check-interval-seconds 30 \
  --region us-east-1

# Create HTTPS listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

---

### Phase 3: Frontend Deployment

#### 3.1 Create S3 Bucket

```bash
aws s3 mb s3://recipe-app-frontend --region us-east-1

# Enable static website hosting
aws s3 website s3://recipe-app-frontend \
  --index-document index.html \
  --error-document index.html
```

#### 3.2 Build and Deploy Frontend

```bash
cd frontend

# Set production API URL
export VITE_API_URL=https://api.yourdomain.com

# Build for production
npm run build

# Upload to S3
aws s3 sync dist/ s3://recipe-app-frontend \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html"

# Upload index.html with no cache
aws s3 cp dist/index.html s3://recipe-app-frontend/index.html \
  --cache-control "no-cache, no-store, must-revalidate"
```

#### 3.3 Create CloudFront Distribution

```bash
aws cloudfront create-distribution \
  --distribution-config file://deployment/cloudfront-config.json
```

**File**: `deployment/cloudfront-config.json`

```json
{
  "CallerReference": "recipe-app-frontend-2025-12-02",
  "Comment": "Recipe App Frontend Distribution",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-recipe-app-frontend",
        "DomainName": "recipe-app-frontend.s3.us-east-1.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-recipe-app-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000,
    "Compress": true
  },
  "CustomErrorResponses": {
    "Quantity": 1,
    "Items": [
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      }
    ]
  },
  "Enabled": true,
  "PriceClass": "PriceClass_100",
  "ViewerCertificate": {
    "AcmCertificateArn": "arn:aws:acm:us-east-1:ACCOUNT_ID:certificate/xxx",
    "SslSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021"
  }
}
```

---

### Phase 4: Database Migration

#### 4.1 Run Migrations on Production Database

```bash
cd backend

# Set production database URL
export DATABASE_URL="<supabase-production-url>"

# Run migrations
uv run alembic upgrade head

# Verify migration
uv run alembic current
```

#### 4.2 Backup Existing Data (if applicable)

```bash
cd backend
uv run python scripts/db_backup_restore.py dump --output-dir ./backups/pre-production
```

---

### Phase 5: DNS Configuration

#### 5.1 Route 53 Setup (if using AWS)

```bash
# Create hosted zone
aws route53 create-hosted-zone \
  --name yourdomain.com \
  --caller-reference $(date +%s)

# Create A record for API (aliased to ALB)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch file://deployment/route53-api-record.json

# Create A record for Frontend (aliased to CloudFront)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch file://deployment/route53-frontend-record.json
```

---

## Environment Configuration

### Backend Environment Variables

**Production Configuration** (`backend/src/core/config.py`):

```python
# Update CORS origins for production
BACKEND_CORS_ORIGINS: List[str] = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://app.yourdomain.com",
]

# SECRET_KEY should be from Secrets Manager (strong random value)
SECRET_KEY: str = os.getenv("SECRET_KEY", "")
```

### Frontend Environment Variables

**Production Build** (`.env.production`):

```bash
VITE_API_URL=https://api.yourdomain.com
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

**File**: `.github/workflows/deploy.yml`

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: recipe-api
  ECS_SERVICE: recipe-api-service
  ECS_CLUSTER: recipe-api-cluster
  ECS_TASK_DEFINITION: recipe-api-backend

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build, tag, and push image to Amazon ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG ./backend
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

      - name: Download task definition
        run: |
          aws ecs describe-task-definition \
            --task-definition $ECS_TASK_DEFINITION \
            --query taskDefinition > task-definition.json

      - name: Fill in the new image ID in the Amazon ECS task definition
        id: task-def
        uses: aws-actions/amazon-ecs-render-task-definition@v1
        with:
          task-definition: task-definition.json
          container-name: recipe-api
          image: ${{ steps.login-ecr.outputs.registry }}/$ECR_REPOSITORY:${{ github.sha }}

      - name: Deploy Amazon ECS task definition
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ${{ steps.task-def.outputs.task-definition }}
          service: $ECS_SERVICE
          cluster: $ECS_CLUSTER
          wait-for-service-stability: true

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Build frontend
        run: |
          cd frontend
          npm run build
        env:
          VITE_API_URL: https://api.yourdomain.com

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Deploy to S3
        run: |
          aws s3 sync frontend/dist/ s3://recipe-app-frontend \
            --delete \
            --cache-control "public, max-age=31536000, immutable" \
            --exclude "index.html"
          aws s3 cp frontend/dist/index.html s3://recipe-app-frontend/index.html \
            --cache-control "no-cache, no-store, must-revalidate"

      - name: Invalidate CloudFront cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
            --paths "/*"
```

---

## Security & Compliance

### 1. Network Security

- **VPC**: Private subnets for ECS tasks
- **Security Groups**: Restrict inbound to ALB only
- **NAT Gateway**: Outbound internet access for ECS
- **WAF**: Optional Web Application Firewall on ALB

### 2. Secrets Management

- ✅ All secrets in AWS Secrets Manager
- ✅ Secrets rotated regularly
- ✅ IAM roles with least privilege
- ✅ No secrets in code or logs

### 3. SSL/TLS

- ✅ ACM certificates for ALB
- ✅ HTTPS only (HTTP → HTTPS redirect)
- ✅ TLS 1.2+ enforced
- ✅ HSTS headers

### 4. Application Security

- ✅ CORS configured for production domains
- ✅ JWT tokens with secure expiration
- ✅ Input validation on all endpoints
- ✅ Rate limiting (consider AWS WAF)

### 5. Compliance

- **GDPR**: Data encryption at rest and in transit
- **SOC 2**: AWS infrastructure compliance
- **HIPAA**: Not applicable (recipe data)

---

## Monitoring & Logging

### 1. CloudWatch Logs

**ECS Log Groups**:
- `/ecs/recipe-api` - Application logs
- `/aws/ecs/recipe-api-service` - Service events

**Log Retention**: 30 days (adjustable)

### 2. CloudWatch Metrics

**Key Metrics**:
- ECS: CPU utilization, memory utilization
- ALB: Request count, latency, error rate
- Target Group: Healthy/unhealthy hosts

**Alarms**:
- High CPU (>80% for 5 minutes)
- High error rate (>5% for 5 minutes)
- Unhealthy hosts (>1 unhealthy)

### 3. AWS X-Ray

**Enable Distributed Tracing**:
```python
# backend/src/main.py
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.asyncio_support import patch_all

patch_all()

app = FastAPI(
    # ... existing config
    middleware=[
        Middleware(XRayMiddleware, recorder=xray_recorder)
    ]
)
```

### 4. Application Health Checks

**Health Check Endpoint**:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.PROJECT_VERSION
    }
```

---

## Backup & Disaster Recovery

### 1. Database Backups

**Supabase**: Automatic daily backups (retained 7 days)

**Manual Backup**:
```bash
cd backend
uv run python scripts/db_backup_restore.py dump \
  --output-dir ./backups/production-$(date +%Y%m%d)
```

**Automated Backup to S3**:
```bash
# Schedule via AWS EventBridge + Lambda
# Backup daily at 2 AM UTC
```

### 2. Disaster Recovery Plan

**RTO (Recovery Time Objective)**: 4 hours  
**RPO (Recovery Point Objective)**: 24 hours

**Recovery Steps**:
1. Restore database from Supabase backup
2. Redeploy ECS service from latest image
3. Update DNS if needed
4. Verify application health

---

## Cost Estimation

### Monthly AWS Costs (Estimated)

| Service | Usage | Cost |
|---------|-------|------|
| **ECS Fargate** | 2 tasks (512 CPU, 1GB RAM) | $30-50 |
| **Application Load Balancer** | 1 ALB | $20-25 |
| **CloudFront** | 100GB data transfer | $10-15 |
| **S3** | 10GB storage + requests | $1-2 |
| **CloudWatch** | Logs + metrics | $5-10 |
| **Secrets Manager** | 6 secrets | $0.60 |
| **Route 53** | Hosted zone + queries | $1-2 |
| **NAT Gateway** | 100GB data transfer | $32-45 |
| **Data Transfer** | Inter-region | $10-20 |
| **Total** | | **$110-170/month** |

### Supabase Costs

| Plan | Price |
|------|-------|
| **Pro Plan** (recommended) | $25/month |
| Includes: 8GB database, automatic backups, 100GB bandwidth |

### Total Estimated Cost

**AWS**: $110-170/month  
**Supabase**: $25/month  
**Total**: **$135-195/month**

**Note**: Costs vary based on traffic, data transfer, and usage patterns.

---

## Post-Deployment Checklist

### Immediate (Day 1)

- [ ] Verify all endpoints are accessible
- [ ] Test authentication flow
- [ ] Verify database connections
- [ ] Check CloudWatch logs for errors
- [ ] Test frontend → backend communication
- [ ] Verify SSL certificates
- [ ] Test API documentation (Swagger)
- [ ] Run smoke tests

### Week 1

- [ ] Monitor CloudWatch metrics
- [ ] Review application logs
- [ ] Test auto-scaling (load test)
- [ ] Verify backup process
- [ ] Update DNS if needed
- [ ] Set up monitoring alerts
- [ ] Document runbooks

### Month 1

- [ ] Review cost optimization
- [ ] Security audit
- [ ] Performance tuning
- [ ] Update documentation
- [ ] Review disaster recovery plan
- [ ] Team training on production setup

---

## Troubleshooting

### Common Issues

#### 1. ECS Task Won't Start

**Symptoms**: Tasks keep stopping  
**Solutions**:
- Check CloudWatch logs for errors
- Verify secrets are accessible
- Check task definition resources (CPU/memory)
- Verify security group rules

#### 2. Database Connection Issues

**Symptoms**: 500 errors, connection timeouts  
**Solutions**:
- Verify DATABASE_URL in Secrets Manager
- Check Supabase network settings
- Verify NAT Gateway is working
- Check security group allows outbound 5432

#### 3. Frontend Can't Reach Backend

**Symptoms**: CORS errors, 404s  
**Solutions**:
- Verify CORS origins in backend config
- Check ALB health checks
- Verify API URL in frontend build
- Check CloudFront cache settings

---

## Additional Resources

### AWS Documentation
- [ECS Fargate Getting Started](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- [CloudFront Distribution](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/)

### Supabase Documentation
- [Supabase Production Guide](https://supabase.com/docs/guides/platform/going-into-prod)
- [Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres)

### Codebase References
- Backend config: `backend/src/core/config.py`
- Frontend API client: `frontend/src/lib/api-client.ts`
- Dockerfile: `backend/Dockerfile` (to be created)
- Migrations: `backend/migrations/versions/`

---

## Next Steps

1. **Create Dockerfile** for backend
2. **Set up AWS infrastructure** (VPC, ECR, ECS, ALB)
3. **Configure secrets** in Secrets Manager
4. **Build and push** Docker image
5. **Deploy backend** to ECS
6. **Deploy frontend** to S3 + CloudFront
7. **Run database migrations** on production
8. **Set up CI/CD pipeline**
9. **Configure monitoring** and alerts
10. **Test and verify** all functionality

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-02  
**Maintained By**: Development Team


