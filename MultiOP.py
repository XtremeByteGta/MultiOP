# MultiOP.py
import ply.lex as lex
import ply.yacc as yacc

# --- Лексер ---
tokens = (
    'NUMBER', 'STRING', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'EQUALS', 'LET', 'PRINT',
    'LSS', 'GTR', 'EQ', 'AND', 'OR', 'NOT', 'ID', 'LPAREN', 'RPAREN', 'IF', 'WHILE',
    'DEF', 'COMMA'
)

reserved = {'let': 'LET', 'print': 'PRINT', 'and': 'AND', 'or': 'OR', 'not': 'NOT',
            'if': 'IF', 'while': 'WHILE', 'def': 'DEF'}

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_EQUALS = r'='
t_LSS = r'<'
t_GTR = r'>'
t_EQ = r'=='
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]  # Убираем кавычки
    return t

def t_COMMENT(t):
    r'\#.*'
    pass  # Игнорируем комментарии

t_ignore = ' \t\n'

def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()

# --- Парсер ---
variables = {}
functions = {}

# Приоритеты операторов для устранения shift/reduce конфликтов
precedence = (
    ('left', 'OR', 'AND'),
    ('left', 'LSS', 'GTR', 'EQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'NOT'),
)

def p_program(p):
    '''program : statement
               | program statement'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_statement_let(p):
    'statement : LET ID EQUALS expression'
    p[0] = ('let', p[2], p[4])

def p_statement_print(p):
    'statement : PRINT expression'
    p[0] = ('print', p[2])

def p_statement_if(p):
    'statement : IF expression statement'
    p[0] = ('if', p[2], p[3])

def p_statement_while(p):
    'statement : WHILE expression statement'
    p[0] = ('while', p[2], p[3])

def p_statement_def(p):
    'statement : DEF ID LPAREN id_list RPAREN statement'
    p[0] = ('def', p[2], p[4], p[6])

def p_statement_call(p):
    'statement : ID LPAREN expr_list RPAREN'
    p[0] = ('call', p[1], p[3])

def p_id_list(p):
    '''id_list : ID
               | id_list COMMA ID'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_expr_list(p):
    '''expr_list : expression
                 | expr_list COMMA expression'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression LSS expression
                  | expression GTR expression
                  | expression EQ expression
                  | expression AND expression
                  | expression OR expression'''
    p[0] = (p[2], p[1], p[3])

def p_expression_not(p):
    'expression : NOT expression'
    p[0] = ('not', p[2])

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

def p_expression_number(p):
    'expression : NUMBER'
    p[0] = p[1]

def p_expression_string(p):
    'expression : STRING'
    p[0] = p[1]

def p_expression_id(p):
    'expression : ID'
    p[0] = p[1]

def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}'")

parser = yacc.yacc()

# --- Интерпретатор ---
def evaluate(expr):
    try:
        if isinstance(expr, int):
            return expr
        if isinstance(expr, str) and expr not in variables:
            return expr  # Строка как литерал
        if isinstance(expr, str):
            return variables.get(expr, 0)
        op = expr[0]
        if op == '+':
            left, right = evaluate(expr[1]), evaluate(expr[2])
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
        elif op == '-':
            return evaluate(expr[1]) - evaluate(expr[2])
        elif op == '*':
            return evaluate(expr[1]) * evaluate(expr[2])
        elif op == '/':
            right = evaluate(expr[2])
            if right == 0:
                raise ValueError("Division by zero")
            return evaluate(expr[1]) / right
        elif op == '<':
            return evaluate(expr[1]) < evaluate(expr[2])
        elif op == '>':
            return evaluate(expr[1]) > evaluate(expr[2])
        elif op == '==':
            return evaluate(expr[1]) == evaluate(expr[2])
        elif op == 'and':
            return evaluate(expr[1]) and evaluate(expr[2])
        elif op == 'or':
            return evaluate(expr[1]) or evaluate(expr[2])
        elif op == 'not':
            return not evaluate(expr[1])
    except Exception as e:
        return f"Error: {str(e)}"

def execute(code):
    """Выполняет код MultiOp и возвращает вывод как строку."""
    ast = parser.parse(code)
    if not ast:
        return "Error: Invalid code"
    output = []
    for stmt in ast:
        if isinstance(stmt, str) and stmt.startswith("Error"):
            return stmt
        if stmt[0] == 'let':
            variables[stmt[1]] = evaluate(stmt[2])
        elif stmt[0] == 'print':
            result = evaluate(stmt[1])
            if isinstance(result, str) and result.startswith("Error"):
                return result
            output.append(str(result))
        elif stmt[0] == 'if':
            if evaluate(stmt[1]):
                result = execute([stmt[2]])
                if isinstance(result, str) and result.startswith("Error"):
                    return result
                output.extend(result.split('\n'))
        elif stmt[0] == 'while':
            while evaluate(stmt[1]):
                result = execute([stmt[2]])
                if isinstance(result, str) and result.startswith("Error"):
                    return result
                output.extend(result.split('\n'))
        elif stmt[0] == 'def':
            functions[stmt[1]] = (stmt[2], stmt[3])  # Параметры, тело
        elif stmt[0] == 'call':
            fname = stmt[1]
            args = [evaluate(arg) for arg in stmt[2]]
            if fname in functions:
                params, body = functions[fname]
                old_vars = variables.copy()
                for param, arg in zip(params, args):
                    variables[param] = arg
                result = execute([body])
                variables.clear()
                variables.update(old_vars)
                if isinstance(result, str) and result.startswith("Error"):
                    return result
                output.extend(result.split('\n'))
    return '\n'.join(output)

if __name__ == "__main__":
    code = """
    let x = 5
    let msg = "Hello"
    print msg + " world"
    if x > 0
        print x
    while x > 0
        print x
        let x = x - 1
    def add(a, b)
        print a + b
    add(3, 4)
    """
    print(execute(code))