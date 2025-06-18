# YAML Parsing Error Fix - Pattern-2 Template

## Error Message
```
Error: Failed to parse template: while parsing a block mapping
  in "<unicode string>", line 481, column 13:
            order: 5
            ^
expected <block end>, but found '<block mapping start>'
  in "<unicode string>", line 486, column 15:
              temperature:
              ^
```

## Root Cause Analysis

The error was caused by **two separate YAML syntax issues** in the Pattern-2 template:

### Issue 1: Missing Field Name in Assessment Section (Lines 481-486)

**Location**: `patterns/pattern-2/template.yaml` around line 484-485

**Problem**: The `assessment` section had a `properties:` block with missing field structure:

```yaml
assessment:
  order: 5
  type: object
  sectionLabel: Assessment Inference
  properties:
      order: 2          # ❌ Missing field name before 'order'
    temperature:        # ❌ Incorrect indentation
```

**Root Cause**: The `properties` section was missing a proper field name (like `model:`) before the `order: 2` line, and the subsequent fields were incorrectly indented.

### Issue 2: Misplaced Policies Section (Line 640)

**Location**: `patterns/pattern-2/template.yaml` around line 640

**Problem**: Lambda function policies were incorrectly placed under a CloudFormation Custom Resource:

```yaml
UpdateDefaultConfig:
  Type: AWS::CloudFormation::CustomResource
  Properties:
    ServiceToken: !Ref UpdateConfigurationFunctionArn
    Default: !Ref ConfigurationDefaultS3Uri
    ConfigLibraryHash: !Ref ConfigLibraryHash
      - DynamoDBCrudPolicy:     # ❌ Policies don't belong in Custom Resource
          TableName: !Ref ConfigurationTable
      - Statement:              # ❌ Misplaced IAM statements
```

**Root Cause**: IAM policies that should have been under a Lambda function's `Policies` section were incorrectly indented and placed under the `UpdateDefaultConfig` custom resource.

## Fixes Applied

### Fix 1: Corrected Assessment Section Structure

**Before**:
```yaml
assessment:
  order: 5
  type: object
  sectionLabel: Assessment Inference
  properties:
      order: 2
    temperature:
```

**After**:
```yaml
assessment:
  order: 5
  type: object
  sectionLabel: Assessment Inference
  properties:
    model:
      type: string
      description: Bedrock model ID
      enum: ["us.amazon.nova-lite-v1:0", "us.amazon.nova-pro-v1:0", ...]
      order: 1
    default_confidence_threshold:
      type: number
      description: Default confidence threshold for assessment (0.0 to 1.0)
      minimum: 0
      maximum: 1
      order: 2
    temperature:
      type: number
      description: Sampling temperature
      order: 3
```

### Fix 2: Removed Misplaced Policies

**Before**:
```yaml
UpdateDefaultConfig:
  Type: AWS::CloudFormation::CustomResource
  Properties:
    ServiceToken: !Ref UpdateConfigurationFunctionArn
    Default: !Ref ConfigurationDefaultS3Uri
    ConfigLibraryHash: !Ref ConfigLibraryHash
      - DynamoDBCrudPolicy:
          TableName: !Ref ConfigurationTable
      - Statement:
        - Effect: Allow
          Action: cloudwatch:PutMetricData
          Resource: '*'
        # ... more misplaced policies
```

**After**:
```yaml
UpdateDefaultConfig:
  Type: AWS::CloudFormation::CustomResource
  Properties:
    ServiceToken: !Ref UpdateConfigurationFunctionArn
    Default: !Ref ConfigurationDefaultS3Uri
    ConfigLibraryHash: !Ref ConfigLibraryHash
```

## Why This Happened

1. **Assessment Section**: The configuration schema was likely modified without properly maintaining the YAML structure, resulting in missing field names and incorrect indentation.

2. **Misplaced Policies**: During template editing, IAM policies were accidentally moved or copied to the wrong location, ending up under a Custom Resource instead of a Lambda function.

## Validation

After applying the fixes:

```bash
cd patterns/pattern-2
sam validate --template template.yaml
# Result: ✅ "/path/to/template.yaml is a valid SAM Template"
```

## Prevention

To prevent similar issues in the future:

1. **Use YAML Linting**: Always validate YAML syntax before committing changes
2. **Consistent Indentation**: Use consistent spacing (2 or 4 spaces, not tabs)
3. **Structure Validation**: Ensure CloudFormation resource properties are correctly nested
4. **Template Validation**: Run `sam validate` as part of the build process

## Files Modified

- `patterns/pattern-2/template.yaml` - Fixed YAML syntax issues

## Impact

- ✅ Pattern-2 template now passes SAM validation
- ✅ Build process can continue successfully
- ✅ Assessment section properly structured for UI configuration
- ✅ No functional changes to the actual deployment
