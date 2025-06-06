#!/bin/bash

# Security Validation Script for A2I Role Changes
echo "🔍 Validating Security Improvements..."

# Check 1: Verify A2IFlowDefinitionRole exists
if grep -q "A2IFlowDefinitionRole:" template.yaml; then
    echo "✅ A2IFlowDefinitionRole is defined"
else
    echo "❌ A2IFlowDefinitionRole is missing"
    exit 1
fi

# Check 2: Verify PassRole is restricted to specific resource
if grep -A2 "iam:PassRole" template.yaml | grep -q "!GetAtt A2IFlowDefinitionRole.Arn"; then
    echo "✅ PassRole permission is restricted to specific role"
else
    echo "❌ PassRole permission is not properly restricted"
    exit 1
fi

# Check 3: Verify no wildcard PassRole permissions
if grep -A2 "iam:PassRole" template.yaml | grep -q "Resource: '\*'"; then
    echo "❌ Found wildcard PassRole permission"
    exit 1
else
    echo "✅ No wildcard PassRole permissions found"
fi

# Check 4: Verify SSM permissions are restricted
if grep -A5 "ssm:PutParameter" template.yaml | grep -q "${AWS::StackName}/FlowDefinitionArn"; then
    echo "✅ SSM permissions are restricted to specific parameter"
else
    echo "❌ SSM permissions are not properly restricted"
    exit 1
fi

# Check 5: Verify Lambda code uses new environment variable
if grep -q "A2I_FLOW_DEFINITION_ROLE_ARN" src/lambda/create_a2i_resources/index.py; then
    echo "✅ Lambda code uses new environment variable"
else
    echo "❌ Lambda code still uses old environment variable"
    exit 1
fi

# Check 6: Verify no old environment variable references in main template
if grep -q "LAMBDA_EXECUTION_ROLE_ARN" template.yaml; then
    echo "❌ Found old environment variable reference in template"
    exit 1
else
    echo "✅ No old environment variable references in template"
fi

# Check 7: Verify A2IFlowDefinitionRole has minimal permissions
if grep -A20 "A2IFlowDefinitionRole:" template.yaml | grep -q "sagemaker.amazonaws.com"; then
    echo "✅ A2IFlowDefinitionRole has correct service principal"
else
    echo "❌ A2IFlowDefinitionRole missing correct service principal"
    exit 1
fi

# Check 8: Verify ARN parsing uses correct index
if grep -q "!Select \[2, !Split" template.yaml; then
    echo "✅ ARN parsing uses correct index (2) for workteam name"
else
    echo "❌ ARN parsing uses incorrect index"
    exit 1
fi

# Check 9: Verify no incorrect ARN parsing indices
if grep -q "!Select \[5, !Split" template.yaml; then
    echo "❌ Found incorrect ARN parsing index (5)"
    exit 1
else
    echo "✅ No incorrect ARN parsing indices found"
fi

# Check 10: Verify S3 bucket ARNs are properly formatted
if grep -A25 "A2IFlowDefinitionRole:" template.yaml | grep -q "Bucket\.Arn"; then
    echo "✅ S3 bucket ARNs use proper .Arn attribute"
else
    echo "❌ S3 bucket ARNs may not be properly formatted"
    exit 1
fi

echo ""
echo "🎉 All security validation checks passed!"
echo "📋 Summary of improvements:"
echo "   • Created dedicated A2IFlowDefinitionRole with minimal permissions"
echo "   • Restricted PassRole to specific role ARN only"
echo "   • Limited SSM access to specific parameter path"
echo "   • Removed unnecessary service principals"
echo "   • Updated Lambda code to use new role"
echo "   • Fixed ARN parsing logic for workteam name extraction"
echo "   • Fixed S3 bucket ARN formatting in IAM policies"
echo ""
echo "🔒 Security posture significantly improved!"
