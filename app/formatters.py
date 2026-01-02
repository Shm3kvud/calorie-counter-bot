def format_kbju(string: str):
    result = string.split()
    return result

def format_errors(string: str):
    result = string[string.find(",")+2:]
    return result