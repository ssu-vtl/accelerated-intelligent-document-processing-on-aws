# Configuration and Customization

## Template.yaml Changes for Custom Configuration Path

### 1. New CloudFormation Parameter
```yaml
CustomConfigPath:
  Type: String
  Default: ""
  Description: >-
    Optional S3 URI to a custom configuration file (e.g., s3://my-bucket/config.yaml).
    When specified, this configuration will override the default pattern configuration.
    Leave empty to use the default configuration library.
```

### 2. Conditional Logic
```yaml
Conditions:
  HasCustomConfigPath: !Not [!Equals [!Ref CustomConfigPath, ""]]
```

### 3. Pattern Integration (All 3 Patterns)
```yaml
# Applied to Pattern1, Pattern2, and Pattern3
ConfigurationDefaultS3Uri: !If
  - HasCustomConfigPath
  - !Ref CustomConfigPath
  - !Sub "s3://${ConfigurationBucket}/config_library/pattern-X/${ConfigPath}/config.yaml"
```

### 4. Least-Privilege IAM Permissions
```yaml
# Replace overly broad permissions with conditional, scoped access
- !If
  - HasCustomConfigPath
  - Effect: Allow
    Action:
      - "s3:GetObject"
    Resource: !Sub
      - "arn:aws:s3:::${Path}"
      - Path: !Select [1, !Split ["s3://", !Ref CustomConfigPath]]
  - !Ref AWS::NoValue
- !If
  - HasCustomConfigPath
  - Effect: Allow
    Action:
      - "s3:ListBucket"
    Resource: !Sub
      - "arn:aws:s3:::${BucketName}"
      - BucketName: !Select [0, !Split ["/", !Select [1, !Split ["s3://", !Ref CustomConfigPath]]]]
  - !Ref AWS::NoValue
```

**Security Benefits:**
- Eliminates wildcard `arn:aws:s3:::*/*` permissions
- Conditional access only when CustomConfigPath is specified
- Converts S3 URI to proper ARN format for IAM resources
- Passes security scans with least-privilege compliance

## Testing Validation: Custom Configuration Loading

The following comprehensive testing procedures were executed to validate that custom configuration files are loaded correctly when specified:

### Test Environment Setup

**Test Configuration File:**
- **Location**: `s3://your-bucket/path/to/config.yaml` (For Example)
- **Size**: 1,509 bytes
- **Format**: YAML with Invoice and Receipt classes
- **Models**: Claude 3.7 Sonnet for OCR, classification, and extraction

**Test Configuration Content:**
```yaml
# SPDX-License-Identifier: MIT-0

ocr:
  backend: "textract"
  model_id: "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
  features:
    - name: LAYOUT
    - name: TABLES
    - name: SIGNATURES

classes:
  - name: Invoice
    description: Commercial document with itemized transaction details between buyer and seller
    attributes:
      - name: InvoiceNumber
        description: Unique invoice identifier
        evaluation_method: EXACT
        attributeType: simple
      - name: InvoiceDate
        description: Invoice issue date
        evaluation_method: EXACT
        attributeType: simple
      - name: TotalAmount
        description: Total amount due
        evaluation_method: NUMERIC_EXACT
        attributeType: simple
      - name: VendorName
        description: Invoice issuer name
        evaluation_method: EXACT
        attributeType: simple

  - name: Receipt
    description: Payment acknowledgment document with transaction details
    attributes:
      - name: TransactionDate
        description: Transaction date
        evaluation_method: EXACT
        attributeType: simple
      - name: Amount
        description: Transaction amount
        evaluation_method: NUMERIC_EXACT
        attributeType: simple
      - name: MerchantName
        description: Business name
        evaluation_method: EXACT
        attributeType: simple

classification:
  model_id: "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

extraction:
  model_id: "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
```

### Test 1: Configuration File Accessibility Validation

**Objective**: Verify the custom configuration file exists and is accessible

**Test Commands:**
```bash
# 1. Verify file exists in S3
aws s3 ls s3://your-bucket/path/to/config.yaml

# Expected Output:
# 2025-08-26 21:41:06       1509 custom-config.yaml

# 2. Download and validate YAML syntax
aws s3 cp s3://your-bucket/path/to/config.yaml /tmp/test-config.yaml
python3 -c "
import yaml
with open('/tmp/test-config.yaml', 'r') as f:
    config = yaml.safe_load(f)
print('✅ YAML syntax is valid')
print(f'Custom classes defined: {len(config[\"classes\"])}')
for cls in config['classes']:
    print(f'  - {cls[\"name\"]}: {cls[\"description\"][:50]}...')
"

# Actual Output:
# ✅ YAML syntax is valid
# Custom classes defined: 2
#   - Invoice: Commercial document with itemized transaction...
#   - Receipt: Payment acknowledgment document with transact...
```

**Result**: ✅ **PASSED** - Configuration file is accessible and has valid YAML syntax with required sections

### Test 2: CloudFormation Template Validation

**Objective**: Verify template syntax and parameter definitions are correct

**Test Commands:**
```bash
# 1. Check CustomConfigPath parameter exists
grep -A 8 "CustomConfigPath:" template.yaml

# Expected Output:
# CustomConfigPath:
#   Type: String
#   Default: ""
#   Description: >-
#     Optional S3 URI to a custom configuration file...

# 2. Check HasCustomConfigPath condition exists
grep -A 2 "HasCustomConfigPath:" template.yaml

# Expected Output:
# HasCustomConfigPath: !Not [!Equals [!Ref CustomConfigPath, ""]]

# 3. Verify conditional IAM permissions
grep -A 10 -B 2 "HasCustomConfigPath" template.yaml | grep -A 8 "Effect: Allow"

# Expected Output shows conditional permissions with proper ARN format
```

**Result**: ✅ **PASSED** 
### Test 3: IAM Permissions Security Validation

**Objective**: Verify least-privilege IAM permissions are properly configured

**Test Commands:**
```bash
# 1. Check for conditional IAM permissions (should exist)
grep -A 15 "Allow reading user-supplied config file" template.yaml

# Expected Output shows:
# - !If conditions for HasCustomConfigPath
# - Proper ARN format using CloudFormation functions
# - No wildcard permissions

# 2. Verify no wildcard S3 permissions exist (should return empty)
grep -n "arn:aws:s3:::.*\*" template.yaml || echo "✅ No wildcard S3 permissions found"

# Expected Output:
# ✅ No wildcard S3 permissions found

# 3. Confirm S3 URI to ARN conversion
grep -A 5 "Path: !Select" template.yaml

# Expected Output shows CloudFormation functions converting S3 URI to ARN
```

**Result**: ✅ **PASSED** 
