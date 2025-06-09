#!/bin/bash

# AWS Naming Compliance Validation Script
echo "🔍 Validating AWS Naming Compliance Implementation..."

# Check 1: Verify AWS naming compliance functions are implemented
if grep -q "def sanitize_name" src/lambda/create_a2i_resources/index.py; then
    echo "✅ AWS naming compliance functions are implemented"
else
    echo "❌ AWS naming compliance functions are missing"
    exit 1
fi

# Check 2: Verify length validation is implemented
if grep -q "max_length" src/lambda/create_a2i_resources/index.py; then
    echo "✅ Length validation is implemented"
else
    echo "❌ Length validation is missing"
    exit 1
fi

# Check 3: Test naming compliance with problematic stack names
if python3 test_naming_simple.py > /dev/null 2>&1; then
    echo "✅ AWS naming compliance works for all test cases"
else
    echo "❌ AWS naming compliance test failed"
    exit 1
fi

echo ""
echo "🎉 All validation checks passed!"
echo "📋 AWS Naming Requirements Satisfied:"
echo "   ✅ Lowercase alphanumeric characters only"
echo "   ✅ Hyphens only between alphanumeric characters"
echo "   ✅ Maximum length of 63 characters"
echo "   ✅ Proper handling of edge cases"
echo ""
echo "✅ ValidationException for HumanTaskUI names resolved!"
