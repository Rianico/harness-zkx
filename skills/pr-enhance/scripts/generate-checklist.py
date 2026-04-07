#!/usr/bin/env python3
import sys
import json
from collections import defaultdict

def generate_review_checklist(analysis):
    """
    Generate context-aware review checklist
    """
    checklist = ["## Review Checklist\n"]

    # General items
    general_items = [
        "Code follows project style guidelines",
        "Self-review completed",
        "Comments added for complex logic",
        "No debugging code left",
        "No sensitive data exposed"
    ]

    # Add general items
    checklist.append("### General")
    for item in general_items:
        checklist.append(f"- [ ] {item}")

    # File-specific checks
    file_types = {file['category'] for file in analysis.get('files_changed', [])}

    if 'source' in file_types:
        checklist.append("\n### Code Quality")
        checklist.extend([
            "- [ ] No code duplication",
            "- [ ] Functions are focused and small",
            "- [ ] Variable names are descriptive",
            "- [ ] Error handling is comprehensive",
            "- [ ] No performance bottlenecks introduced"
        ])

    if 'test' in file_types:
        checklist.append("\n### Testing")
        checklist.extend([
            "- [ ] All new code is covered by tests",
            "- [ ] Tests are meaningful and not just for coverage",
            "- [ ] Edge cases are tested",
            "- [ ] Tests follow AAA pattern (Arrange, Act, Assert)",
            "- [ ] No flaky tests introduced"
        ])

    if 'config' in file_types:
        checklist.append("\n### Configuration")
        checklist.extend([
            "- [ ] No hardcoded values",
            "- [ ] Environment variables documented",
            "- [ ] Backwards compatibility maintained",
            "- [ ] Security implications reviewed",
            "- [ ] Default values are sensible"
        ])

    if 'docs' in file_types:
        checklist.append("\n### Documentation")
        checklist.extend([
            "- [ ] Documentation is clear and accurate",
            "- [ ] Examples are provided where helpful",
            "- [ ] API changes are documented",
            "- [ ] README updated if necessary",
            "- [ ] Changelog updated"
        ])

    return '\n'.join(checklist)

if __name__ == '__main__':
    try:
        input_data = sys.stdin.read()
        analysis = json.loads(input_data)
        print(generate_review_checklist(analysis))
    except Exception as e:
        print(f"Error generating checklist: {str(e)}")
