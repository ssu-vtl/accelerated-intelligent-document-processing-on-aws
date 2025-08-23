@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    Development Environment Setup
echo ========================================
echo.
echo This script will install:
echo - AWS CLI
echo - Python 3.13 (required for compatibility)
echo - Node.js (for React development)
echo - Git
echo - Docker
echo - AWS SAM CLI
echo - Python dependencies (boto3, numpy 2.3.2)
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
    echo Python is not installed. Installing Python 3.13...
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
:: Check if version is 3.13 or later
if %MAJOR% lss 3 (
    echo Python version is too old. Need Python 3.13 or later.
    goto :install_python
)
if %MAJOR% equ 3 (
   if %MINOR% lss 13 (
       echo Python version is too old. Need Python 3.13 or later.
       goto :install_python
    )
) 
echo Python %PYTHON_VERSION% meets requirements (3.13+)

:install_python
echo ========================================
echo    Step 2: Installing Python 3.13
echo ========================================
echo.

echo Installing Python 3.13...
choco install python313 -y
    
if !errorLevel! neq 0 (
	echo ERROR: Failed to install Python 3.13
	pause
	exit /b 1
)
    
call refreshenv
echo Python 3.13 installed successfully!

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
echo    Step 4.1: Configuring AWS CLI
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
echo    Step 5: Installing Docker Desktop
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
    echo Installing AWS SAM CLI via Chocolatey...
    choco install aws-sam-cli -y
    
    if !errorLevel! neq 0 (
        echo WARNING: Chocolatey installation failed. Trying pip installation...
        python -m pip install aws-sam-cli
        
        if !errorLevel! neq 0 (
            echo ERROR: Failed to install AWS SAM CLI
            echo Please install manually from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
            pause
            exit /b 1
        )
    )
    
    call refreshenv
    
    REM Verify installation and check version
    sam --version >nul 2>&1
    if !errorLevel! equ 0 (
        echo AWS SAM CLI installed successfully!
        echo Checking SAM CLI version...
        for /f "tokens=4" %%i in ('sam --version 2^>^&1') do set SAM_VERSION=%%i
        echo Found SAM CLI version: !SAM_VERSION!
        echo Note: publish.py requires SAM CLI version >= 1.129.0
    ) else (
        echo ERROR: AWS SAM CLI installation verification failed
        pause
        exit /b 1
    )
) else (
    echo AWS SAM CLI is already installed.
    echo Checking SAM CLI version...
    for /f "tokens=4" %%i in ('sam --version 2^>^&1') do set SAM_VERSION=%%i
    echo Found SAM CLI version: !SAM_VERSION!
    echo Note: publish.py requires SAM CLI version >= 1.129.0
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
echo - Python 3.13
echo - Node.js and npm
echo - AWS CLI (configured)
echo - Git
echo - Python dependencies (boto3, numpy 2.3.2)


echo ========================================
echo    Step 7: GitLab Project Setup
echo ========================================
echo.
mwinit -k C:\Users\tanimath\.ssh\id_ecdsa.pub
echo NOTE: This GitLab instance requires SSH authentication.
echo.
set /p GITLAB_PROJECT_URL="Enter GitLab project SSH URL (default: git@ssh.gitlab.aws.dev:genaiic-reusable-assets/engagement-artifacts/genaiic-idp-accelerator.git): "
if "!GITLAB_PROJECT_URL!"=="" (
    set GITLAB_PROJECT_URL=git@ssh.gitlab.aws.dev:genaiic-reusable-assets/engagement-artifacts/genaiic-idp-accelerator.git
    echo Using default SSH URL: !GITLAB_PROJECT_URL!
)
echo Using SSH URL: !GITLAB_PROJECT_URL!
set /p PROJECT_DIR="Enter local directory name for the project (default: idp): "
if "!PROJECT_DIR!"=="" set PROJECT_DIR=idp

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

REM Check if project directory already exists
if exist "!PROJECT_DIR!" (
    echo Project directory C:\Projects\!PROJECT_DIR! already exists
    cd "!PROJECT_DIR!"
    
    REM Check if it's a git repository
    git status >nul 2>&1
    if !errorLevel! equ 0 (
        echo Found existing git repository, skipping clone...
        echo Checking current branch and pulling latest changes...
        
        REM Get current branch
        for /f "tokens=*" %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
        echo Current branch: !CURRENT_BRANCH!
        
        REM Pull latest changes
        git pull origin !CURRENT_BRANCH!
        if !errorLevel! neq 0 (
            echo WARNING: Failed to pull latest changes
        )
        
        REM Ask user which branch to checkout
        echo.
        set /p TARGET_BRANCH="Enter branch to checkout (default: develop): "
        
        if "!TARGET_BRANCH!"=="" (
            set TARGET_BRANCH=develop
            echo Using default branch: develop
        )
        
        REM Checkout target branch if not already on it
        if not "!CURRENT_BRANCH!"=="!TARGET_BRANCH!" (
            echo Checking out branch: !TARGET_BRANCH!
            git checkout !TARGET_BRANCH!
            if !errorLevel! neq 0 (
                echo ERROR: Failed to checkout branch !TARGET_BRANCH!
                echo The branch may not exist or there may be network issues
                pause
            ) else (
                echo Successfully checked out branch !TARGET_BRANCH!
            )
        ) else (
            echo Already on !TARGET_BRANCH! branch
        )
        
        goto :build_project
    ) else (
        echo Directory exists but is not a git repository
        echo Please remove C:\Projects\!PROJECT_DIR! or choose a different directory name
        pause
        goto :skip_gitlab
    )
)

REM Clone the project
git clone "!GITLAB_PROJECT_URL!" "!PROJECT_DIR!"

if !errorLevel! neq 0 (
    echo ERROR: Failed to clone GitLab project
    echo Please ensure you have access to the repository and try again manually
    pause
    goto :skip_gitlab
)

cd "!PROJECT_DIR!"

echo.
echo Repository cloned successfully!
echo.
set /p TARGET_BRANCH="Enter branch to checkout (default: develop): "

if "!TARGET_BRANCH!"=="" (
    set TARGET_BRANCH=develop
    echo Using default branch: develop
)

echo Checking out branch: !TARGET_BRANCH!
git checkout !TARGET_BRANCH!

if !errorLevel! neq 0 (
    echo ERROR: Failed to checkout branch !TARGET_BRANCH!
    echo The branch may not exist or there may be network issues
    pause
) else (
    echo Successfully checked out branch !TARGET_BRANCH!
)

echo GitLab project cloned successfully to C:\Projects\!PROJECT_DIR!

:skip_gitlab
:build_project

echo.
echo ========================================
echo    Step 8: Building Project
echo ========================================
echo.

echo Please provide the required arguments for publish.py:
echo.
set /p BUCKET_NAME="Enter S3 bucket name for artifacts: "
set /p PREFIX="Enter S3 prefix for artifacts (default: idp): "
set /p REGION="Enter AWS region (default: us-east-1): "

if "!BUCKET_NAME!"=="" (
    echo ERROR: S3 bucket name cannot be empty
    pause
    exit /b 1
)

if "!PREFIX!"=="" (
    set PREFIX=idp
    echo Using default prefix: idp
)

if "!REGION!"=="" (
    set REGION=us-east-1
    echo Using default region: us-east-1
)

echo.
echo ========================================
echo    Step 8a: Installing Python Dependencies
echo ========================================
echo.

echo Installing required Python packages for publish.py...
echo Installing editdistance, boto3 and numpy...

python -m pip install --upgrade pip
if !errorLevel! neq 0 (
    echo WARNING: Failed to upgrade pip, continuing anyway...
)

echo Checking Python version for editdistance compatibility...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

echo Installing editdistance...
python -m pip install editdistance==0.8.1
if !errorLevel! neq 0 (
    echo WARNING: Failed to install editdistance 0.8.1 from wheels
    echo Attempting to install Visual Studio Build Tools for source compilation...
    
    REM Check if Visual Studio Build Tools are already installed
    where cl >nul 2>&1
    if !errorLevel! neq 0 (
        echo Installing Microsoft Visual C++ Build Tools...
        choco install visualstudio2022buildtools --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --includeOptional --passive"
        
        if !errorLevel! neq 0 (
            echo ERROR: Failed to install Visual Studio Build Tools via Chocolatey
            echo Please install manually from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
            echo Then run: pip install editdistance --no-binary editdistance
            pause
            exit /b 1
        )
        
        echo Visual Studio Build Tools installed. Refreshing environment...
        call refreshenv
        
        REM Add VS tools to PATH for current session
        call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
    ) else (
        echo Visual Studio Build Tools already available
    )
    
    echo Building editdistance from source...
    python -m pip install editdistance==0.8.1 --no-binary editdistance --force-reinstall
    
    if !errorLevel! neq 0 (
        echo ERROR: Failed to build editdistance from source
        echo This may be due to missing build dependencies
        echo Please ensure Visual Studio Build Tools are properly installed
        echo Manual installation: pip install editdistance --no-binary editdistance
        pause
        exit /b 1
    ) else (
        echo Successfully built and installed editdistance from source
    )
) else (
    echo Successfully installed editdistance 0.8.1
)

python -m pip install boto3
if !errorLevel! neq 0 (
    echo ERROR: Failed to install boto3
    echo Please install boto3 manually: pip install boto3
    pause
    exit /b 1
)

echo Installing numpy 2.3.2...
python -m pip install numpy==2.3.2
if !errorLevel! neq 0 (
    echo ERROR: Failed to install numpy 2.3.2
    echo Please install numpy manually: pip install numpy==2.3.2
    pause
    exit /b 1
)

echo Python dependencies installed successfully!

echo.
echo ========================================
echo    Step 8b: Building Project
echo ========================================
echo.

echo Running publish.py to build the project...
echo Command: python publish.py !BUCKET_NAME! !PREFIX! !REGION!
echo.

python publish.py !BUCKET_NAME! !PREFIX! !REGION!
if !errorLevel! equ 0 (
    echo Project built successfully!
) else (
    echo ERROR: Project build failed
    echo Please check the output above for details
    pause
)

echo ========================================
echo    Setup Complete!
echo ========================================
echo.
echo Your development environment has been set up with:
echo - Python 3.13
echo - Node.js and npm
echo - AWS CLI (configured)
echo - Git
echo - Python dependencies (boto3, numpy 2.3.2)
pause
