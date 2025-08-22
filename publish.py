#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Create new Cfn artifacts bucket if not already existing
Build artifacts
Upload artifacts to S3 bucket for deployment with CloudFormation
"""

import os
import sys
import subprocess
import hashlib
import json
import argparse
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import tempfile
import platform
import concurrent.futures
import threading
from functools import partial
import time


class IDPPublisher:
    def __init__(self):
        self.bucket_basename = None
        self.prefix = None
        self.region = None
        self.acl = None
        self.bucket = None
        self.prefix_and_version = None
        self.version = None
        self.public_sample_udop_model = ""
        self.public = False
        self.main_template = "idp-main.yaml"
        self.use_container_flag = ""
        self.stat_cmd = None
        self.s3_client = None
        self.cf_client = None
        self._print_lock = threading.Lock()  # Thread-safe printing
        
    def thread_safe_print(self, message):
        """Thread-safe print method"""
        with self._print_lock:
            print(message)
        
    def print_usage(self):
        """Print usage information"""
        print("Usage: python3 publish.py <cfn_bucket_basename> <cfn_prefix> <region> [public] [--max-workers N]")
        print("  <cfn_bucket_basename>: Base name for the CloudFormation artifacts bucket")
        print("  <cfn_prefix>: S3 prefix for artifacts")
        print("  <region>: AWS region for deployment")
        print("  [public]: Optional. If 'public', artifacts will be made publicly readable")
        print("  [--max-workers N]: Optional. Maximum number of concurrent workers (default: auto-detect)")
        print("                     Use 1 for sequential processing, higher numbers for more concurrency")

    def check_parameters(self, args):
        """Check and validate input parameters"""
        if len(args) < 3:
            print("Error: Missing required parameters")
            self.print_usage()
            sys.exit(1)
        
        # Parse arguments
        self.bucket_basename = args[0]
        self.prefix = args[1].rstrip('/')  # Remove trailing slash
        self.region = args[2]
        
        # Default values
        self.public = False
        self.acl = "bucket-owner-full-control"
        self.max_workers = None  # Auto-detect
        
        # Parse optional arguments
        remaining_args = args[3:]
        i = 0
        while i < len(remaining_args):
            arg = remaining_args[i]
            
            if arg.lower() == 'public':
                self.public = True
                self.acl = "public-read"
                print("Published S3 artifacts will be accessible by public.")
            elif arg == '--max-workers':
                if i + 1 >= len(remaining_args):
                    print("Error: --max-workers requires a number")
                    self.print_usage()
                    sys.exit(1)
                try:
                    self.max_workers = int(remaining_args[i + 1])
                    if self.max_workers < 1:
                        print("Error: --max-workers must be at least 1")
                        sys.exit(1)
                    print(f"Using {self.max_workers} concurrent workers")
                    i += 1  # Skip the next argument (the number)
                except ValueError:
                    print("Error: --max-workers must be followed by a valid number")
                    self.print_usage()
                    sys.exit(1)
            else:
                print(f"Warning: Unknown argument '{arg}' ignored")
            
            i += 1
        
        if not self.public:
            print("Published S3 artifacts will NOT be accessible by public.")

    def setup_environment(self):
        """Set up environment variables and derived values"""
        os.environ['AWS_DEFAULT_REGION'] = self.region
        
        # Initialize AWS clients
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.cf_client = boto3.client('cloudformation', region_name=self.region)
        
        # Read version
        try:
            with open('./VERSION', 'r') as f:
                self.version = f.read().strip()
        except FileNotFoundError:
            print("Error: VERSION file not found")
            sys.exit(1)
            
        self.prefix_and_version = f"{self.prefix}/{self.version}"
        self.bucket = f"{self.bucket_basename}-{self.region}"
        
        # Set platform-specific commands
        if platform.machine() == "x86_64":
            self.stat_cmd = "stat --format='%Y'"
        else:
            self.stat_cmd = "stat -f %m"
            
        # Set UDOP model path based on region
        if self.region == "us-east-1":
            self.public_sample_udop_model = "s3://aws-ml-blog-us-east-1/artifacts/genai-idp/udop-finetuning/rvl-cdip/model.tar.gz"
        elif self.region == "us-west-2":
            self.public_sample_udop_model = "s3://aws-ml-blog-us-west-2/artifacts/genai-idp/udop-finetuning/rvl-cdip/model.tar.gz"
        else:
            self.public_sample_udop_model = ""

    def check_prerequisites(self):
        """Check for required commands and versions"""
        # Check required commands
        required_commands = ["aws", "sam"]
        for cmd in required_commands:
            if not shutil.which(cmd):
                print(f"Error: {cmd} is required but not installed")
                sys.exit(1)
        
        # Check SAM version
        try:
            result = subprocess.run(['sam', '--version'], capture_output=True, text=True, check=True)
            sam_version = result.stdout.split()[3]  # Extract version from output
            min_sam_version = "1.129.0"
            if self.version_compare(sam_version, min_sam_version) < 0:
                print(f"Error: sam version >= {min_sam_version} is required. (Installed version is {sam_version})")
                print("Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/manage-sam-cli-versions.html")
                sys.exit(1)
        except subprocess.CalledProcessError:
            print("Error: Could not determine SAM version")
            sys.exit(1)
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        min_python_version = "3.12"
        if self.version_compare(python_version, min_python_version) < 0:
            print(f"Error: Python version >= {min_python_version} is required. (Installed version is {python_version})")
            sys.exit(1)

    def version_compare(self, version1, version2):
        """Compare two version strings. Returns -1 if v1 < v2, 0 if equal, 1 if v1 > v2"""
        def normalize(v):
            return [int(x) for x in v.split('.')]
        
        v1_parts = normalize(version1)
        v2_parts = normalize(version2)
        
        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for i in range(max_len):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        return 0

    def setup_artifacts_bucket(self):
        """Create bucket if necessary"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            print(f"Using existing bucket: {self.bucket}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"Creating s3 bucket: {self.bucket}")
                try:
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    
                    # Enable versioning
                    self.s3_client.put_bucket_versioning(
                        Bucket=self.bucket,
                        VersioningConfiguration={'Status': 'Enabled'}
                    )
                except ClientError as create_error:
                    print(f"Failed to create bucket: {create_error}")
                    sys.exit(1)
            else:
                print(f"Error accessing bucket: {e}")
                sys.exit(1)

    def clean_temp_files(self):
        """Clean temporary files in ./lib"""
        print("Delete temp files in ./lib")
        lib_dir = "./lib"
        if os.path.exists(lib_dir):
            for root, dirs, files in os.walk(lib_dir):
                # Remove __pycache__ directories
                for dir_name in dirs[:]:
                    if dir_name == '__pycache__':
                        shutil.rmtree(os.path.join(root, dir_name))
                        dirs.remove(dir_name)
                
                # Remove .pyc files
                for file_name in files:
                    if file_name.endswith('.pyc'):
                        os.remove(os.path.join(root, file_name))

    def get_file_checksum(self, file_path):
        """Get SHA256 checksum of a file"""
        if not os.path.exists(file_path):
            return ""
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def get_directory_checksum(self, directory):
        """Get combined checksum of all files in a directory"""
        if not os.path.exists(directory):
            return ""
        
        checksums = []
        for root, dirs, files in os.walk(directory):
            # Sort to ensure consistent ordering
            dirs.sort()
            files.sort()
            
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    checksums.append(self.get_file_checksum(file_path))
        
        # Combine all checksums
        combined = ''.join(checksums)
        return hashlib.sha256(combined.encode()).hexdigest()

    def get_checksum(self, *paths):
        """Get combined checksum for multiple paths (files or directories)"""
        checksums = []
        for path in paths:
            if os.path.isfile(path):
                checksums.append(self.get_file_checksum(path))
            elif os.path.isdir(path):
                checksums.append(self.get_directory_checksum(path))
        
        combined = ''.join(checksums)
        return hashlib.sha256(combined.encode()).hexdigest()

    def set_checksum(self, directory):
        """Set checksum for a directory in .checksum file"""
        checksum = self.get_checksum(directory)
        checksum_file = os.path.join(directory, '.checksum')
        with open(checksum_file, 'w') as f:
            f.write(checksum)

    def get_stored_checksum(self, directory):
        """Get stored checksum from .checksum file"""
        checksum_file = os.path.join(directory, '.checksum')
        if os.path.exists(checksum_file):
            with open(checksum_file, 'r') as f:
                return f.read().strip()
        return ""

    def needs_rebuild(self, *paths):
        """Check if any of the paths have changed since last build"""
        current_checksum = self.get_checksum(*paths)
        
        # For single directory, check its stored checksum
        if len(paths) == 1 and os.path.isdir(paths[0]):
            stored_checksum = self.get_stored_checksum(paths[0])
            return current_checksum != stored_checksum
        
        # For multiple paths or files, use a global checksum file
        checksum_file = '.build_checksum'
        if os.path.exists(checksum_file):
            with open(checksum_file, 'r') as f:
                stored_checksum = f.read().strip()
            return current_checksum != stored_checksum
        
        return True

    def set_file_checksum(self, path):
        """Set checksum for files in global checksum file"""
        checksum = self.get_checksum(path)
        with open('.build_checksum', 'w') as f:
            f.write(checksum)

    def clean_lib(self):
        """Clean previous build artifacts in ./lib"""
        print("Cleaning previous build artifacts in ./lib/idp_common_pkg")
        lib_pkg_dir = "./lib/idp_common_pkg"
        
        # Remove build directories
        for dir_name in ['build', 'dist']:
            dir_path = os.path.join(lib_pkg_dir, dir_name)
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
        
        # Remove egg-info directories
        for item in os.listdir(lib_pkg_dir):
            if item.endswith('.egg-info'):
                shutil.rmtree(os.path.join(lib_pkg_dir, item))
        
        # Remove __pycache__ directories and .pyc files
        for root, dirs, files in os.walk(lib_pkg_dir):
            for dir_name in dirs[:]:
                if dir_name == '__pycache__':
                    shutil.rmtree(os.path.join(root, dir_name))
                    dirs.remove(dir_name)
            
            for file_name in files:
                if file_name.endswith('.pyc'):
                    os.remove(os.path.join(root, file_name))

    def clean_and_build(self, template_path):
        """Clean previous build artifacts and run sam build"""
        dir_path = os.path.dirname(template_path)
        
        # If dir_path is empty (template.yaml in current directory), use current directory
        if not dir_path:
            dir_path = "."
        
        # Clean previous build artifacts if they exist
        aws_sam_dir = os.path.join(dir_path, '.aws-sam')
        if os.path.exists(aws_sam_dir):
            build_dir = os.path.join(aws_sam_dir, 'build')
            if os.path.exists(build_dir):
                print(f"Cleaning previous build artifacts in {build_dir}")
                shutil.rmtree(build_dir)
        
        # Run sam build
        cmd = ['sam', 'build', '--template-file', template_path]
        if self.use_container_flag:
            cmd.append(self.use_container_flag)
        
        result = subprocess.run(cmd, cwd=dir_path)
        if result.returncode != 0:
            print(f"Error running sam build in {dir_path}")
            sys.exit(1)

    def build_and_package_template(self, directory):
        """Build and package a template directory (thread-safe version)"""
        if self.needs_rebuild(directory):
            self.thread_safe_print(f"BUILDING {directory}")
            
            # Use absolute paths to avoid directory changing issues
            abs_directory = os.path.abspath(directory)
            template_path = os.path.join(abs_directory, "template.yaml")
            
            try:
                # Build the template using absolute paths
                cmd = ['sam', 'build', '--template-file', template_path]
                if self.use_container_flag:
                    cmd.append(self.use_container_flag)
                
                # Clean previous build artifacts if they exist
                aws_sam_dir = os.path.join(abs_directory, '.aws-sam')
                if os.path.exists(aws_sam_dir):
                    build_dir = os.path.join(aws_sam_dir, 'build')
                    if os.path.exists(build_dir):
                        self.thread_safe_print(f"Cleaning previous build artifacts in {build_dir}")
                        shutil.rmtree(build_dir)
                
                result = subprocess.run(cmd, cwd=abs_directory, capture_output=True, text=True)
                if result.returncode != 0:
                    self.thread_safe_print(f"Error building template in {directory}: {result.stderr}")
                    return False
                
                # Package the template
                build_template_path = os.path.join(abs_directory, '.aws-sam', 'build', 'template.yaml')
                packaged_template_path = os.path.join(abs_directory, '.aws-sam', 'packaged.yaml')
                
                cmd = [
                    'sam', 'package',
                    '--template-file', build_template_path,
                    '--output-template-file', packaged_template_path,
                    '--s3-bucket', self.bucket,
                    '--s3-prefix', self.prefix_and_version
                ]
                
                result = subprocess.run(cmd, cwd=abs_directory, capture_output=True, text=True)
                if result.returncode != 0:
                    self.thread_safe_print(f"Error packaging template in {directory}: {result.stderr}")
                    return False
                
            except Exception as e:
                self.thread_safe_print(f"Error building {directory}: {str(e)}")
                return False
            
            self.thread_safe_print(f"DONE {directory}")
            
            # Update the checksum
            self.set_checksum(directory)
            return True
        else:
            self.thread_safe_print(f"SKIPPING {directory} (unchanged)")
            return True

    def build_patterns_concurrently(self, max_workers=None):
        """Build patterns concurrently"""
        patterns = ["patterns/pattern-1", "patterns/pattern-2", "patterns/pattern-3"]
        existing_patterns = [pattern for pattern in patterns if os.path.exists(pattern)]
        
        if not existing_patterns:
            self.thread_safe_print("No patterns found to build")
            return True
        
        self.thread_safe_print(f"Building {len(existing_patterns)} patterns concurrently with {max_workers} workers...")
        
        # Use ThreadPoolExecutor for I/O bound operations (sam build/package)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all pattern build tasks
            future_to_pattern = {
                executor.submit(self.build_and_package_template, pattern): pattern 
                for pattern in existing_patterns
            }
            
            # Wait for all tasks to complete and check results
            all_successful = True
            completed = 0
            total = len(existing_patterns)
            
            for future in concurrent.futures.as_completed(future_to_pattern):
                pattern = future_to_pattern[future]
                completed += 1
                try:
                    success = future.result()
                    if not success:
                        self.thread_safe_print(f"Failed to build pattern: {pattern}")
                        all_successful = False
                    else:
                        self.thread_safe_print(f"Progress: {completed}/{total} patterns completed")
                except Exception as e:
                    self.thread_safe_print(f"Exception building pattern {pattern}: {str(e)}")
                    all_successful = False
        
        return all_successful

    def build_options_concurrently(self, max_workers=None):
        """Build options concurrently"""
        options = ["options/bda-lending-project", "options/bedrockkb"]
        existing_options = [option for option in options if os.path.exists(option)]
        
        if not existing_options:
            self.thread_safe_print("No options found to build")
            return True
        
        self.thread_safe_print(f"Building {len(existing_options)} options concurrently with {max_workers} workers...")
        
        # Use ThreadPoolExecutor for I/O bound operations (sam build/package)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all option build tasks
            future_to_option = {
                executor.submit(self.build_and_package_template, option): option 
                for option in existing_options
            }
            
            # Wait for all tasks to complete and check results
            all_successful = True
            completed = 0
            total = len(existing_options)
            
            for future in concurrent.futures.as_completed(future_to_option):
                option = future_to_option[future]
                completed += 1
                try:
                    success = future.result()
                    if not success:
                        self.thread_safe_print(f"Failed to build option: {option}")
                        all_successful = False
                    else:
                        self.thread_safe_print(f"Progress: {completed}/{total} options completed")
                except Exception as e:
                    self.thread_safe_print(f"Exception building option {option}: {str(e)}")
                    all_successful = False
        
        return all_successful

    def generate_config_file_list(self):
        """Generate list of configuration files for explicit copying"""
        config_dir = "config_library"
        file_list = []
        
        for root, dirs, files in os.walk(config_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, config_dir)
                file_list.append(relative_path)
        
        return sorted(file_list)

    def upload_config_library(self):
        """Upload configuration library to S3"""
        print("UPLOADING config_library to S3")
        config_dir = "config_library"
        
        if not os.path.exists(config_dir):
            print(f"Warning: {config_dir} directory not found")
            return
        
        print("Uploading configuration library to S3")
        
        # Upload all files in config_library
        for root, dirs, files in os.walk(config_dir):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, config_dir)
                s3_key = f"{self.prefix_and_version}/config_library/{relative_path}"
                
                try:
                    self.s3_client.upload_file(
                        local_path,
                        self.bucket,
                        s3_key,
                        ExtraArgs={'ACL': self.acl}
                    )
                except ClientError as e:
                    print(f"Error uploading {local_path}: {e}")
                    sys.exit(1)
        
        print(f"Configuration library uploaded to s3://{self.bucket}/{self.prefix_and_version}/config_library")

    def compute_ui_hash(self):
        """Compute hash of UI folder contents"""
        print("Computing hash of ui folder contents")
        ui_dir = "src/ui"
        return self.get_directory_checksum(ui_dir)

    def package_ui(self):
        """Package UI source code"""
        ui_hash = self.compute_ui_hash()
        zipfile_name = f"src-{ui_hash[:16]}.zip"
        
        # Check if we need to rebuild
        existing_zipfiles = [f for f in os.listdir('.aws-sam') if f.startswith('src-') and f.endswith('.zip')]
        
        if existing_zipfiles and existing_zipfiles[0] != zipfile_name:
            print(f"WebUI zipfile name changed from {existing_zipfiles[0]} to {zipfile_name}, forcing rebuild")
            # Remove old zipfile
            for old_zip in existing_zipfiles:
                old_path = os.path.join('.aws-sam', old_zip)
                if os.path.exists(old_path):
                    os.remove(old_path)
        
        zipfile_path = os.path.join('.aws-sam', zipfile_name)
        
        if not os.path.exists(zipfile_path):
            print("PACKAGING src/ui")
            print(f"Zipping source to {zipfile_path}")
            
            with zipfile.ZipFile(zipfile_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                ui_dir = "src/ui"
                for root, dirs, files in os.walk(ui_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, ui_dir)
                        zipf.write(file_path, arcname)
            
            print("Upload source to S3")
            s3_key = f"{self.prefix_and_version}/{zipfile_name}"
            
            try:
                self.s3_client.upload_file(
                    zipfile_path,
                    self.bucket,
                    s3_key,
                    ExtraArgs={'ACL': self.acl}
                )
            except ClientError as e:
                print(f"Error uploading UI zipfile: {e}")
                sys.exit(1)
        
        print(f"WebUI zipfile: {zipfile_name}")
        return zipfile_name

    def build_main_template(self, webui_zipfile):
        """Build and package main template"""
        print("BUILDING main")
        
        if self.needs_rebuild("./src", "./options", "./patterns", "template.yaml"):
            print("Library files in ./lib have changed. All patterns will be rebuilt.")
            
            # Build main template
            self.clean_and_build("template.yaml")
            
            print("PACKAGING main")
            
            # Read the template
            with open('.aws-sam/build/template.yaml', 'r') as f:
                template_content = f.read()
            
            # Get configuration file list
            config_files_list = self.generate_config_file_list()
            config_files_json = json.dumps(config_files_list)
            
            # Get various hashes
            workforce_url_file = "src/lambda/get-workforce-url/index.py"
            a2i_resources_file = "src/lambda/create_a2i_resources/index.py"
            cognito_client_file = "src/lambda/cognito_updater_hitl/index.py"
            
            workforce_url_hash = self.get_file_checksum(workforce_url_file)[:16] if os.path.exists(workforce_url_file) else ""
            a2i_resources_hash = self.get_file_checksum(a2i_resources_file)[:16] if os.path.exists(a2i_resources_file) else ""
            cognito_client_hash = self.get_file_checksum(cognito_client_file)[:16] if os.path.exists(cognito_client_file) else ""
            
            # Replace tokens in template
            from datetime import datetime, timezone
            build_date_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            
            replacements = {
                '<VERSION>': self.version,
                '<BUILD_DATE_TIME>': build_date_time,
                '<PUBLIC_SAMPLE_UDOP_MODEL>': self.public_sample_udop_model,
                '<ARTIFACT_BUCKET_TOKEN>': self.bucket,
                '<ARTIFACT_PREFIX_TOKEN>': self.prefix_and_version,
                '<WEBUI_ZIPFILE_TOKEN>': webui_zipfile,
                '<HASH_TOKEN>': self.get_directory_checksum("./lib")[:16],
                '<CONFIG_LIBRARY_HASH_TOKEN>': self.get_directory_checksum("config_library")[:16],
                '<CONFIG_FILES_LIST_TOKEN>': config_files_json,
                '<WORKFORCE_URL_HASH_TOKEN>': workforce_url_hash,
                '<A2I_RESOURCES_HASH_TOKEN>': a2i_resources_hash,
                '<COGNITO_CLIENT_HASH_TOKEN>': cognito_client_hash
            }
            
            print("Inline edit main template to replace:")
            for token, value in replacements.items():
                print(f"   {token} with: {value}")
                template_content = template_content.replace(token, value)
            
            # Write the modified template to the build directory
            build_packaged_template_path = '.aws-sam/build/packaged.yaml'
            with open(build_packaged_template_path, 'w') as f:
                f.write(template_content)
            
            # Package the template from the build directory
            original_cwd = os.getcwd()
            try:
                os.chdir('.aws-sam/build')
                cmd = [
                    'sam', 'package',
                    '--template-file', 'packaged.yaml',
                    '--output-template-file', '../../.aws-sam/packaged.yaml',
                    '--s3-bucket', self.bucket,
                    '--s3-prefix', self.prefix_and_version
                ]
                
                result = subprocess.run(cmd)
                if result.returncode != 0:
                    print("Error packaging main template")
                    sys.exit(1)
            finally:
                os.chdir(original_cwd)
            
            # Upload the final template
            final_template_key = f"{self.prefix}/{self.main_template}"
            packaged_template_path = '.aws-sam/packaged.yaml'
            
            try:
                self.s3_client.upload_file(
                    packaged_template_path,
                    self.bucket,
                    final_template_key,
                    ExtraArgs={'ACL': self.acl}
                )
            except ClientError as e:
                print(f"Error uploading main template: {e}")
                sys.exit(1)
            
            # Validate the template
            template_url = f"https://s3.{self.region}.amazonaws.com/{self.bucket}/{final_template_key}"
            print(f"Validating template: {template_url}")
            
            try:
                self.cf_client.validate_template(TemplateURL=template_url)
            except ClientError as e:
                print(f"Template validation failed: {e}")
                sys.exit(1)
            
            # Update checksums
            checksum = self.get_checksum("./src", "./options", "./patterns", "template.yaml")
            with open('.build_checksum', 'w') as f:
                f.write(checksum)
        
        else:
            print("SKIPPING main (unchanged)")

    def update_lib_checksum(self):
        """Update lib checksum file to track changes in the library directories"""
        print("Updated lib checksum file to track changes in the library directories")
        lib_checksum = self.get_directory_checksum("./lib")
        with open('.lib_checksum', 'w') as f:
            f.write(lib_checksum)

    def print_outputs(self):
        """Print final outputs"""
        template_url = f"https://s3.{self.region}.amazonaws.com/{self.bucket}/{self.prefix}/{self.main_template}"
        launch_url = f"https://{self.region}.console.aws.amazon.com/cloudformation/home?region={self.region}#/stacks/create/review?templateURL={template_url}&stackName=IDP"
        
        print("OUTPUTS")
        print(f"Template URL (use to update existing stack): {template_url}")
        print(f"1-Click Launch URL (use to launch new stack): {launch_url}")

    def run(self, args):
        """Main execution method"""
        try:
            # Parse and validate parameters
            self.check_parameters(args)
            
            # Set up environment
            self.setup_environment()
            
            # Check prerequisites
            self.check_prerequisites()
            
            # Set up S3 bucket
            self.setup_artifacts_bucket()
            
            # Clean temporary files
            self.clean_temp_files()
            
            # Clean lib artifacts
            self.clean_lib()
            
            # Check if lib has changed
            lib_changed = self.needs_rebuild("./lib")
            if lib_changed:
                print("Library files in ./lib have changed. All patterns will be rebuilt.")
            
            # Build patterns and options concurrently
            print("Building patterns and options concurrently...")
            start_time = time.time()
            
            # Determine optimal number of workers
            if self.max_workers is None:
                # Auto-detect: typically CPU count or a bit less, capped at 4
                import os
                self.max_workers = min(4, (os.cpu_count() or 1) + 1)
                print(f"Auto-detected {self.max_workers} concurrent workers")
            
            # Build patterns concurrently
            patterns_start = time.time()
            patterns_success = self.build_patterns_concurrently(max_workers=self.max_workers)
            patterns_time = time.time() - patterns_start
            
            if not patterns_success:
                print("Error: Failed to build one or more patterns")
                sys.exit(1)
            
            # Build options concurrently
            options_start = time.time()
            options_success = self.build_options_concurrently(max_workers=self.max_workers)
            options_time = time.time() - options_start
            
            if not options_success:
                print("Error: Failed to build one or more options")
                sys.exit(1)
            
            total_build_time = time.time() - start_time
            print(f"Concurrent build completed in {total_build_time:.2f}s (patterns: {patterns_time:.2f}s, options: {options_time:.2f}s)")
            
            # Upload configuration library
            self.upload_config_library()
            
            # Package UI
            webui_zipfile = self.package_ui()
            
            # Build main template
            self.build_main_template(webui_zipfile)
            
            # Update lib checksum
            self.update_lib_checksum()
            
            # Print outputs
            self.print_outputs()
            
            print("Done")
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    if len(sys.argv) < 4:
        publisher = IDPPublisher()
        publisher.print_usage()
        sys.exit(1)
    
    publisher = IDPPublisher()
    publisher.run(sys.argv[1:])


if __name__ == "__main__":
    main()
