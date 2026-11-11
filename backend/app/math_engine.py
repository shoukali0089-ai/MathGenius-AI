
import ast
import re

import sympy as sp


x = sp.Symbol("x")


def prepare_expression(expression: str) -> str:
    """Normalize basic mathematical notation without evaluating code."""

    expression = expression.strip()
    expression = expression.replace("^", "**")
    expression = expression.replace("X", "x")

    # Support common implicit multiplication: 5x, 2(x+1), (x+1)(x-1).
    expression = re.sub(r"(?<=\d)(?=x\b)", "*", expression)
    expression = re.sub(r"(?<=x)(?=\d)", "*", expression)
    expression = re.sub(r"(?<=[0-9x)])(?=\()", "*", expression)
    expression = re.sub(r"(?<=\))(?=[0-9x(])", "*", expression)

    return expression


def parse_node(node, depth=0):
    """Convert only explicitly allowed AST nodes into SymPy expressions."""

    if depth > 30:
        raise ValueError("Expression is too deeply nested.")

    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise ValueError("Boolean values are not supported.")

        if isinstance(node.value, (int, float)):
            return sp.Rational(str(node.value))

        raise ValueError("Only numeric values are supported.")

    if isinstance(node, ast.Name):
        if node.id == "x":
            return x
        raise ValueError("Only the variable x is supported.")

    if isinstance(node, ast.UnaryOp):
        value = parse_node(node.operand, depth + 1)

        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value

        raise ValueError("Unsupported unary operator.")

    if isinstance(node, ast.BinOp):
        left = parse_node(node.left, depth + 1)
        right = parse_node(node.right, depth + 1)

        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ValueError("Division by zero is not allowed.")
            return left / right

        if isinstance(node.op, ast.Pow):
            if not right.is_number:
                raise ValueError("Variable exponents are not supported yet.")

            if abs(float(right)) > 20:
                raise ValueError("Exponent is too large. Maximum is 20.")

            return left ** right

        raise ValueError("Unsupported mathematical operator.")

    raise ValueError("Unsupported expression syntax.")


def parse_math_expression(expression: str):
    prepared = prepare_expression(expression)

    try:
        tree = ast.parse(prepared, mode="eval")
    except SyntaxError:
        raise ValueError("Invalid mathematical expression.")

    if sum(1 for _ in ast.walk(tree)) > 80:
        raise ValueError("Expression is too complex.")

    return parse_node(tree.body)


def format_value(value) -> str:
    return str(sp.simplify(value))


def build_equation_steps(lhs, rhs, solutions):
    """Create genuine steps for supported linear and quadratic equations."""

    steps = []
    polynomial = sp.Poly(sp.expand(lhs - rhs), x)

    if polynomial.degree() == 1:
        a, b = polynomial.all_coeffs()
        solution = sp.simplify(-b / a)

        steps.append(
            f"Move all terms to one side: {format_value(a)}*x "
            f"+ ({format_value(b)}) = 0"
        )
        steps.append(
            f"Move the constant term: {format_value(a)}*x "
            f"= {format_value(-b)}"
        )
        steps.append(
            f"Divide by {format_value(a)}: x = {format_value(solution)}"
        )

        return steps

    if polynomial.degree() == 2:
        a, b, c = polynomial.all_coeffs()

        steps.append(
            "Write the equation in standard form: "
            f"{format_value(a)}*x^2 + ({format_value(b)})*x "
            f"+ ({format_value(c)}) = 0"
        )

        factorized = sp.factor(polynomial.as_expr())

        if isinstance(factorized, sp.Mul):
            factors = sp.Mul.make_args(factorized)
            linear_factors = [
                factor for factor in factors
                if sp.Poly(factor, x).degree() == 1
            ]

            if len(linear_factors) == 2:
                steps.append(
                    f"Factorize the quadratic: {sp.sstr(factorized)} = 0"
                )
                steps.append(
                    "Apply the zero-product property: set each "
                    "linear factor equal to zero."
                )

                for factor in linear_factors:
                    factor_poly = sp.Poly(factor, x)
                    factor_a, factor_b = factor_poly.all_coeffs()
                    root = sp.simplify(-factor_b / factor_a)
                    steps.append(
                        f"Solve {sp.sstr(factor)} = 0: x = "
                        f"{format_value(root)}"
                    )

                return steps

        discriminant = sp.simplify(b**2 - 4*a*c)

        steps.append(
            "Use the quadratic formula: "
            "x = (-b ± sqrt(b^2 - 4ac)) / (2a)"
        )
        steps.append(
            f"Calculate the discriminant: D = {format_value(discriminant)}"
        )
        steps.append(
            "Substitute the coefficients into the quadratic formula "
            "and simplify."
        )

        for solution in solutions:
            steps.append(f"One solution is x = {format_value(solution)}")

        return steps

    return []



