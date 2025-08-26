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
