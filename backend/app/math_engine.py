
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
    if isinstance(node, ast.Call):
        if (
            not isinstance(node.func, ast.Name)
            or node.func.id != "sqrt"
            or len(node.args) != 1
            or node.keywords
        ):
            raise ValueError(
                "Only sqrt() with one argument is supported."
            )

        argument_node = node.args[0]

        if any(
            isinstance(child, ast.Call)
            for child in ast.walk(argument_node)
        ):
            raise ValueError("Nested function calls are not supported.")

        argument = parse_node(argument_node, depth + 1)
        return sp.sqrt(argument)

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
def get_denominator_restrictions(expression: str):

    prepared = prepare_expression(expression)

    try:
        tree = ast.parse(prepared, mode="eval")
    except SyntaxError:
        raise ValueError("Invalid mathematical expression.")

    if sum(1 for _ in ast.walk(tree)) > 80:
        raise ValueError("Expression is too complex.")

    restrictions = []

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Div)
        ):
            denominator = parse_node(node.right)

            if denominator == 0:
                raise ValueError("Division by zero is not allowed.")

            restrictions.append(denominator)

    return restrictions

def format_value(value) -> str:
    return str(sp.simplify(value))


def format_substitution(shift) -> str:
    shift = sp.simplify(shift)

    if shift == 0:
        return "x = t"

    return f"x = t - {format_value(shift)}"

def get_trigonometric_cubic_roots(polynomial):
    """Return exact trigonometric roots for cubics with three distinct real roots."""

    if polynomial.degree() != 3:
        return None

    a, b, c, d = polynomial.all_coeffs()

    # The current parser supports rational numeric coefficients.
    if not all(coefficient.is_Rational for coefficient in (a, b, c, d)):
        return None

    if a == 0:
        return None

    # Convert the cubic into depressed form: t^3 + p*t + q = 0.
    p = sp.simplify((3 * a * c - b**2) / (3 * a**2))
    q = sp.simplify(
        (2 * b**3 - 9 * a * b * c + 27 * a**2 * d)
        / (27 * a**3)
    )

    discriminant = sp.simplify(-4 * p**3 - 27 * q**2)

    # This method applies to three distinct real roots.
    if not (p < 0 and discriminant > 0):
        return None

    amplitude = 2 * sp.sqrt(-p / 3)
    cosine_value = sp.simplify(
        (3 * q / (2 * p)) * sp.sqrt(-3 / p)
    )

    angle = sp.acos(cosine_value) / 3
    shift = b / (3 * a)

    roots = [
        sp.simplify(
            amplitude * sp.cos(angle - 2 * sp.pi * k / 3) - shift
        )
        for k in range(3)
    ]

    roots.sort(key=lambda root: float(sp.N(root)))
    return roots



def get_cardano_cubic_roots(polynomial):
    """Return exact roots for cubics with one real and two complex roots."""

    if polynomial.degree() != 3:
        return None

    a, b, c, d = polynomial.all_coeffs()

    if not all(
        coefficient.is_Rational
        for coefficient in (a, b, c, d)
    ):
        return None

    if a == 0:
        return None

    # Convert to depressed cubic: t^3 + p*t + q = 0.
    p = sp.simplify(
        (3 * a * c - b**2) / (3 * a**2)
    )
    q = sp.simplify(
        (2 * b**3 - 9 * a * b * c + 27 * a**2 * d)
        / (27 * a**3)
    )

    delta = sp.simplify(
        (q / 2)**2 + (p / 3)**3
    )

    # Cardano's real-root branch applies when delta is positive.
    if not (delta > 0):
        return None

    sqrt_delta = sp.sqrt(delta)

    u = sp.real_root(-q / 2 + sqrt_delta, 3)
    v = sp.real_root(-q / 2 - sqrt_delta, 3)

    shift = sp.simplify(b / (3 * a))

    omega = (-1 + sp.sqrt(3) * sp.I) / 2
    omega_squared = sp.conjugate(omega)

    roots = [
        sp.simplify(u + v - shift),
        sp.simplify(omega * u + omega_squared * v - shift),
        sp.simplify(omega_squared * u + omega * v - shift),
    ]

    return roots