def build_equation_step_formulas(lhs, rhs, solutions):
    """Generate one LaTeX formula for each equation explanation step."""

    polynomial = sp.Poly(sp.expand(lhs - rhs), x)
    degree = polynomial.degree()

    if degree == 1:
        a, b = polynomial.all_coeffs()
        solution = sp.simplify(-b / a)

        return [
            sp.latex(a * x + b) + r" = 0",
            sp.latex(a * x) + " = " + sp.latex(-b),
            r"x = " + sp.latex(solution),
        ]

    if degree == 2:
        a, b, c = polynomial.all_coeffs()
        standard = a * x**2 + b * x + c
        factorized = sp.factor(standard)

        formulas = [
            sp.latex(standard) + r" = 0"
        ]

        if isinstance(factorized, sp.Mul):
            factors = [
                factor for factor in sp.Mul.make_args(factorized)
                if sp.Poly(factor, x).degree() == 1
            ]

            if len(factors) == 2:
                formulas.append(sp.latex(factorized) + r" = 0")

                formulas.append(
                    sp.latex(factors[0]) + r" = 0"
                    + r"\quad \text{or}\quad "
                    + sp.latex(factors[1]) + r" = 0"
                )

                for factor in factors:
                    factor_poly = sp.Poly(factor, x)
                    factor_a, factor_b = factor_poly.all_coeffs()
                    root = sp.simplify(-factor_b / factor_a)

                    formulas.append(
                        sp.latex(factor) + r" = 0"
                        + r"\quad \Rightarrow \quad x = "
                        + sp.latex(root)
                    )

                return formulas

        discriminant = sp.simplify(b**2 - 4*a*c)

        formulas.append(
            r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}"
        )

        formulas.append(
            r"D = " + sp.latex(discriminant)
        )

        formulas.append(
            r"x = \frac{-("
            + sp.latex(b)
            + r") \pm \sqrt{"
            + sp.latex(discriminant)
            + r"}}{2("
            + sp.latex(a)
            + r")}"
        )

        for solution in solutions:
            formulas.append(
                r"x = " + sp.latex(solution)
            )

        return formulas



    return []

def solve_math(problem: str) -> dict:
    if not isinstance(problem, str):
        raise ValueError("Problem must be text.")

    problem = problem.strip()

    if not problem:
        raise ValueError("Please enter a mathematics problem.")

    if len(problem) > 200:
        raise ValueError("Problem is too long. Maximum 200 characters.")

    if problem.count("=") > 1:
        raise ValueError("Only one equation is supported.")

    try:
        if "=" in problem:
            left, right = problem.split("=")

            if not left.strip() or not right.strip():
                raise ValueError("Invalid equation.")


            lhs = parse_math_expression(left)
            rhs = parse_math_expression(right)

            difference = sp.simplify(lhs - rhs)

            if difference == 0:
                return {
                    "success": True,
                    "type": "equation",
                    "problem": problem,
                    "answer": ["All values of x"],
                    "steps": [
                        "Simplify both sides: 0 = 0",
                        "This identity is true for every value of x."
                    ],
                    "step_formulas": [
                        r"0 = 0",
                        r"\text{True for all } x"
                    ],
                    "verified": True,
                    "message": "Identity equation: infinitely many solutions."
                }

            if not difference.has(x):
                return {
                    "success": True,
                    "type": "equation",
                    "problem": problem,
                    "answer": [],
                    "steps": [
                        f"Simplify the equation: {sp.sstr(difference)} = 0",
                        "This is a contradiction, so no value of x satisfies the equation."
                    ],
                    "step_formulas": [
                        sp.latex(difference) + r" = 0",
                        r"\text{No solution}"
                    ],
                    "verified": True,
                    "message": "No solutions exist for this equation."
                }

            solutions = sp.solve(sp.Eq(lhs, rhs), x)


            answer = [format_value(item) for item in solutions]

            verified = bool(solutions) and all(
                sp.simplify(lhs.subs(x, item) - rhs.subs(x, item)) == 0
                for item in solutions
            )

            try:
                steps = build_equation_steps(lhs, rhs, solutions)
            except (sp.PolynomialError, ValueError, TypeError):
                steps = []

            try:
                step_formulas = build_equation_step_formulas(
                    lhs, rhs, solutions
                )
            except (sp.PolynomialError, ValueError, TypeError):
                step_formulas = []
            detailed_steps_available = bool(steps) and (
                len(steps) == len(step_formulas)
            )

            return {
                "success": True,
                "type": "equation",
                "problem": problem,
                "answer": answer,
                "steps": steps,
                "step_formulas": step_formulas,
                "verified": verified,
                "message": (
                    "Equation solved successfully."
                    if solutions and detailed_steps_available
                    else (
                        "Equation solved, but detailed steps "
                        "are not currently available for this equation."
                        if solutions
                        else "No solutions found for this equation."
                    )
                )
            }

        expression = parse_math_expression(problem)
        simplified = sp.simplify(expression)

        return {
            "success": True,
            "type": "expression",
            "problem": problem,
            "answer": str(simplified),
            "steps": [
                f"Original expression: {problem}",
                f"Simplified expression: {sp.sstr(simplified)}"
            ],
            "verified": True,
            "message": "Expression simplified successfully."
        }

    except ValueError:
        raise
    except Exception:
        raise ValueError(
            "Unable to solve this problem. Please check your expression."
        )