#!/bin/bash

# Security and Dependency Validation Script with Orphaned Workforce Fix
echo "🔍 Validating Security Improvements and Comprehensive Workforce Cleanup..."

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
echo "   • Implemented AWS naming compliance for HumanTaskUI and FlowDefinition"
echo "   • Fixed ValidationException with stack names containing special characters"
echo "   • Added dependency version constraints to prevent build failures"
echo ""
echo "✅ AWS naming validation errors fixed!"