def build_radical_equation_steps(lhs, rhs, solutions):
    """Build detailed steps for a simple square root on the left side."""

    if not (
        isinstance(lhs, sp.Pow)
        and lhs.exp == sp.Rational(1, 2)
        and not rhs.has(sp.sqrt(x))
    ):
        return None

    radicand = lhs.base

    try:
        sp.Poly(radicand, x)
        sp.Poly(rhs, x)
    except sp.PolynomialError:
        return None

    squared_equation = sp.expand(radicand - rhs**2)

    try:
        candidates = sp.solve(squared_equation, x)
    except (NotImplementedError, ValueError):
        return None

    if not isinstance(candidates, list) or not candidates:
        return None

    valid_values = {
        sp.simplify(solution) for solution in solutions
    }

    steps = []
    formulas = []

    steps.append(
        "Since a square root is non-negative, "
        "the right-hand side must also be non-negative."
    )
    formulas.append(
        rf"\sqrt{{{sp.latex(radicand)}}}={sp.latex(rhs)},"
        rf"\quad {sp.latex(rhs)}\geq 0"
    )

    steps.append("Square both sides of the equation.")
    formulas.append(
        rf"{sp.latex(radicand)}="
        rf"\left({sp.latex(rhs)}\right)^2"
    )

    steps.append(
        "Expand and simplify the resulting equation."
    )
    formulas.append(
        rf"{sp.latex(squared_equation)}=0"
    )

    candidate_text = ", ".join(
        format_value(candidate) for candidate in candidates
    )

    steps.append(
        f"Solving the squared equation gives candidates: "
        f"{candidate_text}."
    )
    formulas.append(
        rf"x\in\left\{{{', '.join(sp.latex(c) for c in candidates)}"
        rf"\right\}}"
    )

    for candidate in candidates:
        value = sp.simplify(candidate)

        if value in valid_values:
            steps.append(
                f"Substitute x = {format_value(value)} "
                "into the original equation. It is valid."
            )
            formulas.append(
                rf"\sqrt{{{sp.latex(radicand.subs(x, value))}}}"
                rf"={sp.latex(rhs.subs(x, value))}"
            )
        else:
            steps.append(
                f"Reject x = {format_value(value)} because it "
                "does not satisfy the original equation."
            )
            formulas.append(
                rf"\sqrt{{{sp.latex(radicand.subs(x, value))}}}"
                rf"\ne {sp.latex(rhs.subs(x, value))}"
            )

    if valid_values:
        sorted_values = sorted(
            valid_values,
            key=sp.default_sort_key,
        )

        answer_text = ", ".join(
            format_value(value)
            for value in sorted_values
        )

        steps.append(
            f"Final solution: x = {answer_text}."
        )
        formulas.append(
            rf"x\in\left\{{{', '.join(sp.latex(v) for v in sorted_values)}"
            rf"\right\}}"
        )
    else:
        steps.append(
            "None of the candidates satisfies the original equation. "
            "Therefore, no real solutions exist."
        )
        formulas.append(
            r"\text{No real solutions}"
        )

    return steps, formulas


