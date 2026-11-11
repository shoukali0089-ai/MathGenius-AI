
import re
import sympy as sp

from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

x = sp.Symbol("x")

TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def parse_math_expression(expression: str):
    return parse_expr(
        expression,
        local_dict={"x": x},
        transformations=TRANSFORMATIONS,
    )


def solve_math(problem: str) -> dict:
    if not isinstance(problem, str):
        raise ValueError("Problem must be text.")

    problem = problem.strip()

    if not problem:
        raise ValueError("Please enter a mathematics problem.")

    if len(problem) > 200:
        raise ValueError("Problem is too long. Maximum 200 characters.")

    if not re.fullmatch(r"[0-9xX+\-*/^().=\s]+", problem):
        raise ValueError(
            "Only numbers, x, brackets and basic operators are supported."
        )

    problem = problem.replace("X", "x")

    if problem.count("=") > 1:
        raise ValueError("Only one equation is supported.")

    try:
        if "=" in problem:
            left, right = problem.split("=")

            if not left.strip() or not right.strip():
                raise ValueError("Invalid equation.")

            lhs = parse_math_expression(left)
            rhs = parse_math_expression(right)

            solutions = sp.solve(sp.Eq(lhs, rhs), x)

            answer = [str(item) for item in solutions]

            verified = all(
                sp.simplify(lhs.subs(x, item) - rhs.subs(x, item)) == 0
                for item in solutions
            )

            return {
                "success": True,
                "type": "equation",
                "problem": problem,
                "answer": answer,
                "verified": verified,
                "message": "Equation solved successfully."
            }

        expression = parse_math_expression(problem)
        simplified = sp.simplify(expression)

        return {
            "success": True,
            "type": "expression",
            "problem": problem,
            "answer": str(simplified),
            "verified": True,
            "message": "Expression simplified successfully."
        }

    except ValueError:
        raise
    except Exception:
        raise ValueError(
            "Unable to solve this problem. Please check your expression."
        )
