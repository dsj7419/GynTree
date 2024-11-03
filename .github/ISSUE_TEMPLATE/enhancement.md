---
name: Enhancement Suggestion
description: Suggest an improvement to existing functionality
title: "[ENHANCEMENT] "
labels: ["enhancement"]
---

body:

- type: markdown
  attributes:
  value: |
  Thank you for suggesting an enhancement to GynTree. Please provide details about your proposed improvement to existing functionality.
- type: textarea
  id: current-functionality
  attributes:
  label: Current Functionality
  description: Describe the current feature or functionality you want to enhance
  validations:
  required: true
- type: textarea
  id: proposed-enhancement
  attributes:
  label: Proposed Enhancement
  description: Describe how you would improve this functionality
  validations:
  required: true
- type: textarea
  id: benefits
  attributes:
  label: Benefits
  description: What are the benefits of this enhancement?
  validations:
  required: true
- type: dropdown
  id: priority
  attributes:
  label: Suggested Priority
  options: - Low Priority - Medium Priority - High Priority
  validations:
  required: true
