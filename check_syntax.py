try:
    import app.main
    print("No syntax error found.")
except SyntaxError as e:
    print(f"SYNTAX_ERROR_LINE:{e.lineno}")
    print(f"SYNTAX_ERROR_MSG:{e.msg}")
except Exception as e:
    print(f"OTHER_ERROR:{e}")
