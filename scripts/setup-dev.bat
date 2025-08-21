@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    Development Environment Setup
echo ========================================
echo.
echo This script will install:
echo - AWS CLI
echo - Python 3.11 or later
echo - Node.js (for React development)
echo - Git
echo - Docker
echo - AWS SAM CLI
echo - Configure AWS credentials [requires aws cli role secrets]
echo - Clone GitLab project and install dependencies
echo.

pause

:: Check if running as administrator
 net session >nul 2>&1
 if %errorLevel% neq 0 (
   echo ERROR: This script must be run as Administrator!
   echo Please right-click and select "Run as administrator"
   pause
    exit /b 1
 )

echo ========================================
echo    Step 1: Installing Chocolatey
echo ========================================
echo.

REM Check if Chocolatey is installed
choco --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing Chocolatey package manager...
    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    
    if !errorLevel! neq 0 (
        echo ERROR: Failed to install Chocolatey
        pause
        exit /b 1
    )
    
    REM Refresh environment variables
    call refreshenv
    echo Chocolatey installed successfully!
) else (
    echo Chocolatey is already installed.
)

echo.

echo Checking Python installation...
 
:: Check if python command exists
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    goto :install_python
) 
:: Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i 
  :: Extract major and minor version numbers
  for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
     set MAJOR=%%a
     set MINOR=%%b
  ) 
echo Found Python %PYTHON_VERSION%
:: Check if version is 3.11 or later
if %MAJOR% lss 3 (
    echo Python version is too old. Need Python 3.11 or later.
    goto :install_python
)
if %MAJOR% equ 3 (
   if %MINOR% lss 11 (
       echo Python version is too old. Need Python 3.11 or later.
       goto :install_python
    )
) 
echo Python %PYTHON_VERSION% meets requirements (3.11+)
goto :end

:install_python
echo ========================================
echo    Step 2: Installing Python 3.11
echo ========================================
echo.


echo Installing Python 3.11...
choco install python311 -y
    
if !errorLevel! neq 0 (
	echo ERROR: Failed to install Python 3.11
	pause
	exit /b 1
)
    
    call refreshenv
    echo Python 3.11 installed successfully!
) else (
    echo Python 3.11 is already installed.
)
:end
echo.

echo ========================================
echo    Step 3: Installing Node.js
echo ========================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing Node.js...
    choco install nodejs -y
    
    if !errorLevel! neq 0 (
        echo ERROR: Failed to install Node.js
        pause
        exit /b 1
    )
    
    call refreshenv
    echo Node.js installed successfully!
) else (
    echo Node.js is already installed.
)

echo.

echo ========================================
echo    Step 4: Installing AWS CLI
echo ========================================
echo.

REM Check if AWS CLI is installed
aws --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing AWS CLI...
    choco install awscli -y
    
    if !errorLevel! neq 0 (
        echo ERROR: Failed to install AWS CLI
        pause
        exit /b 1
    )
    
    call refreshenv
    echo AWS CLI installed successfully!
) else (
    echo AWS CLI is already installed.
)

echo.

echo ========================================
echo    Step 6: Configuring AWS CLI
echo ========================================
echo.

echo Please provide your AWS credentials:
echo.

set /p AWS_ACCESS_KEY_ID="Enter AWS Access Key ID: "
set /p AWS_SECRET_ACCESS_KEY="Enter AWS Secret Access Key: "
set /p AWS_DEFAULT_REGION="Enter AWS Default Region (e.g., us-east-1): "

if "!AWS_ACCESS_KEY_ID!"=="" (
    echo ERROR: AWS Access Key ID cannot be empty
    pause
    exit /b 1
)

if "!AWS_SECRET_ACCESS_KEY!"=="" (
    echo ERROR: AWS Secret Access Key cannot be empty
    pause
    exit /b 1
)

if "!AWS_DEFAULT_REGION!"=="" (
    set AWS_DEFAULT_REGION=us-east-1
    echo Using default region: us-east-1
)

