#!/bin/bash

# Security and Dependency Validation Script with Orphaned Workforce Fix
echo "🔍 Validating Security Improvements and Comprehensive Workforce Cleanup..."

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

# Check 11: Verify comprehensive workforce cleanup is implemented in CreateA2IResourcesLambda
if grep -q "comprehensive_workforce_cleanup" src/lambda/create_a2i_resources/index.py; then
    echo "✅ Comprehensive workforce cleanup is implemented in CreateA2IResourcesLambda"
else
    echo "❌ Comprehensive workforce cleanup is missing from CreateA2IResourcesLambda"
    exit 1
fi

# Check 12: Verify CreateA2IResourcesLambda has workforce management permissions
if grep -A35 "A2IHumanTaskUILambdaRole:" template.yaml | grep -q "sagemaker:DeleteWorkteam"; then
    echo "✅ CreateA2IResourcesLambda has workforce management permissions"
else
    echo "❌ CreateA2IResourcesLambda missing workforce management permissions"
    exit 1
fi

# Check 13: Verify no separate workforce cleanup resources exist
if grep -q "WorkforceCleanupResource:" template.yaml; then
    echo "❌ Found separate workforce cleanup resources (should be consolidated)"
    exit 1
else
    echo "✅ No separate workforce cleanup resources (properly consolidated)"
fi

# Check 14: Verify increased timeout for comprehensive operations
if grep -A20 "CodeUri: src/lambda/create_a2i_resources" template.yaml | grep -q "Timeout: 600"; then
    echo "✅ CreateA2IResourcesLambda has increased timeout for comprehensive cleanup"
else
    echo "❌ CreateA2IResourcesLambda timeout not increased for comprehensive cleanup"
    exit 1
fi

# Check 15: Verify orphaned workforce scenario is handled
if python3 test_orphaned_workforce_scenario.py > /dev/null 2>&1; then
    echo "✅ Orphaned workforce scenario is properly handled"
else
    echo "❌ Orphaned workforce scenario handling has issues"
    exit 1
fi

# Check 16: Verify no reserved AWS environment variables are set
if grep -A10 "Environment:" template.yaml | grep -A10 "CodeUri: src/lambda/create_a2i_resources" | grep -q "AWS_REGION\|AWS_ACCOUNT_ID"; then
    echo "❌ Found reserved AWS environment variables in Lambda configuration"
    exit 1
else
    echo "✅ No reserved AWS environment variables in Lambda configuration"
fi

# Check 17: Verify numpy version constraints are in place
if grep -q "numpy>=1.24.0,<2.0.0" lib/idp_common_pkg/setup.py; then
    echo "✅ Numpy version constraints are properly set"
else
    echo "❌ Numpy version constraints are missing"
    exit 1
fi

# Check 18: Verify pandas version constraints are in place
if grep -q "pandas>=1.5.0,<3.0.0" lib/idp_common_pkg/setup.py; then
    echo "✅ Pandas version constraints are properly set"
else
    echo "❌ Pandas version constraints are missing"
    exit 1
fi

# Check 19: Verify AWS naming compliance functions are implemented
if grep -q "def sanitize_name" src/lambda/create_a2i_resources/index.py; then
    echo "✅ AWS naming compliance functions are implemented"
else
    echo "❌ AWS naming compliance functions are missing"
    exit 1
fi

# Check 20: Test naming compliance with problematic stack names
if python3 test_naming_simple.py > /dev/null 2>&1; then
    echo "✅ AWS naming compliance works for problematic stack names"
else
    echo "❌ AWS naming compliance test failed"
    exit 1
fi

echo ""
echo "🎉 All validation checks passed!"
echo "📋 Summary of improvements:"
echo "   • Created dedicated A2IFlowDefinitionRole with minimal permissions"
echo "   • Restricted PassRole to specific role ARN only"
echo "   • Limited SSM access to specific parameter path"
echo "   • Removed unnecessary service principals"
echo "   • Updated Lambda code to use new role"
echo "   • Fixed ARN parsing logic for workteam name extraction"
echo "   • Fixed S3 bucket ARN formatting in IAM policies"
echo "   • Implemented comprehensive workforce cleanup in single Lambda function"
echo "   • Simplified architecture by consolidating functionality"
echo "   • Increased Lambda timeout for comprehensive operations"
echo "   • Fixed critical orphaned workforce cleanup scenario"
echo "   • Removed reserved AWS environment variables from Lambda configuration"
echo "   • Added dependency version constraints to prevent build failures"
echo "   • Implemented AWS naming compliance for HumanTaskUI and FlowDefinition"
echo ""
echo "🔒 Security posture significantly improved!"
echo "🧹 Comprehensive workforce cleanup implemented!"
echo "⚡ Simplified architecture with single Lambda function!"
echo "🔧 Critical orphaned workforce edge case resolved!"
echo "🚀 CloudFormation deployment issues fixed!"
echo "📦 Dependency build issues resolved!"
echo "✅ AWS naming validation errors fixed!"
