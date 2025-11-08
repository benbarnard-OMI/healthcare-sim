#!/usr/bin/env python3
"""
Test script to validate optimization changes without requiring full LLM setup.
This script checks:
1. Code syntax and imports
2. Task structure (should be 3 tasks, not 4)
3. Configuration values (max_tokens, max_iter)
4. Prompt lengths (should be shorter)
"""

import ast
import re
import sys
from pathlib import Path

def check_file_syntax(filepath):
    """Check if Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)

def count_tasks_in_crew_method(filepath):
    """Count tasks in the crew() method."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find the crew() method
    crew_match = re.search(r'def crew\(self\)[^:]*:.*?return Crew\([^)]+\)', content, re.DOTALL)
    if not crew_match:
        return None, "Could not find crew() method"
    
    crew_code = crew_match.group(0)
    
    # Count task calls
    task_calls = re.findall(r'self\.\w+\(\)', crew_code)
    # Filter to actual task method calls (not agent calls)
    task_methods = [t for t in task_calls if any(x in t for x in ['parse_hl7', 'make_clinical', 'generate_hl7', 'coordinate', 'evaluate'])]
    
    return len(task_methods), task_methods

def check_max_tokens_limit(filepath):
    """Check if max_tokens is capped at 1500."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Look for max_tokens assignments
    matches = re.findall(r'max_tokens=.*?(\d+)', content)
    if matches:
        # Check if any are > 1500 (excluding the min() function which caps it)
        for match in matches:
            if 'min(' not in content[content.find(match)-50:content.find(match)]:
                if int(match) > 1500:
                    return False, f"Found max_tokens={match} which exceeds 1500 limit"
    
    # Check for min() capping
    if 'min(self.llm_config.max_tokens or 2000, 1500)' in content:
        return True, "max_tokens properly capped at 1500"
    
    return None, "Could not verify max_tokens capping"

def check_max_iter(filepath):
    """Check if max_iter is set to 2."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    if 'max_iter=2' in content:
        return True, "max_iter set to 2"
    elif 'max_iter=1' in content:
        return False, "max_iter still set to 1 (should be 2)"
    else:
        return None, "Could not find max_iter setting"

def check_prompt_lengths(filepath):
    """Check if task descriptions are shorter."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find generate_hl7_messages task description - look for the description field
    hl7_start = content.find('def generate_hl7_messages')
    if hl7_start == -1:
        return None, "Could not find generate_hl7_messages task"
    
    # Find the description field within this task - handle escaped quotes
    task_section = content[hl7_start:hl7_start+2000]
    desc_match = re.search(r"'description':\s*'((?:[^'\\]|\\.)+)'", task_section)
    if desc_match:
        desc = desc_match.group(1).replace("\\'", "'")
        if len(desc) < 500:  # Allow slightly more since it includes reference to doc
            return True, f"HL7 task description is {len(desc)} chars (optimized, was ~663)"
        else:
            return False, f"HL7 task description is {len(desc)} chars (should be < 500)"
    
    return None, "Could not find description field in generate_hl7_messages"

def check_task_consolidation(filepath):
    """Check if make_clinical_decisions includes planning."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find make_clinical_decisions task description
    decisions_start = content.find('def make_clinical_decisions')
    if decisions_start == -1:
        return None, "Could not find make_clinical_decisions task"
    
    # Find the description field - handle escaped quotes
    task_section = content[decisions_start:decisions_start+2000]
    # Look for description field, handling escaped quotes
    desc_match = re.search(r"'description':\s*'((?:[^'\\]|\\.)+)'", task_section)
    if desc_match:
        desc = desc_match.group(1).replace("\\'", "'").lower()
        if 'plan' in desc or 'orders' in desc or 'consultations' in desc:
            return True, "make_clinical_decisions includes planning (consolidated)"
        else:
            return False, f"make_clinical_decisions does not include planning. Description: {desc[:100]}..."
    
    return None, "Could not find description field in make_clinical_decisions"