echo.
echo Configuring AWS CLI...

REM Configure AWS CLI
aws configure set aws_access_key_id "!AWS_ACCESS_KEY_ID!"
aws configure set aws_secret_access_key "!AWS_SECRET_ACCESS_KEY!"
aws configure set default.region "!AWS_DEFAULT_REGION!"
aws configure set default.output json

if !errorLevel! neq 0 (
    echo ERROR: Failed to configure AWS CLI
    pause
    exit /b 1
)

echo AWS CLI configured successfully!

REM Test AWS configuration
echo Testing AWS configuration...
aws sts get-caller-identity >nul 2>&1
if !errorLevel! neq 0 (
    echo WARNING: AWS configuration test failed. Please verify your credentials.
) else (
    echo AWS configuration test passed!
)

echo ========================================
echo    Step 4: Installing Docker Desktop
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing Docker Desktop...
    choco install docker-desktop -y
    
    if !errorLevel! neq 0 (
        echo ERROR: Failed to install Docker Desktop
        echo Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop
        pause
    ) else (
        echo Docker Desktop installed successfully!
        echo NOTE: You may need to restart your computer and enable WSL2 for Docker to work properly.
    )
    
    call refreshenv
) else (
    echo Docker is already installed.
)

echo.

echo ========================================
echo    Step 6: Installing AWS SAM CLI
echo ========================================
echo.

REM Check if AWS SAM CLI is installed
sam --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing AWS SAM CLI...
    where pip3 >nul 2>&1
		if !errorLevel! == 0 (
				echo pip3 found. Installing AWS SAM CLI...
				pip3 install aws-sam-cli
				if !errorLevel! == 0 (
					echo SUCCESS: AWS SAM CLI installed via pip3
				)
	)
) else (
    echo AWS SAM CLI is already installed.
)

echo.
:: Install Git using Chocolatey
echo Installing Git ..
:: check if git is installed
git --version > nul 2>&1

if %errorLevel% equ 0 (
	echo Git is already installed
) else (
	echo Installing Git...
	choco install git -y
	git --version > nul 2>&1
	call refreshenv
	if %errorLevel% equ 0 (
		echo Git installation completed
	) else (
		echo Git installation failed
	)
)

echo Your development environment has been set up with:
echo - Python 3.11
echo - Node.js and npm
echo - AWS CLI (configured)
echo - Git


echo ========================================
echo    Step 7: GitLab Project Setup
echo ========================================
echo.
mwinit -k C:\Users\tanimath\.ssh\id_ecdsa.pub
set /p GITLAB_PROJECT_URL="Enter GitLab project URL (e.g., https://gitlab.com/username/project.git): "
set /p PROJECT_DIR="Enter local directory name for the project: "

if "!GITLAB_PROJECT_URL!"=="" (
    echo Skipping GitLab project clone...
    goto :skip_gitlab
)

if "!PROJECT_DIR!"=="" (
    echo ERROR: Project directory name cannot be empty
    pause
    exit /b 1
)

echo.
echo Cloning GitLab project...

REM Create projects directory if it doesn't exist
if not exist "C:\Projects" (
    mkdir "C:\Projects"
)

cd /d "C:\Projects"

REM Clone the project
git clone "!GITLAB_PROJECT_URL!" "!PROJECT_DIR!"

if !errorLevel! neq 0 (
    echo ERROR: Failed to clone GitLab project
    echo Please ensure you have access to the repository and try again manually
    pause
    goto :skip_gitlab
)

cd "!PROJECT_DIR!"

echo GitLab project cloned successfully to C:\Projects\!PROJECT_DIR!

echo ==========================================
echo building project
echo ==========================================

python publish.py > nul 2>&1
if %errorLevel% equ 0 (
		echo Project built successfully
	) else (
		echo Project build failed
	)

echo ========================================
echo    Setup Complete!
echo ========================================
echo.

pause
