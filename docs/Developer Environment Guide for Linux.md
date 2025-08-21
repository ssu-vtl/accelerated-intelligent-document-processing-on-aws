# Development Environment Setup Guide on Linux
# Introduction
This guide establishes a cloud-based development environment using Amazon Linux 2023 on AWS EC2, specifically designed for the GenAI IDP accelerator.

Purpose: Provides a standardized, scalable development infrastructure that combines the familiar VSCode interface on your local machine with powerful cloud compute resources. This approach eliminates local environment configuration issues while ensuring consistent development experiences across team members.

When to use this guide:
• You need a new development environment
• Your current setup has configuration issues
• You prefer cloud-based development with scalable resources
• You want a clean, isolated environment for this project

What you'll achieve: 
A hybrid development setup where your code runs on a pre-configured Amazon Linux EC2 instance while you work through VS Code on your local machine, providing both performance and consistency.

## Step 1: Launch EC2 Instance

# 1.1 Navigate to EC2 Console
1. Log into [AWS Management Console](https://console.aws.amazon.com/)
2. Navigate to EC2 service
3. Click Launch Instance

# 1.2 Configure Instance Settings
Name: genai-idp-dev-environment (example)
AMI Selection:
• **Amazon Linux 2023**
Architecture: 64-bit (x86)
Instance Type:
• Heavy development: t3.2xlarge (8 vCPU, 32 GB RAM)(recommended)
(Other instance types will also work, but this is one we tested)

# 1.3 Key Pair Setup
1. Click Create new key pair (or select existing)
2. Name: genai-idp-dev-key (example)
3. Type: RSA
4. Format: .pem
5. Download and save the .pem file securely

# 1.4 Network Settings
Security Group Configuration:
1. Create new security group: genai-idp-dev-sg (example)
2. Add these inbound rules:
   • **SSH**: Port 22, Source: My IP

# 1.5 Storage Configuration
• Size: 720 GiB (minimum 20GB)
• Type: gp3
• Delete on termination: Yes

# 1.6 Launch
Click Launch instance and wait for it to reach "Running" state.

## Step 2: Connect to Your Instance

# Get Connection Info
1. Select your instance in EC2 console
2. Note the Public IPv4 address

#SSH Connection Command
On local machine:
```bash
# CMD Terminal
ssh -i /path/to/genai-idp-dev-key.pem ec2-user@YOUR_INSTANCE_IP
or
# PowerShell:
ssh -i C:\path\to\genai-idp-dev-key.pem ec2-user@YOUR_INSTANCE_IP
```
## Step 3: Automated Setup Script

# Introduction:
For faster setup, you can use this automated script that installs all required development tools in one go. This 
script configures Python 3.12, AWS CLI, SAM CLI, Node.js, Docker, and development tools with optimized settings.
What it installs: Complete development stack including Python 3.13, AWS CLI v2, SAM CLI, Node.js 18, Docker, 
Miniconda, and enhanced shell configuration.
Usage: Copy the script below, save it as setup.sh, make it executable with chmod +x setup.sh, and run ./setup.sh. 
Reboot required after completion.

Note: This script is an alternative to the manual installation steps.

./scripts/dev_setup.sh
```bash
# Navigate to the project directory
cd /home/ec2-user/genaiic-idp-accelerator

# Run the setup script
./scripts/dev_setup.sh

## Step 4: Install Visual Studio Code
Visit the official website: Go to [https://code.visualstudio.com/](https://code.visualstudio.com/)
Download: Click the "Download for Windows" button
   • This will download the User Installer (recommended for most users)
   • File name will be something like VSCodeUserSetup-x64-1.x.x.exe
Install: 
   • Run the downloaded installer
   • Choose installation location (default is recommended)
Launch: Click "Launch Visual Studio Code" when installation completes

VSCode setup
1. Open VSCode on your local computer
2. Install Remote - SSH extension (by Microsoft)

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

# Clone Repository
bash
git clone https://github.com/aws-samples/genaiic-idp-accelerator.git
cd genaiic-idp-accelerator


# 4.3 Connect via VSCode
1. Press Ctrl+Shift+P
2. Type "Remote-SSH: Connect to Host"
3. Select "genai-idp-dev"
4. Open folder: /home/ec2-user/genaiic-idp-accelerator

## Step 5: Setup

### Setup Python Environment
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

### Test Build Process
```bash
# Test publish script help
./scripts/publish.sh --help

# Test build (this will take 10-15 minutes)
./scripts/publish.sh --build-only --region us-east-1
```
