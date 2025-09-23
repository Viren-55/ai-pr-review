#!/usr/bin/env python3
"""
Sample code with various issues for testing AI agents
"""

import os
import sys

# Security issue: SQL injection vulnerability
def get_user_data(user_id):
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    # This is vulnerable to SQL injection
    return execute_query(query)

# Performance issue: Inefficient recursion without memoization
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Code quality issue: Too broad exception handling
def process_data(data):
    try:
        result = data / 0  # Division by zero
        return result
    except:  # Too broad exception
        pass  # Silent failure

# Security issue: Hardcoded credentials
DATABASE_PASSWORD = "admin123"
API_KEY = "sk-1234567890abcdef"

# Best practices issue: No input validation
def calculate_discount(price, discount_percent):
    # Missing validation for negative values
    return price * (1 - discount_percent / 100)

# Performance issue: Inefficient list operations
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    return duplicates

# Error handling issue: Resource not properly closed
def read_file(filename):
    f = open(filename, 'r')
    content = f.read()
    # File not closed - resource leak
    return content

if __name__ == "__main__":
    # Test the functions
    print(fibonacci(10))
    print(get_user_data("1; DROP TABLE users;"))