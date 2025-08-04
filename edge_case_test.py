# Edge Case Testing for Issue #778 Phase 3.2
# Comprehensive test for all supported error types

import threading  # Another unused import

def complex_function_with_multiple_issues():
    # E501: Very long line with nested function calls and complex arguments
    result = some_very_long_function_name_that_makes_the_line_exceed_limit(first_argument="very_long_value_string", second_argument="another_very_long_value", third_argument={"nested": "dictionary", "with": "multiple", "keys": "and_values"})

    # E226: Multiple operator spacing issues
    x=1+2*3-4/5
    y=x**2%7
    condition=(x>y)and(y<10)or(x==5)

    # E704/E702: Multiple statements with complex patterns
    a = 1; b = 2; c = a + b
    print("test")
    result = x + y
    final = result * 2

    # E704/E702: Statements with strings containing semicolons (should be protected)
    sql_query = "SELECT * FROM users; UPDATE users SET active = 1;"
    executed = True
    log_message = "Process started; Status: OK; Time: 10:30"; logged = False

    # E501: Long string that should be split
    error_message = "This is a very long error message that exceeds the line length limit and should be automatically split into multiple lines for better readability"

    # E226 + E501: Combined issues on same line
    very_long_calculation_result=first_very_long_variable_name+second_very_long_variable_name*third_very_long_variable_name-fourth_very_long_variable_name

    # E704: Multiple assignments with complex expressions
    first_result = complex_calculation(1, 2); second_result = another_calculation(3, 4); third_result = first_result + second_result

    return result, x, y, condition

def test_string_edge_cases():
    # E704: Semicolons in different string types
    single_quote = 'SELECT id; UPDATE table;'; double_quote = "DELETE from table; INSERT into table;"
    triple_single = '''Complex SQL:
    SELECT * FROM users;
    UPDATE users SET status = 'active';
    DELETE FROM logs;'''; processed = True

    # E704: Escaped semicolons in strings
    escaped_string = "This\\; is\\; escaped"; normal_statement = "not escaped"

    # E501: Long f-string
    formatted_message = f"User {user_name} has performed {action_count} actions in the last {time_period} hours and has {remaining_credits} credits remaining"

    return single_quote, double_quote, processed

class ComplexClassWithIssues:
    def __init__(self, param1, param2, param3="default_value_that_makes_this_line_very_long"):
        # E226: Multiple operator issues in class
        self.value=param1+param2
        self.result=self.value*2+param3

        # E704: Multiple assignments in constructor
        self.status = "active"; self.count = 0; self.initialized = True

    def method_with_long_signature(self, first_parameter, second_parameter, third_parameter="default", fourth_parameter=None):
        # E501: Method with very long signature
        return self.complex_processing(
            first_parameter,
            second_parameter,
            third_parameter,
            fourth_parameter
        )

# E302: Missing blank lines (flake8 will detect this)
def another_function():
    pass

# E704: Global level multiple statements
global_var1 = "test"; global_var2 = "another"; global_var3 = global_var1 + global_var2
