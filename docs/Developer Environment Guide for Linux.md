# Development Environment Setup Guide

## Step 1: Launch EC2 Instance

### 1.1 Navigate to EC2 Console
1. Log into [AWS Management Console](https://console.aws.amazon.com/)
2. Navigate to EC2 service
3. Click Launch Instance

### 1.2 Configure Instance Settings
Name: genai-idp-dev-environment
AMI Selection:
• **Amazon Linux 2023**
  • Search: "Amazon Linux 2023 AMI"
  • Architecture: 64-bit (x86)
Instance Type:
• Heavy development: t3.xlarge (4 vCPU, 16 GB RAM)

### 1.3 Key Pair Setup
1. Click Create new key pair (or select existing)
2. Name: genai-idp-dev-key
3. Type: RSA
4. Format: .pem
5. Download and save the .pem file securely

### 1.4 Network Settings
Security Group Configuration:
1. Create new security group: genai-idp-dev-sg
2. Add these inbound rules:
   • **SSH**: Port 22, Source: My IP

### 1.5 Storage Configuration
• Size: 30 GiB (minimum 20GB)
• Type: gp3
• Delete on termination: Yes

### 1.6 Launch
Click Launch instance and wait for it to reach "Running" state.

## Step 2: Connect to Your Instance

### Get Connection Info
1. Select your instance in EC2 console
2. Note the Public IPv4 address

### SSH Connection Command

For Amazon Linux 2023:
```bash
# Command Prompt
ssh -i /path/to/genai-idp-dev-key.pem ec2-user@YOUR_INSTANCE_IP

# Windows PowerShell:
ssh -i C:\path\to\genai-idp-dev-key.pem ec2-user@YOUR_INSTANCE_IP
```

## Step 3: Install Development Tools
Once connected, run these commands:

### 3.1 Verify User Data Results

```bash
# Check versions
python3 --version # Should be 3.13.x
aws --version     # Should be aws-cli/2.x
```

### 3.2 Install Build Tools
```bash
# Amazon Linux 2023:
sudo yum groupinstall -y "Development Tools"
sudo yum install -y make gcc gcc-c++ jq
```

### 3.3 Generate an SSH key
```bash
# Run the following command to generate an ECDSA key:
ssh-keygen -t ecdsa -b 521 -C "your_email@example.com"
```

Press Enter to save the key as ~/.ssh/id_ecdsa. Optionally, add a passphrase.

### 3.4 Initialize the key with AWS GitLab
```bash
# Register your SSH public key with GitLab:
mwinit -k ~/.ssh/id_ecdsa.pub
```

### 3.5 Test the connection
```bash
# Verify that you can connect to GitLab over SSH:
ssh -T ssh.gitlab.aws.dev
```

Expected output:
```
Welcome to GitLab, @your-username!
```

### 3.6 Setup Python Environment
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
cd lib/idp_common_pkg
pip install -e .
cd ../..
```

## Step 4: VSCode Remote Development Setup

### 4.1 Install VSCode Extension (Local Machine)
1. Open VSCode on your local computer
2. Install Remote - SSH extension (by Microsoft)

### Clone your repository
Once connected, clone repositories using SSH:
```bash
git clone git@ssh.gitlab.aws.dev:your-group/your-repo.git
```

### 4.2 Connect via VSCode: Update your SSH config
Press Ctrl+Shift+P for commands
Append the following block to your ~/.ssh/config file:

```
Host genai-idp-dev
    HostName YOUR_INSTANCE_PUBLIC_IP
    User ec2-user
    IdentityFile /path/to/genai-idp-dev-key.pem
    Port 22
```

### 4.3 Connect via VSCode
1. Press Ctrl+Shift+P
2. Type "Remote-SSH: Connect to Host"
3. Select "genai-idp-dev"
4. Open folder: /home/ec2-user/genaiic-idp-accelerator

## Step 5: Verify Setup

### Test Development Environment
```bash
# Activate virtual environment
source venv/bin/activate
```

### Test Build Process
```bash
# Test publish script help
./scripts/publish.sh --help

# Test build (this will take 10-15 minutes)
./scripts/publish.sh --build-only --region us-east-1
```
