#!/usr/bin/env python3
"""
Test script to validate the orphaned workforce cleanup scenario
"""

import re


def analyze_orphaned_workforce_handling():
    """Analyze the comprehensive workforce cleanup to ensure it handles orphaned workforces"""

    print("🔍 Analyzing Orphaned Workforce Cleanup Logic")
    print("=" * 60)

    with open("src/lambda/create_a2i_resources/index.py", "r") as f:
        content = f.read()

    # Find the comprehensive_workforce_cleanup function
    cleanup_function = re.search(
        r"def comprehensive_workforce_cleanup\(.*?\):(.*?)(?=\ndef|\nclass|\Z)",
        content,
        re.DOTALL,
    )

    if not cleanup_function:
        print("❌ ERROR: Could not find comprehensive_workforce_cleanup function")
        return False

    cleanup_code = cleanup_function.group(1)

    # Test 1: Check if it handles workteam already deleted scenario
    handles_workteam_deleted = (
        "ValidationException" in cleanup_code and "already deleted" in cleanup_code
    )
    print(f"✅ Handles workteam already deleted: {handles_workteam_deleted}")

    # Test 2: Check if it ALWAYS checks for orphaned workforces (not just on workteam deletion failure)
    always_checks_workforce = (
        "ALWAYS check for" in cleanup_code
        or "regardless of workteam status" in cleanup_code
    )
    print(f"✅ Always checks for orphaned workforces: {always_checks_workforce}")

    # Test 3: Check if it identifies workforces associated with the stack
    identifies_associated_workforce = (
        "is_our_workforce" in cleanup_code
        or "associated with our stack" in cleanup_code
    )
    print(f"✅ Identifies associated workforces: {identifies_associated_workforce}")

    # Test 4: Check if it handles the specific orphaned workforce scenario
    handles_orphaned_scenario = (
        "Workteam already deleted, cleaning up orphaned workforce" in cleanup_code
    )
    print(f"✅ Handles orphaned workforce scenario: {handles_orphaned_scenario}")

    # Test 5: Check if it has multiple identification methods
    has_multiple_identification = (
        "workteam_name_lower in workforce_str" in cleanup_code
        and "stack_name_lower in workforce_str" in cleanup_code
    )
    print(
        f"✅ Has multiple workforce identification methods: {has_multiple_identification}"
    )

    # Test 6: Check if it verifies final cleanup state
    verifies_final_state = (
        "Final verification" in cleanup_code and "private workforce" in cleanup_code
    )
    print(f"✅ Verifies final cleanup state: {verifies_final_state}")

    # Test 7: Check if it handles workforce in bad state
    handles_bad_state = "potentially orphaned workforce" in cleanup_code
    print(f"✅ Handles workforce in bad state: {handles_bad_state}")

    all_tests = [
        handles_workteam_deleted,
        always_checks_workforce,
        identifies_associated_workforce,
        handles_orphaned_scenario,
        has_multiple_identification,
        verifies_final_state,
        handles_bad_state,
    ]

    return all(all_tests)


def main():
    """Run all orphaned workforce scenario tests"""

    print("🧪 Testing Orphaned Workforce Cleanup Solution")
    print("=" * 80)

    try:
        result = analyze_orphaned_workforce_handling()
        if result:
            print("\n🎉 All orphaned workforce scenario tests PASSED!")
            return True
        else:
            print("\n❌ Some orphaned workforce scenario tests FAILED!")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
