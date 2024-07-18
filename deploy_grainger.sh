#!/bin/bash

# Variables
IMAGE_NAME="grainger_recommendations_chatbot"
REPOSITORY_URI="public.ecr.aws/e2o8h8p3/$IMAGE_NAME"
REGION="us-east-1"
KEY_PAIR_PATH="/Users/noel_niko/Desktop/BedRockAi/AWS/grainger_recs.pem"
EC2_PUBLIC_IP="3.91.229.59"
CLOUDFORMATION_TEMPLATE="stack.yml"
STACK_NAME="grainger-recommendations-stack"
SECURITY_GROUP_ID="sg-0857f1e3a154956da"
MY_PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)

# Step 0: Authorize SSH, HTTP, and HTTPS access
echo "Authorizing SSH, HTTP, and HTTPS access to the EC2 instance..."
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 22 --cidr $MY_PUBLIC_IP/32
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 443 --cidr 0.0.0.0/0

# Step 1: Build the Docker Image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Step 2: Authenticate Docker to ECR
echo "Authenticating Docker to ECR..."
aws ecr-public get-login-password --region $REGION | docker login --username AWS --password-stdin public.ecr.aws

# Step 3: Tag and Push Image to ECR
echo "Tagging Docker image..."
docker tag $IMAGE_NAME:latest $REPOSITORY_URI:latest

echo "Pushing Docker image to ECR..."
docker push $REPOSITORY_URI:latest

# Step 4: SSH into EC2 Instance and Run the Container
echo "Connecting to EC2 instance..."
ssh -i "$KEY_PAIR_PATH" -t ec2-user@$EC2_PUBLIC_IP << EOF
  sudo yum update -y
  sudo yum install -y docker
  sudo service docker start
  sudo usermod -a -G docker ec2-user
  newgrp docker

  # Authenticate Docker to ECR
  echo "Authenticating Docker to ECR on EC2 instance..."
  aws ecr-public get-login-password --region $REGION | docker login --username AWS --password-stdin public.ecr.aws

  # Pull and Run the Docker Container
  echo "Pulling Docker image from ECR..."
  docker pull $REPOSITORY_URI:latest

  echo "Running Docker container..."
  docker run -d -p 80:8505 $REPOSITORY_URI:latest
EOF

# Step 5: Deploy CloudFormation Stack
echo "Deploying CloudFormation stack..."
aws cloudformation create-stack --stack-name $STACK_NAME --template-body file://$CLOUDFORMATION_TEMPLATE --capabilities CAPABILITY_IAM

echo "Deployment complete!"