def build_equation_steps(lhs, rhs, solutions):
    """Create genuine steps for supported linear, quadratic and cubic equations."""

    steps = []
    polynomial = sp.Poly(sp.expand(lhs - rhs), x)
    degree = polynomial.degree()

    if degree == 1:
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

    if degree == 2:
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




    if degree == 3:
        standard = polynomial.as_expr()
        factorized = sp.factor(standard)
        factor_data = sp.factor_list(standard)[1]

        total_degree = sum(
            sp.Poly(factor, x).degree() * multiplicity
            for factor, multiplicity in factor_data
        )


        # Case 0: Pure cubic equation (a*x^3 + d = 0)
        cubic_coefficients = polynomial.all_coeffs()

        if len(cubic_coefficients) == 4:
            a, b, c, d = cubic_coefficients

            if b == 0 and c == 0 and a != 0:
                cube_value = sp.simplify(-d / a)

                if cube_value != 0:
                    real_root = sp.real_root(cube_value, 3)

                    steps.append(
                        "Write the pure cubic equation in standard form: "
                        f"{sp.sstr(standard)} = 0"
                    )

                    steps.append(
                        "Isolate the cubic term: "
                        f"x^3 = {format_value(cube_value)}"
                    )

                    steps.append(
                        "Take the real cube root: "
                        f"x = {format_value(real_root)}"
                    )

                    steps.append(
                        "A non-zero number has three complex cube roots. "
                        "They are obtained using the three cube roots of unity."
                    )

                    roots_text = "; ".join(
                        format_value(solution)
                        for solution in solutions
                    )

                    steps.append(
                        "Therefore, the three solutions are: "
                        + roots_text
                    )

                    return steps

        # Case 1: All factors are linear
        if total_degree == 3 and all(
            sp.Poly(factor, x).degree() == 1
            for factor, multiplicity in factor_data
        ):
            steps.append(
                "Write the cubic equation in standard form: "
                f"{sp.sstr(standard)} = 0"
            )
            steps.append(
                f"Factorize the cubic: {sp.sstr(factorized)} = 0"
            )
            steps.append(
                "Apply the zero-product property: set each distinct "
                "linear factor equal to zero."
            )

            for factor, multiplicity in factor_data:
                factor_poly = sp.Poly(factor, x)
                factor_a, factor_b = factor_poly.all_coeffs()
                root = sp.simplify(-factor_b / factor_a)

                steps.append(
                    f"Solve {sp.sstr(factor)} = 0: "
                    f"x = {format_value(root)}"
                )

                if multiplicity > 1:
                    steps.append(
                        f"The factor {sp.sstr(factor)} occurs "
                        f"{multiplicity} times. Therefore, "
                        f"x = {format_value(root)} has "
                        f"multiplicity {multiplicity}."
                    )

            return steps

        # Case 2: One linear factor and one quadratic factor

        factor_degrees = [
            sp.Poly(factor, x).degree()
            for factor, multiplicity in factor_data
        ]

        if (
            total_degree == 3
            and sorted(factor_degrees) == [1, 2]
            and all(
                multiplicity == 1
                for factor, multiplicity in factor_data
            )
        ):
            linear_factor = next(
                factor for factor, multiplicity in factor_data
                if sp.Poly(factor, x).degree() == 1
            )

            quadratic_factor = next(
                factor for factor, multiplicity in factor_data
                if sp.Poly(factor, x).degree() == 2
            )

            factor_poly = sp.Poly(linear_factor, x)
            factor_a, factor_b = factor_poly.all_coeffs()
            linear_root = sp.simplify(-factor_b / factor_a)

            a, b, c = sp.Poly(
                quadratic_factor, x
            ).all_coeffs()

            discriminant = sp.simplify(b**2 - 4*a*c)

            root_plus = sp.simplify(
                (-b + sp.sqrt(discriminant)) / (2*a)
            )

            root_minus = sp.simplify(
                (-b - sp.sqrt(discriminant)) / (2*a)
            )

            steps.append(
                "Write the cubic equation in standard form: "
                f"{sp.sstr(standard)} = 0"
            )
            steps.append(
                f"Factorize the cubic: {sp.sstr(factorized)} = 0"
            )
            steps.append(
                "Apply the zero-product property: set the "
                "linear and quadratic factors equal to zero."
            )
            steps.append(
                f"Solve {sp.sstr(linear_factor)} = 0: "
                f"x = {format_value(linear_root)}"
            )
            steps.append(
                f"For {sp.sstr(quadratic_factor)} = 0, "
                f"identify a = {format_value(a)}, "
                f"b = {format_value(b)}, "
                f"c = {format_value(c)}."
            )
            steps.append(
                f"Calculate the discriminant: "
                f"D = {format_value(discriminant)}"
            )
            steps.append(
                "Apply the quadratic formula: "
                "x = (-b ± sqrt(D)) / (2a)."
            )
            steps.append(
                "Simplify the quadratic roots: "
                f"x = {format_value(root_plus)} "
                f"or x = {format_value(root_minus)}."
            )

            return steps

        factor_degrees = [
            sp.Poly(factor, x).degree()
            for factor, multiplicity in factor_data
        ]

        if (
            total_degree == 3
            and sorted(factor_degrees) == [1, 2]
            and all(multiplicity == 1 for factor, multiplicity in factor_data)
        ):
            linear_factor = next(
                factor for factor, multiplicity in factor_data
                if sp.Poly(factor, x).degree() == 1
            )

            quadratic_factor = next(
                factor for factor, multiplicity in factor_data
                if sp.Poly(factor, x).degree() == 2
            )

            factor_poly = sp.Poly(linear_factor, x)
            factor_a, factor_b = factor_poly.all_coeffs()
            linear_root = sp.simplify(-factor_b / factor_a)

            a, b, c = sp.Poly(
                quadratic_factor, x
            ).all_coeffs()

            discriminant = sp.simplify(b**2 - 4*a*c)

            root_plus = sp.simplify(
                (-b + sp.sqrt(discriminant)) / (2*a)
            )

            root_minus = sp.simplify(
                (-b - sp.sqrt(discriminant)) / (2*a)
            )

            steps.append(
                "Write the cubic equation in standard form: "
                f"{sp.sstr(standard)} = 0"
            )

            steps.append(
                f"Factorize the cubic: {sp.sstr(factorized)} = 0"
            )

            steps.append(
                "Apply the zero-product property: set the "
                "linear and quadratic factors equal to zero."
            )

            steps.append(
                f"Solve {sp.sstr(linear_factor)} = 0: "
                f"x = {format_value(linear_root)}"
            )

            steps.append(
                f"For {sp.sstr(quadratic_factor)} = 0, "
                f"identify a = {format_value(a)}, "
                f"b = {format_value(b)}, "
                f"c = {format_value(c)}."
            )

            steps.append(
                f"Calculate the discriminant: "
                f"D = {format_value(discriminant)}"
            )

            steps.append(
                "Apply the quadratic formula: "
                "x = (-b ± sqrt(D)) / (2a)."
            )

            steps.append(
                "Simplify the quadratic roots: "
                f"x = {format_value(root_plus)} "
                f"or x = {format_value(root_minus)}."
            )

            return steps


        # Case 3: Cubic with three distinct real roots (trigonometric method)
        trig_roots = get_trigonometric_cubic_roots(polynomial)

        if trig_roots is not None:
            a, b, c, d = polynomial.all_coeffs()

            p = sp.simplify(
                (3 * a * c - b**2) / (3 * a**2)
            )
            q = sp.simplify(
                (2 * b**3 - 9 * a * b * c + 27 * a**2 * d)
                / (27 * a**3)
            )

            discriminant = sp.simplify(-4 * p**3 - 27 * q**2)
            amplitude = 2 * sp.sqrt(-p / 3)
            cosine_value = sp.simplify(
                (3 * q / (2 * p)) * sp.sqrt(-3 / p)
            )
            angle = sp.acos(cosine_value) / 3
            shift = sp.simplify(b / (3 * a))

            steps.extend([
                f"Write the cubic equation in standard form: {sp.sstr(polynomial.as_expr())} = 0.",
                f"Remove the quadratic term using the substitution {format_substitution(shift)}.",
                f"The depressed cubic is t^3 + p*t + q = 0, where p = {format_value(p)} and q = {format_value(q)}.",
                f"Calculate the discriminant: D = -4p^3 - 27q^2 = {format_value(discriminant)}.",
                "Since D is positive, the equation has three distinct real roots.",
                f"Use the trigonometric substitution t = {format_value(amplitude)} cos(theta), where cos(3*theta) = {format_value(cosine_value)}.",
                f"The angle is theta = {format_value(angle)} radians.",
                "The three roots are obtained by using k = 0, 1, 2 in the trigonometric formula.",
                "Therefore, the three solutions are: "
                + "; ".join(format_value(root) for root in trig_roots)
                + ".",
            ])

            return steps



        # Case 4: Cubic with one real and two complex roots (Cardano method)
        cardano_roots = get_cardano_cubic_roots(polynomial)

        if cardano_roots is not None:
            a, b, c, d = polynomial.all_coeffs()

            p = sp.simplify(
                (3 * a * c - b**2) / (3 * a**2)
            )
            q = sp.simplify(
                (2 * b**3 - 9 * a * b * c + 27 * a**2 * d)
                / (27 * a**3)
            )

            delta = sp.simplify(
                (q / 2)**2 + (p / 3)**3
            )

            sqrt_delta = sp.sqrt(delta)
            u = sp.real_root(-q / 2 + sqrt_delta, 3)
            v = sp.real_root(-q / 2 - sqrt_delta, 3)

            shift = sp.simplify(b / (3 * a))
            omega = (-1 + sp.sqrt(3) * sp.I) / 2
            omega_squared = sp.conjugate(omega)

            steps.extend([
                f"Write the cubic equation in standard form: {sp.sstr(polynomial.as_expr())} = 0.",
                f"Remove the quadratic term using the substitution {format_substitution(shift)}.",
                f"The depressed cubic is t^3 + p*t + q = 0, where p = {format_value(p)} and q = {format_value(q)}.",
                f"Calculate Cardano's discriminant: delta = (q/2)^2 + (p/3)^3 = {format_value(delta)}.",
                "Since delta is positive, the equation has one real root and two non-real complex conjugate roots.",
                f"Calculate u = cube_root(-q/2 + sqrt(delta)) = {format_value(u)} and v = cube_root(-q/2 - sqrt(delta)) = {format_value(v)}, using real cube roots.",
                f"The real root is x1 = u + v - {format_value(shift)} = {format_value(cardano_roots[0])}.",
                f"Using omega = {format_value(omega)}, the two complex roots are x2 = {format_value(cardano_roots[1])} and x3 = {format_value(cardano_roots[2])}.",
                "Therefore, the three solutions are: "
                + "; ".join(format_value(root) for root in cardano_roots)
                + ".",
            ])

            return steps

    # Degree 4: Factorable and biquadratic quartic equations
    if degree == 4:
        standard = polynomial.as_expr()
        factorized = sp.factor(standard)
        factor_data = sp.factor_list(standard)[1]

        factor_degrees = [
            sp.Poly(factor, x).degree()
            for factor, multiplicity in factor_data
        ]

        total_degree = sum(
            sp.Poly(factor, x).degree() * multiplicity
            for factor, multiplicity in factor_data
        )

        # Method 1: Quartics with rational linear factors
        if total_degree == 4 and all(
            factor_degree == 1
            for factor_degree in factor_degrees
        ):
            steps.append(
                f"Write the quartic equation in standard form: "
                f"{sp.sstr(standard)} = 0."
            )

            steps.append(
                f"Factorize the polynomial: "
                f"{sp.sstr(factorized)} = 0."
            )

            steps.append(
                "Apply the zero-product property: "
                "set each linear factor equal to zero."
            )

            for factor, multiplicity in factor_data:
                factor_poly = sp.Poly(factor, x)
                factor_a, factor_b = factor_poly.all_coeffs()
                root = sp.simplify(-factor_b / factor_a)

                steps.append(
                    f"Solve {sp.sstr(factor)} = 0: "
                    f"x = {format_value(root)}."
                )

                if multiplicity > 1:
                    steps.append(
                        f"The root x = {format_value(root)} "
                        f"has multiplicity {multiplicity}."
                    )

            steps.append(
                "Therefore, the solutions are: "
                + "; ".join(
                    format_value(root) for root in solutions
                )
                + "."
            )

            return steps

        # Method 2: Biquadratic equations
        coefficients = polynomial.all_coeffs()

        if len(coefficients) == 5:
            a, b, c, d, e = coefficients

            if b == 0 and d == 0 and a != 0:
                y = sp.Symbol("y")

                y_solutions = sp.solve(
                    a * y**2 + c * y + e,
                    y
                )

                steps.append(
                    "Write the biquadratic equation in standard form: "
                    f"{sp.sstr(standard)} = 0."
                )

                steps.append(
                    "Substitute y = x^2 to convert the quartic "
                    "equation into a quadratic equation."
                )

                steps.append(
                    f"The quadratic equation becomes: "
                    f"{sp.sstr(a*y**2 + c*y + e)} = 0."
                )

                for y_value in y_solutions:
                    steps.append(
                        f"Solve the quadratic equation: "
                        f"y = {format_value(y_value)}."
                    )

                    steps.append(
                        f"Substitute y = {format_value(y_value)} "
                        f"back into x^2 = y."
                    )

                    for root in sp.solve(x**2 - y_value, x):
                        steps.append(
                            f"Therefore, x = {format_value(root)}."
                        )

                steps.append(
                    "Therefore, the quartic solutions are: "
                    + "; ".join(
                        format_value(root) for root in solutions
                    )
                    + "."
                )

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



    if degree == 3:
        standard = polynomial.as_expr()
        factorized = sp.factor(standard)
        factor_data = sp.factor_list(standard)[1]

        total_degree = sum(
            sp.Poly(factor, x).degree() * multiplicity
            for factor, multiplicity in factor_data
        )


        # Case 0: Pure cubic equation (a*x^3 + d = 0)
        cubic_coefficients = polynomial.all_coeffs()

        if len(cubic_coefficients) == 4:
            a, b, c, d = cubic_coefficients

            if b == 0 and c == 0 and a != 0:
                cube_value = sp.simplify(-d / a)

                if cube_value != 0:
                    real_root = sp.real_root(cube_value, 3)

                    formulas = [
                        sp.latex(standard) + r" = 0",

                        r"x^3 = " + sp.latex(cube_value),

                        r"x = " + sp.latex(real_root),

                        (
                            r"\omega = e^{\frac{2\pi i}{3}},"
                            r"\quad \omega^3 = 1"
                        ),

                        r"x = "
                        + r",\quad x = ".join(
                            sp.latex(solution)
                            for solution in solutions
                        ),
                    ]

                    return formulas

        if total_degree == 3 and all(
            sp.Poly(factor, x).degree() == 1
            for factor, multiplicity in factor_data
        ):
            formulas = [
                sp.latex(standard) + r" = 0",
                sp.latex(factorized) + r" = 0",
                r"\text{Set each distinct linear factor equal to zero}",
            ]

            for factor, multiplicity in factor_data:
                factor_poly = sp.Poly(factor, x)
                factor_a, factor_b = factor_poly.all_coeffs()
                root = sp.simplify(-factor_b / factor_a)

                formulas.append(
                    sp.latex(factor)
                    + r" = 0 \quad \Rightarrow \quad x = "
                    + sp.latex(root)
                )

                if multiplicity > 1:
                    formulas.append(
                        r"\text{Multiplicity of } x = "
                        + sp.latex(root)
                        + r"\text{ is } "
                        + str(multiplicity)
                    )

            return formulas

        factor_degrees = [
            sp.Poly(factor, x).degree()
            for factor, multiplicity in factor_data
        ]

        if (
            total_degree == 3
            and sorted(factor_degrees) == [1, 2]
            and all(multiplicity == 1 for factor, multiplicity in factor_data)
        ):
            linear_factor = next(
                factor for factor, multiplicity in factor_data
                if sp.Poly(factor, x).degree() == 1
            )

            quadratic_factor = next(
                factor for factor, multiplicity in factor_data
                if sp.Poly(factor, x).degree() == 2
            )

            factor_poly = sp.Poly(linear_factor, x)
            factor_a, factor_b = factor_poly.all_coeffs()
            linear_root = sp.simplify(-factor_b / factor_a)

            a, b, c = sp.Poly(
                quadratic_factor, x
            ).all_coeffs()

            discriminant = sp.simplify(b**2 - 4*a*c)

            root_plus = sp.simplify(
                (-b + sp.sqrt(discriminant)) / (2*a)
            )

            root_minus = sp.simplify(
                (-b - sp.sqrt(discriminant)) / (2*a)
            )

            return [
                sp.latex(standard) + r" = 0",

                sp.latex(factorized) + r" = 0",

                r"\text{Set the linear and quadratic factors equal to zero}",

                sp.latex(linear_factor)
                + r" = 0 \quad \Rightarrow \quad x = "
                + sp.latex(linear_root),

                sp.latex(quadratic_factor)
                + r" = 0,\quad a = "
                + sp.latex(a)
                + r",\ b = "
                + sp.latex(b)
                + r",\ c = "
                + sp.latex(c),

                r"D = " + sp.latex(discriminant),

                r"x = \frac{-b \pm \sqrt{D}}{2a}",

                r"x = "
                + sp.latex(root_plus)
                + r"\quad \text{or}\quad x = "
                + sp.latex(root_minus),
            ]


        # Case 3: Cubic with three distinct real roots (trigonometric method)
        trig_roots = get_trigonometric_cubic_roots(polynomial)

        if trig_roots is not None:
            a, b, c, d = polynomial.all_coeffs()

            p = sp.simplify(
                (3 * a * c - b**2) / (3 * a**2)
            )
            q = sp.simplify(
                (2 * b**3 - 9 * a * b * c + 27 * a**2 * d)
                / (27 * a**3)
            )

            discriminant = sp.simplify(-4 * p**3 - 27 * q**2)
            amplitude = 2 * sp.sqrt(-p / 3)
            cosine_value = sp.simplify(
                (3 * q / (2 * p)) * sp.sqrt(-3 / p)
            )
            angle = sp.acos(cosine_value) / 3
            shift = sp.simplify(b / (3 * a))

            return [
                sp.latex(polynomial.as_expr()) + r" = 0",
                (r"x = t" if shift == 0 else r"x = t - " + sp.latex(shift)),
                r"t^3 + pt + q = 0,\quad p = "
                + sp.latex(p) + r",\quad q = " + sp.latex(q),
                r"D = -4p^3 - 27q^2 = "
                + sp.latex(discriminant),
                r"D > 0 \quad \Rightarrow \quad "
                r"\text{three distinct real roots}",
                r"t = " + sp.latex(amplitude)
                + r"\cos(\theta),\quad \cos(3\theta) = "
                + sp.latex(cosine_value),
                r"\theta = " + sp.latex(angle)
                + r"\text{ radians}",
                r"t_k = " + sp.latex(amplitude)
                + r"\cos\left(\theta - \frac{2k\pi}{3}\right),"
                + r"\quad k = 0,1,2",
                r"x = " + r",\quad x = ".join(
                    sp.latex(root) for root in trig_roots
                ),
            ]


        # Case 4: Cubic with one real and two complex roots (Cardano method)
        cardano_roots = get_cardano_cubic_roots(polynomial)

        if cardano_roots is not None:
            a, b, c, d = polynomial.all_coeffs()

            p = sp.simplify(
                (3 * a * c - b**2) / (3 * a**2)
            )
            q = sp.simplify(
                (2 * b**3 - 9 * a * b * c + 27 * a**2 * d)
                / (27 * a**3)
            )

            delta = sp.simplify(
                (q / 2)**2 + (p / 3)**3
            )

            sqrt_delta = sp.sqrt(delta)
            u = sp.real_root(-q / 2 + sqrt_delta, 3)
            v = sp.real_root(-q / 2 - sqrt_delta, 3)

            shift = sp.simplify(b / (3 * a))
            omega = (-1 + sp.sqrt(3) * sp.I) / 2
            omega_squared = sp.conjugate(omega)

            return [
                sp.latex(polynomial.as_expr()) + r" = 0",
                (r"x = t" if shift == 0 else r"x = t - " + sp.latex(shift)),
                r"t^3 + pt + q = 0,\quad p = "
                + sp.latex(p) + r",\quad q = " + sp.latex(q),
                r"\Delta = \left(\frac{q}{2}\right)^2"
                + r" + \left(\frac{p}{3}\right)^3 = "
                + sp.latex(delta),
                r"\Delta > 0 \quad \Rightarrow \quad "
                r"\text{one real root and two complex roots}",
                r"u = \sqrt[3]{-\frac{q}{2}+\sqrt{\Delta}},"
                + r"\quad v = \sqrt[3]{-\frac{q}{2}-\sqrt{\Delta}}",
                r"x_1 = u + v - " + sp.latex(shift)
                + r" = " + sp.latex(cardano_roots[0]),
                r"\omega = " + sp.latex(omega)
                + r",\quad x_2 = \omega u + \omega^2 v - "
                + sp.latex(shift)
                + r",\quad x_3 = \omega^2 u + \omega v - "
                + sp.latex(shift),
                r"x = " + r",\quad x = ".join(
                    sp.latex(root) for root in cardano_roots
                ),
            ]


    # Degree 4: Factorable quartic equations
    if degree == 4:
        standard = polynomial.as_expr()
        factorized = sp.factor(standard)
        factor_data = sp.factor_list(standard)[1]

        factor_degrees = [
            sp.Poly(factor, x).degree()
            for factor, multiplicity in factor_data
        ]

        total_degree = sum(
            sp.Poly(factor, x).degree() * multiplicity
            for factor, multiplicity in factor_data
        )

        if total_degree == 4 and all(
            factor_degree == 1
            for factor_degree in factor_degrees
        ):
            formulas = [
                sp.latex(standard) + r" = 0",
                sp.latex(factorized) + r" = 0",
                r"\text{Apply the zero-product property}",
            ]

            for factor, multiplicity in factor_data:
                factor_poly = sp.Poly(factor, x)
                factor_a, factor_b = factor_poly.all_coeffs()
                root = sp.simplify(-factor_b / factor_a)

                formulas.append(
                    sp.latex(factor)
                    + r" = 0 \quad \Rightarrow \quad x = "
                    + sp.latex(root)
                )

                if multiplicity > 1:
                    formulas.append(
                        r"\text{Multiplicity} = "
                        + str(multiplicity)
                    )

            formulas.append(
                r"x = "
                + r",\quad x = ".join(
                    sp.latex(root) for root in solutions
                )
            )

            return formulas
        # Method 2: Biquadratic equations
        coefficients = polynomial.all_coeffs()

        if len(coefficients) == 5:
            a, b, c, d, e = coefficients

            if b == 0 and d == 0 and a != 0:
                y = sp.Symbol("y")

                y_solutions = sp.solve(
                    a * y**2 + c * y + e,
                    y
                )

                formulas = [
                    sp.latex(standard) + r" = 0",
                    r"\text{Substitute } y = x^2",
                    sp.latex(a*y**2 + c*y + e) + r" = 0",
                ]

                for y_value in y_solutions:
                    formulas.append(
                        r"y = " + sp.latex(y_value)
                    )

                    formulas.append(
                        r"x^2 = " + sp.latex(y_value)
                    )

                    x_roots = sp.solve(
                        x**2 - y_value,
                        x
                    )

                    for root in x_roots:
                        formulas.append(
                            r"x = " + sp.latex(root)
                        )

                formulas.append(
                    r"x = "
                    + r",\quad x = ".join(
                        sp.latex(root) for root in solutions
                    )
                )

                return formulas
    return []


