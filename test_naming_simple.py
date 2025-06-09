#!/usr/bin/env python3
"""
Simple test for AWS naming compliance
"""

import re


def sanitize_name(name, max_length=63):
    """
    Convert a name to AWS-compliant format for HumanTaskUI
    Requirements:
    - Must be lowercase alphanumeric
    - Can contain hyphens only between alphanumeric characters
    - Maximum length of 63 characters
    """
    # Convert to lowercase
    name = name.lower()

    # Convert underscores to hyphens
    name = name.replace("_", "-")

    # Process the string character by character to ensure hyphens are only between alphanumeric
    result = []
    for i, char in enumerate(name):
        if char.isalnum():
            result.append(char)
        elif char == "-" and i > 0 and i < len(name) - 1:
            # Only add hyphen if it's between alphanumeric characters
            if name[i - 1].isalnum() and name[i + 1].isalnum():
                result.append(char)

    name = "".join(result)

    # Ensure it's not empty
    if not name:
        name = "default"

    # Ensure it starts with alphanumeric
    if not name[0].isalnum():
        name = "a" + name

    # Truncate to max length while preserving word boundaries
    if len(name) > max_length:
        # Try to truncate at last hyphen before max_length
        last_hyphen = name.rfind("-", 0, max_length)
        if last_hyphen > 0:
            name = name[:last_hyphen]
        else:
            name = name[:max_length]

    return name


def generate_resource_names(stack_name):
    """Generate AWS-compliant names for A2I resources"""
    base_name = sanitize_name(stack_name)

    # Calculate maximum length for base name to accommodate suffixes
    max_base_length = 63 - len("-hitl-ui")  # Account for longest suffix
    base_name = sanitize_name(stack_name, max_base_length)

    return {
        "human_task_ui": f"{base_name}-hitl-ui",
        "flow_definition": f"{base_name}-hitl-fd",
    }


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
    "a" * 100,  # Very long name
    "abc-def-" + "g" * 60,  # Long name with hyphens
    "a-b-c-d-e-f-g-h-i-j-k",  # Many hyphens
    "a@b-c#d-e$f",  # Mixed special chars and hyphens
]

print("🧪 Testing AWS Naming Compliance Fix")
print("=" * 50)


def verify_aws_requirements(name):
    """Verify all AWS requirements for the name"""
    requirements = [
        (name.islower(), "Must be lowercase"),
        (
            bool(re.match(r"^[a-z0-9].*[a-z0-9]$", name)),
            "Must start and end with alphanumeric",
        ),
        (
            all(c.isalnum() or c == "-" for c in name),
            "Must only contain alphanumeric and hyphens",
        ),
        ("--" not in name, "No consecutive hyphens"),
        (len(name) <= 63, f"Length must be <= 63 (current: {len(name)})"),
        (
            all(
                name[i - 1].isalnum() and name[i + 1].isalnum()
                for i, c in enumerate(name)
                if c == "-" and 0 < i < len(name) - 1
            ),
            "Hyphens must be between alphanumeric characters",
        ),
    ]
    return [(passed, message) for passed, message in requirements]


for stack_name in test_cases:
    print(f"\nTesting stack name: '{stack_name}'")
    resource_names = generate_resource_names(stack_name)

    for resource_type, name in resource_names.items():
        print(f"\n{resource_type}:")
        print(f"  Result: '{name}'")

        # Verify AWS requirements
        requirements = verify_aws_requirements(name)
        all_passed = all(passed for passed, _ in requirements)

        print(f"  Status: {'✅' if all_passed else '❌'}")

        # Show any failed requirements
        if not all_passed:
            print("  Failed requirements:")
            for passed, message in requirements:
                if not passed:
                    print(f"    ❌ {message}")

print("\n" + "=" * 50)
print("🎉 Testing complete!")
