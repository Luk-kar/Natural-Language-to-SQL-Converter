"""
Comprehensive test suite for core data processing and visualization components.

This module contains validation tests for two critical system capabilities:

1. **SQL Query Handling & Security**
   - SQL query extraction from natural language inputs
   - CTE support and comment sanitization
   - Blocking of unauthorized operations (DDL/DCL/TCL commands)
   - Security patterns preventing data manipulation/injection
   - Error context propagation for debugging

2. **Visualization Metadata Extraction**
   - Function signature parsing for plot generation
   - Parameter type detection and documentation
   - Docstring processing for API documentation
   - Multi-function module analysis

Tests validate both functional correctness and security requirements through positive/negative test cases
and edge condition simulations.
"""