def build_rational_equation_steps(
    lhs,
    rhs,
    numerator,
    denominator,
    denominator_restrictions,
    solutions,
):
    """Build detailed steps for supported rational equations."""

    if not denominator_restrictions:
        return None

    try:
        polynomial = sp.Poly(
            sp.expand(numerator),
            x,
        )

        if polynomial.degree() < 1:
            return None

        candidates = sp.solve(
            polynomial.as_expr(),
            x,
        )

        if not isinstance(candidates, list) or not candidates:
            return None

    except (sp.PolynomialError, NotImplementedError, ValueError):
        return None

    excluded_values = set()

    try:
        for restriction in denominator_restrictions:
            restriction_roots = sp.solve(restriction, x)

            if not isinstance(restriction_roots, list):
                return None

            excluded_values.update(
                sp.simplify(value)
                for value in restriction_roots
            )

    except (NotImplementedError, ValueError):
        return None

    valid_values = {
        sp.simplify(value)
        for value in solutions
    }

    steps = []
    formulas = []

    steps.append(
        "Write down the original rational equation."
    )
    formulas.append(
        sp.latex(lhs) + " = " + sp.latex(rhs)
    )

    if excluded_values:
        excluded_text = ", ".join(
            format_value(value)
            for value in sorted(
                excluded_values,
                key=sp.default_sort_key,
            )
        )

        steps.append(
            "Identify denominator restrictions: "
            f"x cannot equal {excluded_text}."
        )

        formulas.append(
            r"x \ne "
            + r",\quad x \ne ".join(
                sp.latex(value)
                for value in sorted(
                    excluded_values,
                    key=sp.default_sort_key,
                )
            )
        )

    else:
        return None

    steps.append(
        "Combine the equation into a single rational expression."
    )

    formulas.append(
        r"\frac{"
        + sp.latex(numerator)
        + r"}{"
        + sp.latex(denominator)
        + r"} = 0"
    )

    steps.append(
        "Set the numerator equal to zero, while keeping "
        "the denominator restrictions."
    )

    formulas.append(
        sp.latex(numerator) + " = 0"
    )

    candidate_text = ", ".join(
        format_value(value)
        for value in candidates
    )

    steps.append(
        f"Solving the numerator equation gives candidates: "
        f"{candidate_text}."
    )

    formulas.append(
        r"x \in \left\{"
        + ", ".join(
            sp.latex(value)
            for value in candidates
        )
        + r"\right\}"
    )

    for candidate in candidates:
        value = sp.simplify(candidate)

        is_excluded = any(
            sp.simplify(value - excluded) == 0
            for excluded in excluded_values
        )

        if is_excluded:
            steps.append(
                f"Reject x = {format_value(value)} because "
                "it makes an original denominator zero."
            )

            formulas.append(
                r"x = "
                + sp.latex(value)
                + r"\quad \Rightarrow \quad "
                r"\text{Invalid}"
            )

        else:
            verification = sp.checksol(
                lhs - rhs,
                x,
                value,
            )

            if verification is not True or value not in valid_values:
                return None

            steps.append(
                f"Accept x = {format_value(value)} because "
                "it satisfies the original equation."
            )

            formulas.append(
                r"x = "
                + sp.latex(value)
                + r"\quad \Rightarrow \quad "
                r"\text{Valid}"
            )

    if valid_values:
        final_values = sorted(
            valid_values,
            key=sp.default_sort_key,
        )

        final_text = ", ".join(
            format_value(value)
            for value in final_values
        )

        steps.append(
            f"Final solution: x = {final_text}."
        )

        formulas.append(
            r"x = "
            + r",\quad x = ".join(
                sp.latex(value)
                for value in final_values
            )
        )

    else:
        steps.append(
            "No candidates satisfy the original rational equation. "
            "Therefore, no solutions exist."
        )

        formulas.append(
            r"\text{No solutions}"
        )

    if len(steps) != len(formulas):
        return None

    return steps, formulas


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

            denominator_restrictions = (
                get_denominator_restrictions(left)
                + get_denominator_restrictions(right)
            )

            difference = sp.simplify(lhs - rhs)

            # Identity equation: 0 = 0
            if difference == 0:
                excluded_values = set()
                unknown_restrictions = False

                for restriction in denominator_restrictions:
                    restriction_numerator = sp.together(
                        restriction
                    ).as_numer_denom()[0]

                    try:
                        restriction_solutions = sp.solveset(
                            restriction_numerator,
                            x,
                            domain=sp.S.Reals,
                        )

                        if isinstance(
                            restriction_solutions,
                            sp.FiniteSet,
                        ):
                            excluded_values.update(
                                sp.simplify(item)
                                for item in restriction_solutions
                            )

                        elif restriction_solutions != sp.EmptySet:
                            unknown_restrictions = True

                    except (NotImplementedError, ValueError):
                        unknown_restrictions = True

                excluded_values = sorted(
                    excluded_values,
                    key=sp.default_sort_key,
                )

                if unknown_restrictions:
                    answer = [
                        "All real values of x satisfying the original denominator restrictions"
                    ]
                elif excluded_values:
                    excluded_text = ", ".join(
                        f"x = {format_value(item)}"
                        for item in excluded_values
                    )

                    answer = [
                        f"All real values of x except {excluded_text}"
                    ]
                else:
                    answer = ["All values of x"]

                steps = [
                    "Simplify both sides: 0 = 0",
                ]

                step_formulas = [
                    r"0 = 0",
                ]

                if excluded_values:
                    excluded_text = ", ".join(
                        f"x = {format_value(item)}"
                        for item in excluded_values
                    )

                    steps.append(
                        "Exclude these values because they make "
                        f"an original denominator zero: {excluded_text}."
                    )

                    step_formulas.append(
                        r"\text{Excluded values: } "
                        + r",\ ".join(
                            sp.latex(item)
                            for item in excluded_values
                        )
                    )

                steps.append(
                    "The identity is true for every remaining "
                    "allowed real value of x."
                )

                step_formulas.append(
                    r"\text{True for all allowed } x"
                )

                return {
                    "success": True,
                    "type": "equation",
                    "problem": problem,
                    "answer": answer,
                    "steps": steps,
                    "step_formulas": step_formulas,
                    "verified": True,
                    "message": (
                        "Identity equation: infinitely many "
                        "allowed solutions."
                    ),
                }

            # Constant contradiction
            if not difference.has(x):
                return {
                    "success": True,
                    "type": "equation",
                    "problem": problem,
                    "answer": [],
                    "steps": [
                        f"Simplify the equation: {sp.sstr(difference)} = 0",
                        "This is a contradiction, so no value of x satisfies the equation.",
                    ],
                    "step_formulas": [
                        sp.latex(difference) + r" = 0",
                        r"\text{No solution}",
                    ],
                    "verified": True,
                    "message": "No solutions exist for this equation.",
                }
            # Handle square-root equations separately over the real numbers.
            has_square_root = any(
                power.exp in (
                    sp.Rational(1, 2),
                    sp.Rational(-1, 2),
                )
                for expression in (lhs, rhs)
                for power in expression.atoms(sp.Pow)
            )

            if has_square_root:
                try:
                    radical_result = sp.solveset(
                        lhs - rhs,
                        x,
                        domain=sp.S.Reals,
                    )
                except (NotImplementedError, ValueError):
                    raise ValueError(
                        "Unable to solve this square-root equation exactly."
                    )

                if radical_result == sp.EmptySet:
                    radical_solutions = []

                elif isinstance(radical_result, sp.FiniteSet):
                    radical_solutions = sorted(
                        radical_result,
                        key=sp.default_sort_key,
                    )

                else:
                    raise ValueError(
                        "This square-root equation is not yet supported."
                    )

                valid_solutions = []

                for item in radical_solutions:
                    verification = sp.checksol(
                        lhs - rhs,
                        x,
                        item,
                    )

                    if verification is False:
                        continue

                    if verification is not True:
                        raise ValueError(
                            "Unable to verify a square-root solution."
                        )

                    denominator_invalid = False

                    for restriction in denominator_restrictions:
                        denominator_value = sp.simplify(
                            restriction.subs(x, item)
                        )

                        is_zero = denominator_value.equals(0)

                        if is_zero is None:
                            raise ValueError(
                                "Unable to verify a denominator restriction."
                            )

                        if is_zero:
                            denominator_invalid = True
                            break

                    if not denominator_invalid:
                        valid_solutions.append(item)

                answer = [
                    format_value(item)
                    for item in valid_solutions
                ]

                radical_steps = build_radical_equation_steps(
                    lhs,
                    rhs,
                    valid_solutions,
                )

                if radical_steps is None:
                    steps = []
                    step_formulas = []
                else:
                    steps, step_formulas = radical_steps

                return {
                    "success": True,
                    "type": "equation",
                    "problem": problem,
                    "answer": answer,
                    "answer_formulas": [
                        sp.latex(item)
                        for item in valid_solutions
                    ],
                    "answer_approximations": [
                        str(sp.N(item, 10))
                        for item in valid_solutions
                    ],
                    "steps": steps,
                    "step_formulas": step_formulas,
                    "verified": True,
                    "message": (
                        "Square-root equation solved successfully."
                        if valid_solutions and steps
                        else (
                            "Square-root equation solved successfully. "
                            "Detailed steps are not currently available."
                            if valid_solutions
                            else "No real solutions exist for this equation."
                        )
                    ),
                }

            # Combine rational expressions and solve the numerator.
            combined_equation = sp.together(lhs - rhs)
            numerator, denominator = combined_equation.as_numer_denom()

            polynomial = sp.Poly(sp.expand(numerator), x)

            solutions = get_trigonometric_cubic_roots(polynomial)

            if solutions is None:
                solutions = get_cardano_cubic_roots(polynomial)

            if solutions is None:
                solutions = sp.solve(sp.Eq(lhs, rhs), x)

            # Remove roots that make an original denominator zero.
            valid_solutions = []

            for item in solutions:
                valid = True

                for restriction in denominator_restrictions:
                    denominator_value = sp.simplify(
                        restriction.subs(x, item)
                    )

                    # Accept only when non-zero is established.
                    if denominator_value.equals(0) is not False:
                        valid = False
                        break

                if valid:
                    valid_solutions.append(item)

            solutions = valid_solutions

            answer = [
                format_value(item)
                for item in solutions
            ]

            answer_formulas = [
                sp.latex(item)
                for item in solutions
            ]

            answer_approximations = [
                str(sp.N(item, 10))
                for item in solutions
            ]

            verified = bool(solutions) and all(
                sp.checksol(lhs - rhs, x, item) is True
                for item in solutions
            )

            rational_steps = build_rational_equation_steps(
                lhs,
                rhs,
                numerator,
                denominator,
                denominator_restrictions,
                solutions,
            )

            if rational_steps is not None:
                steps, step_formulas = rational_steps

            else:
                try:
                    steps = build_equation_steps(
                        lhs,
                        rhs,
                        solutions,
                    )
                except (
                    sp.PolynomialError,
                    ValueError,
                    TypeError,
                ):
                    steps = []

                try:
                    step_formulas = build_equation_step_formulas(
                        lhs,
                        rhs,
                        solutions,
                    )
                except (
                    sp.PolynomialError,
                    ValueError,
                    TypeError,
                ):
                    step_formulas = []
            detailed_steps_available = bool(steps) and (
                len(steps) == len(step_formulas)
            )

            return {
                "success": True,
                "type": "equation",
                "problem": problem,
                "answer": answer,
                "answer_formulas": answer_formulas,
                "answer_approximations": answer_approximations,
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
                ),
            }

        # Expression simplification
        expression = parse_math_expression(problem)
        simplified = sp.simplify(expression)

        return {
            "success": True,
            "type": "expression",
            "problem": problem,
            "answer": str(simplified),
            "steps": [
                f"Original expression: {problem}",
                f"Simplified expression: {sp.sstr(simplified)}",
            ],
            "verified": True,
            "message": "Expression simplified successfully.",
        }

    except ValueError:
        raise

    except Exception:
        raise ValueError(
            "Unable to solve this problem. Please check your expression."
        )
