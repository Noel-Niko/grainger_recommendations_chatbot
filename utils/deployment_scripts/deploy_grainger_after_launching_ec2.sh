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

# Step 1: Deploy CloudFormation Stack
echo "Deploying CloudFormation stack..."
aws cloudformation create-stack --stack-name $STACK_NAME --template-body file://$CLOUDFORMATION_TEMPLATE --capabilities CAPABILITY_IAM

echo "Deployment complete!"
