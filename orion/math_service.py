import ast
import operator
import re
from decimal import Decimal, DivisionByZero, InvalidOperation, getcontext

getcontext().prec = 28

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
MATH_HINTS = ("calcule", "calcular", "conta", "quanto e", "quanto é", "resultado")


def answer_math(message):
    expression = extract_expression(message)
    if not expression:
        return None
    try:
        result = evaluate_expression(expression)
    except (ArithmeticError, ValueError, SyntaxError, TypeError, InvalidOperation, DivisionByZero):
        return None
    return f"Analise concluida. {expression} = {format_decimal(result)}."


def extract_expression(message):
    text = normalize_math_words(str(message or "").strip().lower())
    if not looks_like_math(text):
        return None
    match = re.search(r"[\d\s+\-*/%().,]*\d[\d\s+\-*/%().,]*[+\-*/%][\d\s+\-*/%().,]*\d[\d\s+\-*/%().,]*", text)
    if not match:
        return None
    expression = re.sub(r"\s+", "", match.group(0).strip()).replace(",", ".")
    if len(expression) > 80 or not re.search(r"\d", expression):
        return None
    if not re.fullmatch(r"[\d+\-*/%().]+", expression):
        return None
    if not re.search(r"[+\-*/%]", expression):
        return None
    return expression


def normalize_math_words(text):
    text = re.sub(r"(?<=\d)\s*x\s*(?=\d)", "*", text)
    replacements = {
        "×": "*",
        "÷": "/",
        "mais": "+",
        "menos": "-",
        "vezes": "*",
        "multiplicado por": "*",
        "dividido por": "/",
    }
    for word, symbol in replacements.items():
        text = re.sub(rf"\b{re.escape(word)}\b", symbol, text)
    return text


def looks_like_math(text):
    has_operator = bool(re.search(r"\d\s*[+\-*/%]\s*\d", text))
    has_hint = any(hint in text for hint in MATH_HINTS)
    return has_operator or has_hint


def evaluate_expression(expression):
    tree = ast.parse(expression, mode="eval")
    return evaluate_node(tree.body)


def evaluate_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Decimal(str(node.value))
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        left = evaluate_node(node.left)
        right = evaluate_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 8:
            raise ValueError("exponent too large")
        return OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
        return UNARY_OPS[type(node.op)](evaluate_node(node.operand))
    raise ValueError("unsupported expression")


def format_decimal(value):
    if value == value.to_integral_value():
        return str(value.quantize(Decimal(1)))
    return format(value.normalize(), "f").rstrip("0").rstrip(".")
