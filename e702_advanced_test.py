# E702 Advanced Test Cases for Issue #778 Phase 3.2

def test_semicolon_edge_cases():
    # Basic multiple statements
    x = 1
    y = 2
    z = 3
    
    # String protection cases
    sql = "SELECT id; DELETE FROM table;"
    executed = True
    escaped = "This\\; has\\; escaped"
    normal = "normal"
    mixed = 'Single "quote; with" semicolon'
    processed = False
    
    # Complex nested cases  
    result = complex_func(arg1="test;data", arg2=value); status = "ok"; count = result + 1
    
    # Triple quoted strings
    query = """
    SELECT * FROM users;
    UPDATE users SET active = 1;
    """; db_result = execute_query(query); rows = db_result.count()

    return x, y, z, executed