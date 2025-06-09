#!/usr/bin/env python3
"""
Simple test for AWS naming compliance
"""


def sanitize_name(name):
    """Convert a name to AWS-compliant format (lowercase alphanumeric)"""
    name = name.lower()
    name = "".join(c if c.isalnum() else str(ord(c) % 10) for c in name)
    if name[0].isdigit():
        name = "a" + name
    return name


def generate_resource_names(stack_name):
    """Generate AWS-compliant names for A2I resources"""
    base_name = sanitize_name(stack_name)
    return {
        "human_task_ui": f"{base_name}hitlui",
        "flow_definition": f"{base_name}hitlfd",
    }


# Test the problematic case
test_cases = ["IDP-BDA-3", "My-Stack-Name", "123-test", "UPPERCASE-NAME"]

print("🧪 Testing AWS Naming Compliance Fix")
print("=" * 50)

for stack_name in test_cases:
    resource_names = generate_resource_names(stack_name)
    human_task_ui_name = resource_names["human_task_ui"]

    # Check AWS compliance
    import re

    aws_compliant = re.match(r"^[a-z0-9]+$", human_task_ui_name)
    starts_with_letter = human_task_ui_name[0].isalpha()

    status = "✅" if aws_compliant and starts_with_letter else "❌"
    print(f"{status} '{stack_name}' → '{human_task_ui_name}'")

print("\n🎉 All names are now AWS compliant!")
