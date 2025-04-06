import ply.lex as lex
import ply.yacc as yacc

# --- Лексер ---
tokens = (
    'NUMBER', 'STRING', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'EQUALS', 'LET', 'PRINT',
    'LSS', 'GTR', 'EQ', 'AND', 'OR', 'NOT', 'ID', 'LPAREN', 'RPAREN', 'IF', 'WHILE',
    'DEF', 'COMMA', 'LBRACK', 'RBRACK', 'NEWLINE', 'INDENT', 'DEDENT'
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
t_LBRACK = r'\['
t_RBRACK = r'\]'

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

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.lexer.at_line_start = True
    return t

def t_indent(t):
    r'[ \t]+'
    if not t.lexer.at_line_start:
        return None
    indent = 0
    for char in t.value:
        if char == ' ':
            indent += 1
        elif char == '\t':
            indent += 4  # Предполагаем, что таб = 4 пробела
    current_indent = t.lexer.indent_level[-1]
    if indent > current_indent:
        t.type = 'INDENT'
        t.value = indent
        t.lexer.indent_level.append(indent)
        return t
    elif indent < current_indent:
        t.type = 'DEDENT'
        t.value = indent
        t.lexer.indent_level.pop()
        return t
    return None

t_ignore = ' \t'

def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

lexer = lex.lex()
lexer.indent_level = [0]  # Инициализация уровня отступов
lexer.at_line_start = True  # Флаг начала строки

# --- Парсер ---
variables = {}
functions = {}

precedence = (
    ('left', 'OR', 'AND'),
    ('left', 'LSS', 'GTR', 'EQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'NOT'),
)

def p_program(p):
    '''program : statement_list'''
    p[0] = p[1]

def p_statement_list(p):
    '''statement_list : statement
                      | statement_list NEWLINE statement
                      | statement_list NEWLINE'''
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 3:
        p[0] = p[1]  # Игнорируем лишние NEWLINE
    else:
        p[0] = p[1] + [p[3]]

def p_block(p):
    '''block : INDENT statement_list DEDENT'''
    p[0] = p[2]

def p_statement_let(p):
    'statement : LET ID EQUALS expression'
    p[0] = ('let', p[2], p[4])

def p_statement_print(p):
    'statement : PRINT expression'
    p[0] = ('print', p[2])

def p_statement_if(p):
    'statement : IF expression NEWLINE block'
    p[0] = ('if', p[2], p[4])

def p_statement_while(p):
    'statement : WHILE expression NEWLINE block'
    p[0] = ('while', p[2], p[4])

def p_statement_def(p):
    'statement : DEF ID LPAREN id_list RPAREN NEWLINE block'
    p[0] = ('def', p[2], p[4], p[7])

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

def p_expression_list_literal(p):
    'expression : LBRACK expr_list RBRACK'
    p[0] = ('list', p[2])

def p_expression_index(p):
    'expression : expression LBRACK expression RBRACK'
    p[0] = ('index', p[1], p[3])

def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}' on line {p.lineno}")
    else:
        print("Syntax error at EOF")

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
        elif op == 'list':
            return [evaluate(e) for e in expr[1]]
        elif op == 'index':
            lst = evaluate(expr[1])
            idx = evaluate(expr[2])
            return lst[idx]
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
                result = execute(stmt[2])
                if isinstance(result, str) and result.startswith("Error"):
                    return result
                output.extend(result.split('\n'))
        elif stmt[0] == 'while':
            while evaluate(stmt[1]):
                result = execute(stmt[2])
                if isinstance(result, str) and result.startswith("Error"):
                    return result
                output.extend(result.split('\n'))
        elif stmt[0] == 'def':
            functions[stmt[1]] = (stmt[2], stmt[3])
        elif stmt[0] == 'call':
            fname = stmt[1]
            args = [evaluate(arg) for arg in stmt[2]]
            if fname in functions:
                params, body = functions[fname]
                old_vars = variables.copy()
                for param, arg in zip(params, args):
                    variables[param] = arg
                result = execute(body)
                variables.clear()
                variables.update(old_vars)
                if isinstance(result, str) and result.startswith("Error"):
                    return result
                output.extend(result.split('\n'))
    return '\n'.join(output)

if __name__ == "__main__":
    code = """
    let x = 5
    let lst = [10, 20, 30]
    if x > 0
        print "Positive"
        print lst[1]
    while x > 0
        print x
        let x = x - 1
    def add(a, b)
        print a + b
    add(3, 4)
    """
    print(execute(code))
