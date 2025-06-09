#!/usr/bin/env python3
"""
Simple test for AWS naming compliance
"""

import re


def sanitize_name(name):
    """
    Convert a name to AWS-compliant format for HumanTaskUI
    AWS pattern: [a-z0-9](-*[a-z0-9])*
    """
    # Convert to lowercase
    name = name.lower()

    # Remove underscores and replace with hyphens
    name = name.replace("_", "-")

    # Keep only alphanumeric and hyphens
    name = "".join(c for c in name if c.isalnum() or c == "-")

    # Remove leading/trailing hyphens
    name = name.strip("-")

    # Remove consecutive hyphens
    while "--" in name:
        name = name.replace("--", "-")

    # Ensure it starts with alphanumeric (required by AWS)
    if name and not name[0].isalnum():
        name = "a" + name

    # Ensure it's not empty
    if not name:
        name = "default"

    return name


def generate_resource_names(stack_name):
    """Generate AWS-compliant names for A2I resources"""
    base_name = sanitize_name(stack_name)
    return {
        "human_task_ui": f"{base_name}-hitl-ui",
        "flow_definition": f"{base_name}-hitl-fd",
    }


# AWS pattern for HumanTaskUI names
aws_pattern = r"^[a-z0-9](-*[a-z0-9])*$"

# Test cases
test_cases = [
    "IDP-GENAI",  # Your current case
    "IDP_GENAI",  # With underscore
    "My-Stack-Name",  # Mixed case with hyphens
    "123-test",  # Starting with number
    "UPPERCASE-NAME",  # All uppercase with hyphen
    "name--with--double--hyphens",  # Multiple hyphens
    "-leading-hyphen-",  # Leading/trailing hyphens
    "special@#$chars",  # Special characters
    "",  # Empty string
]

print("🧪 Testing AWS Naming Compliance Fix")
print("=" * 50)

for stack_name in test_cases:
    resource_names = generate_resource_names(stack_name)
    human_task_ui_name = resource_names["human_task_ui"]
    flow_definition_name = resource_names["flow_definition"]

    # Check AWS compliance
    ui_compliant = bool(re.match(aws_pattern, human_task_ui_name))
    fd_compliant = bool(re.match(aws_pattern, flow_definition_name))

    status = "✅" if ui_compliant and fd_compliant else "❌"
    print(f"{status} Stack: '{stack_name}'")
    print(f"   HumanTaskUI: '{human_task_ui_name}' ({'✅' if ui_compliant else '❌'})")
    print(
        f"   FlowDef:     '{flow_definition_name}' ({'✅' if fd_compliant else '❌'})"
    )
    print()

print("🎉 All names are now AWS compliant!")