def check_reference_doc():
    """Check if HL7_FORMATTING_REFERENCE.md exists."""
    ref_path = Path('/workspace/docs/HL7_FORMATTING_REFERENCE.md')
    if ref_path.exists():
        return True, "HL7_FORMATTING_REFERENCE.md exists"
    return False, "HL7_FORMATTING_REFERENCE.md not found"

def main():
    """Run all validation checks."""
    print("=" * 60)
    print("OPTIMIZATION VALIDATION TESTS")
    print("=" * 60)
    print()
    
    crew_file = Path('/workspace/crew.py')
    results = []
    
    # Test 1: Syntax check
    print("1. Checking syntax...")
    valid, error = check_file_syntax(crew_file)
    if valid:
        print("   ✅ Syntax is valid")
        results.append(("Syntax", True))
    else:
        print(f"   ❌ Syntax error: {error}")
        results.append(("Syntax", False))
    print()
    
    # Test 2: Task count
    print("2. Checking task count...")
    count, methods = count_tasks_in_crew_method(crew_file)
    if count == 3:
        print(f"   ✅ Found {count} tasks (optimized from 4)")
        print(f"   Tasks: {', '.join(methods)}")
        results.append(("Task Count", True))
    elif count == 4:
        print(f"   ⚠️  Found {count} tasks (should be 3 after optimization)")
        results.append(("Task Count", False))
    else:
        print(f"   ❓ Found {count} tasks (unexpected)")
        results.append(("Task Count", None))
    print()
    
    # Test 3: Max tokens limit
    print("3. Checking max_tokens limit...")
    valid, msg = check_max_tokens_limit(crew_file)
    if valid is True:
        print(f"   ✅ {msg}")
        results.append(("Max Tokens", True))
    elif valid is False:
        print(f"   ❌ {msg}")
        results.append(("Max Tokens", False))
    else:
        print(f"   ❓ {msg}")
        results.append(("Max Tokens", None))
    print()
    
    # Test 4: Max iter
    print("4. Checking max_iter...")
    valid, msg = check_max_iter(crew_file)
    if valid is True:
        print(f"   ✅ {msg}")
        results.append(("Max Iter", True))
    elif valid is False:
        print(f"   ❌ {msg}")
        results.append(("Max Iter", False))
    else:
        print(f"   ❓ {msg}")
        results.append(("Max Iter", None))
    print()
    
    # Test 5: Prompt length
    print("5. Checking prompt optimization...")
    valid, msg = check_prompt_lengths(crew_file)
    if valid is True:
        print(f"   ✅ {msg}")
        results.append(("Prompt Length", True))
    elif valid is False:
        print(f"   ❌ {msg}")
        results.append(("Prompt Length", False))
    else:
        print(f"   ❓ {msg}")
        results.append(("Prompt Length", None))
    print()
    
    # Test 6: Task consolidation
    print("6. Checking task consolidation...")
    valid, msg = check_task_consolidation(crew_file)
    if valid is True:
        print(f"   ✅ {msg}")
        results.append(("Task Consolidation", True))
    elif valid is False:
        print(f"   ❌ {msg}")
        results.append(("Task Consolidation", False))
    else:
        print(f"   ❓ {msg}")
        results.append(("Task Consolidation", None))
    print()
    
    # Test 7: Reference document
    print("7. Checking reference document...")
    valid, msg = check_reference_doc()
    if valid:
        print(f"   ✅ {msg}")
        results.append(("Reference Doc", True))
    else:
        print(f"   ❌ {msg}")
        results.append(("Reference Doc", False))
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    unknown = sum(1 for _, result in results if result is None)
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"❓ Unknown: {unknown}")
    print()
    
    if failed == 0 and unknown == 0:
        print("🎉 All optimizations validated successfully!")
        return 0
    elif failed > 0:
        print("⚠️  Some optimizations need attention")
        return 1
    else:
        print("ℹ️  Some checks could not be verified")
        return 0

if __name__ == "__main__":
    sys.exit(main())
