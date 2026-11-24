import pytest
import sympy as sp

from backend.app.math_engine import (
    format_substitution,
    parse_math_expression,
    solve_math,
)


def test_square_root_expression_parsing():
    result = parse_math_expression("sqrt(x+5)")

    assert result == sp.sqrt(sp.Symbol("x") + 5)


def test_square_root_number_parsing():
    result = parse_math_expression("sqrt(25)")

    assert result == 5


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os')",
        "sqrt()",
        "sqrt(1, 2)",
        "unknown(x)",
        "sqrt(sqrt(x))",
    ],
)
def test_unsupported_function_calls_are_rejected(expression):
    with pytest.raises(ValueError):
        parse_math_expression(expression)


def test_simple_square_root_equation():
    result = solve_math("sqrt(x+5)=4")

    assert result["success"] is True
    assert result["answer"] == ["11"]
    assert result["verified"] is True


def test_square_root_equation_rejects_extraneous_roots():
    result = solve_math("sqrt(x+1)=x-1")

    assert result["success"] is True
    assert result["answer"] == ["3"]
    assert result["verified"] is True


def test_square_root_equation_with_no_real_solution():
    result = solve_math("sqrt(x+1)=-2")

    assert result["success"] is True
    assert result["answer"] == []
    assert result["verified"] is True


def test_square_root_equation_with_zero_solution():
    result = solve_math("sqrt(x+1)=0")

    assert result["success"] is True
    assert result["answer"] == ["-1"]
    assert result["verified"] is True


def test_equation_with_two_square_roots():
    result = solve_math("sqrt(x+1)=sqrt(2*x-1)")

    assert result["success"] is True
    assert result["answer"] == ["2"]
    assert result["verified"] is True


def test_reciprocal_square_root_equation():
    result = solve_math("1/sqrt(x+1)=1")

    assert result["success"] is True
    assert result["answer"] == ["0"]
    assert result["verified"] is True


def test_square_root_equation_rejects_denominator_zero():
    result = solve_math("sqrt(x+1)/(x+1)=0")

    assert result["success"] is True
    assert result["answer"] == []
    assert result["verified"] is True


def test_linear_equation():
    result = solve_math("3x+9=0")

    assert result["success"] is True
    assert result["answer"] == ["-3"]
    assert result["verified"] is True
    assert len(result["steps"]) == len(result["step_formulas"])


def test_factorized_quadratic():
    result = solve_math("x^2+5x+6=0")

    assert result["answer"] == ["-3", "-2"]
    assert result["verified"] is True
    assert len(result["steps"]) == 5
    assert len(result["step_formulas"]) == 5


def test_quadratic_with_two_roots():
    result = solve_math("x^2-9=0")

    assert result["answer"] == ["-3", "3"]
    assert result["verified"] is True
    assert len(result["steps"]) == len(result["step_formulas"])


def test_complex_roots():
    result = solve_math("x^2+4=0")

    assert result["answer"] == ["-2*I", "2*I"]
    assert result["verified"] is True
    assert len(result["steps"]) == 6
    assert len(result["step_formulas"]) == 6


def test_expression_simplification():
    result = solve_math("2x+3x")

    assert result["success"] is True
    assert result["answer"] == "5*x"
    assert result["verified"] is True


def test_invalid_input():
    with pytest.raises(ValueError):
        solve_math("hello")


def test_non_string_problem_raises_type_error():
    with pytest.raises(TypeError, match="Problem must be text."):
        solve_math(123)


def test_empty_input():
    with pytest.raises(ValueError):
        solve_math("")


def test_problem_too_long():
    with pytest.raises(ValueError):
        solve_math("1" * 201)


@pytest.mark.parametrize(
    "problem",
    [
        "1/0",
        "x/0",
        "x/(x-x)",
    ],
)
def test_division_by_zero(problem):
    with pytest.raises(
        ValueError,
        match="Division by zero is not allowed.",
    ):
        solve_math(problem)


def test_cubic_equation_with_complex_roots_has_detailed_steps():
    result = solve_math("x^3+1=0")

    assert result["success"] is True
    assert len(result["answer"]) == 3
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])
    assert "successfully" in result["message"].lower()


def test_identity_equation():
    result = solve_math("x-x=0")

    assert result["success"] is True
    assert result["answer"] == ["All values of x"]
    assert result["verified"] is True
    assert "infinitely many" in result["message"].lower()
    assert len(result["steps"]) == len(result["step_formulas"])


def test_square_root_identity_respects_closed_domain():
    result = solve_math("sqrt(x)=sqrt(x)")

    assert result["success"] is True
    assert result["answer"] == ["All real values of x in [0, ∞)"]
    assert result["verified"] is True
    assert len(result["steps"]) == len(result["step_formulas"])


def test_square_root_identity_excludes_zero_denominator():
    result = solve_math("sqrt(x)/sqrt(x)=1")

    assert result["success"] is True
    assert result["answer"] == ["All real values of x in (0, ∞)"]
    assert result["verified"] is True
    assert len(result["steps"]) == len(result["step_formulas"])


def test_shifted_square_root_identity_respects_domain():
    result = solve_math("sqrt(x+1)/sqrt(x+1)=1")

    assert result["success"] is True
    assert result["answer"] == ["All real values of x in (-1, ∞)"]
    assert result["verified"] is True
    assert len(result["steps"]) == len(result["step_formulas"])


def test_square_root_identity_with_empty_real_domain():
    result = solve_math("sqrt(-1)=sqrt(-1)")

    assert result["success"] is True
    assert result["answer"] == [
        "No real values of x satisfy the original domain restrictions"
    ]
    assert "no real values" in result["message"].lower()
    assert "infinitely many" not in result["message"].lower()
    assert result["verified"] is True
    assert len(result["steps"]) == len(result["step_formulas"])


def test_inconsistent_equation():
    result = solve_math("x-x=5")

    assert result["success"] is True
    assert result["answer"] == []
    assert result["verified"] is True
    assert "no solutions" in result["message"].lower()
    assert len(result["steps"]) == len(result["step_formulas"])


def test_repeated_quadratic_root():
    result = solve_math("x^2=0")

    assert result["answer"] == ["0"]
    assert result["verified"] is True
    assert len(result["steps"]) == len(result["step_formulas"])


def test_cubic_equation_with_three_rational_roots():
    result = solve_math("x^3-6x^2+11x-6=0")

    assert result["success"] is True
    assert result["answer"] == ["1", "2", "3"]
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])
    assert "successfully" in result["message"].lower()


def test_cubic_equation_with_repeated_root():
    result = solve_math("x^3-3x^2+3x-1=0")

    assert result["success"] is True
    assert result["answer"] == ["1"]
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])


def test_cubic_triple_root_multiplicity():
    result = solve_math("x^3-3x^2+3x-1=0")

    assert result["answer"] == ["1"]
    assert result["verified"] is True
    assert any("multiplicity 3" in step.lower() for step in result["steps"])
    assert len(result["steps"]) == len(result["step_formulas"])


def test_cubic_double_root_multiplicity():
    result = solve_math("x^3-5x^2+8x-4=0")

    assert result["answer"] == ["1", "2"]
    assert result["verified"] is True
    assert any("multiplicity 2" in step.lower() for step in result["steps"])
    assert len(result["steps"]) == len(result["step_formulas"])


def test_pure_cubic_equation_with_irrational_roots():
    result = solve_math("x^3-2=0")

    assert result["success"] is True
    assert len(result["answer"]) == 3
    assert result["verified"] is True
    assert len(result["steps"]) == 5
    assert len(result["step_formulas"]) == 5
    assert "successfully" in result["message"].lower()
    assert r"\sqrt[3]{2}" in result["step_formulas"][2]


def test_cubic_equation_with_three_distinct_irrational_real_roots():
    result = solve_math("x^3-3x+1=0")

    assert result["success"] is True
    assert len(result["answer"]) == 3
    assert result["verified"] is True
    assert len(result["steps"]) == 9
    assert len(result["step_formulas"]) == 9
    assert "successfully" in result["message"].lower()

    assert any("cos" in formula for formula in result["step_formulas"])


def test_trigonometric_explanation_states_roots_are_sorted():
    result = solve_math("x^3-3x+1=0")
    assert result["success"] is True
    assert result["verified"] is True
    assert "ascending numerical order" in result["steps"][8].lower()
    assert "ascending numerical order" in result["step_formulas"][8].lower()
    assert len(result["steps"]) == len(result["step_formulas"])


def test_trigonometric_formula_formats_negative_shift_correctly():
    result = solve_math("x^3-6*x^2+9*x-1=0")

    assert result["success"] is True
    assert result["verified"] is True
    assert "x = t + 2" in result["steps"][1]
    assert r"x = t + 2" in result["step_formulas"][1]
    assert len(result["steps"]) == len(result["step_formulas"])


@pytest.mark.parametrize(
    ("shift", "expected"),
    [
        (0, "x = t"),
        (sp.Rational(-5, 6), "x = t + 5/6"),
        (sp.Rational(2, 3), "x = t - 2/3"),
    ],
)
def test_cardano_substitution_formats_shift_correctly(shift, expected):
    assert format_substitution(shift) == expected


def test_cardano_explanation_formats_negative_shift_correctly():
    result = solve_math("2*x^3-5*x^2+7*x-11=0")

    assert result["success"] is True
    assert result["verified"] is True
    assert "x = t + 5/6" in result["steps"][1]
    assert r"x = t + \frac{5}{6}" in result["step_formulas"][1]
    assert len(result["steps"]) == len(result["step_formulas"])
    assert "u + v + 5/6" in result["steps"][6]
    assert r"u + v + \frac{5}{6}" in result["step_formulas"][6]
    assert r"\frac{5}{6}" in result["step_formulas"][7]

def test_cardano_formula_explains_non_real_conjugate_roots():
    result = solve_math("x^3+x+1=0")

    assert "non-real complex conjugate roots" in result["steps"][4]
    assert "non-real complex conjugate roots" in result["step_formulas"][4]
    assert r"\operatorname{cbrt}" in result["step_formulas"][5]

def test_cubic_equation_with_one_real_and_two_complex_roots():
    result = solve_math("x^3+x+1=0")

    assert result["success"] is True
    assert len(result["answer"]) == 3
    assert result["verified"] is True
    assert len(result["steps"]) == 9
    assert len(result["step_formulas"]) == 9
    assert len(result["steps"]) == len(result["step_formulas"])
    assert "successfully" in result["message"].lower()
    assert len(result["answer_approximations"]) == 3
    assert result["answer_approximations"][0].startswith("-0.682")
    assert "I" in result["answer_approximations"][1]
    assert "I" in result["answer_approximations"][2]
    assert any("Cardano" in step for step in result["steps"])

    assert len(result["answer_formulas"]) == 3

    x = sp.Symbol("x")
    polynomial = x**3 + x + 1

    for root_text in result["answer"]:
        root = sp.sympify(root_text)
        residual = sp.N(polynomial.subs(x, root), 30)

        assert abs(complex(residual)) < 1e-25


def test_rational_equation_with_linear_denominator():
    result = solve_math("1/(x-1)=2")

    assert result["answer"] == ["3/2"]
    assert result["verified"] is True


def test_rational_equation_rejects_invalid_root():
    result = solve_math("1/(x-1)=1/(x-1)+(x-1)")

    assert result["answer"] == []
    assert result["verified"] is False


def test_rational_equation_with_two_denominators():
    result = solve_math("1/x + 1/(x-1)=1")

    assert len(result["answer"]) == 2
    assert result["verified"] is True


def test_rational_identity_excludes_zero_denominator():
    result = solve_math("(x-1)/(x-1)=1")

    assert result["answer"] == ["All real values of x in (-∞, 1) ∪ (1, ∞)"]
    assert result["verified"] is True
    assert len(result["steps"]) == len(result["step_formulas"])


def test_factorable_quartic_equation_has_detailed_steps():
    result = solve_math("x^4 - 5*x^2 + 4 = 0")

    assert result["answer"] == ["-2", "-1", "1", "2"]
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])
    assert any("Factorize the polynomial" in step for step in result["steps"])


def test_rational_equation_with_cancelled_factor_has_detailed_steps():
    result = solve_math("(x^2-1)/(x-1)=0")

    assert result["success"] is True
    assert result["answer"] == ["-1"]
    assert result["verified"] is True

    assert any("x cannot equal 1" in step for step in result["steps"])

    assert any("Reject x = 1" in step for step in result["steps"])

    assert len(result["steps"]) == len(result["step_formulas"])


def test_rational_equation_linear_solution_has_detailed_steps():
    result = solve_math("1/(x-1)=2")

    assert result["answer"] == ["3/2"]
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])

    assert any("Accept x = 3/2" in step for step in result["steps"])


def test_rational_equation_rejects_only_candidate_due_to_denominator():
    result = solve_math("1/(x-1)=1/(x-1)+(x-1)")

    assert result["answer"] == []
    assert result["verified"] is False

    assert any("Reject x = 1" in step for step in result["steps"])

    assert any("No candidates satisfy" in step for step in result["steps"])

    assert len(result["steps"]) == len(result["step_formulas"])


def test_factorable_quartic_equation_with_repeated_roots():
    result = solve_math("x^4 - 2*x^3 + x^2 = 0")

    assert result["answer"] == ["0", "1"]
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])
    assert any("multiplicity 2" in step for step in result["steps"])


def test_biquadratic_quartic_equation_has_detailed_steps():
    result = solve_math("x^4 - 2 = 0")

    assert len(result["answer"]) == 4
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])
    assert any("substitute y = x^2" in step.lower() for step in result["steps"])


def test_biquadratic_quartic_equation_with_complex_roots():
    result = solve_math("x^4 + 1 = 0")

    assert len(result["answer"]) == 4
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])
    assert any("substitute y = x^2" in step.lower() for step in result["steps"])
    assert all("I" in answer for answer in result["answer"])


def test_simple_square_root_equation_has_detailed_steps():
    result = solve_math("sqrt(x+5)=4")

    assert result["success"] is True
    assert result["answer"] == ["11"]
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])
    assert any("Square both sides" in step for step in result["steps"])
    assert result["steps"][-1] == "Final solution: x = 11."


def test_square_root_equation_rejects_extraneous_root_in_steps():
    result = solve_math("sqrt(x+1)=x-1")

    assert result["answer"] == ["3"]
    assert result["verified"] is True
    assert len(result["steps"]) == len(result["step_formulas"])
    assert any("Reject x = 0" in step for step in result["steps"])
    assert result["steps"][-1] == "Final solution: x = 3."


def test_square_root_equation_with_no_solution_has_correct_steps():
    result = solve_math("sqrt(x+1)=-2")

    assert result["steps"] == [
        "A square root is always non-negative.",
        "The right-hand side is a negative constant.",
        "Therefore, no real solutions exist.",
    ]
    assert not any("Square both sides" in step for step in result["steps"])
    assert result["answer"] == []
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])
    assert "no real solutions exist" in result["steps"][-1].lower()
    assert result["step_formulas"][-1] == r"\text{No real solutions}"


def test_equal_square_roots_have_detailed_steps():
    result = solve_math("sqrt(x+4)=sqrt(2*x+1)")

    assert result["success"] is True
    assert result["answer"] == ["3"]
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])
    assert any("domain conditions" in step.lower() for step in result["steps"])
    assert result["steps"][-1] == "Final solution: x = 3."


@pytest.mark.parametrize(
    ("problem", "expected_answer"),
    [
        ("sqrt(x+1)+sqrt(x-2)=3", ["3"]),
        ("sqrt(x+1)+sqrt(x)=1", ["0"]),
    ],
)
def test_sum_of_two_square_roots_has_detailed_steps(
    problem,
    expected_answer,
):
    result = solve_math(problem)

    assert result["success"] is True
    assert result["answer"] == expected_answer
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])
    assert any("Square both sides" in step for step in result["steps"])
    assert result["steps"][-1].startswith("Final solution:")


def test_two_square_root_formulas_show_multiplication_signs():
    result = solve_math("sqrt(x+1)+sqrt(x-2)=3")

    assert result["verified"] is True

    formulas = result["step_formulas"]

    assert any(r"2\cdot 3\cdot" in formula for formula in formulas)
    assert any(r"4\cdot 9\cdot" in formula for formula in formulas)
    assert len(result["steps"]) == len(formulas)


def test_zero_rhs_multiple_radicals_with_boundary_solution():
    result = solve_math("sqrt(x)+sqrt(x)=0")

    assert result["success"] is True
    assert result["answer"] == ["0"]
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])
    assert result["steps"][0].startswith("Both square-root terms")
    assert any(r"2 \sqrt{x}=0" in formula for formula in result["step_formulas"])
    assert result["steps"][-1] == "Final solution: x = 0."


def test_zero_rhs_multiple_radicals_without_common_zero():
    result = solve_math("sqrt(x)+sqrt(x+1)=0")

    assert result["success"] is True
    assert result["answer"] == []
    assert result["verified"] is True
    assert len(result["steps"]) > 0
    assert len(result["steps"]) == len(result["step_formulas"])
    assert any("Set both radicands equal to zero" in step for step in result["steps"])
    assert any(
        r"x=0" in formula and r"x + 1=0" in formula
        for formula in result["step_formulas"]
    )
    assert any("Reject x = 0" in step for step in result["steps"])
    assert "no real solutions exist" in result["steps"][-1].lower()


def test_multiple_radicals_reject_extraneous_candidate_and_format_radicand():
    result = solve_math("sqrt(x+1)+sqrt(2*x+1)=2")

    assert result["success"] is True
    assert result["answer"] == ["0"]
    assert result["verified"] is True

    assert any(
        "candidate solutions are: 0, 24" in step.lower() for step in result["steps"]
    )
    assert any("Reject x = 24" in step for step in result["steps"])
    assert result["steps"][-1] == "Final solution: x = 0."

    assert len(result["steps"]) == len(result["step_formulas"])

    assert any(
        r"4\cdot 4\cdot \left(2 x + 1\right)" in formula
        for formula in result["step_formulas"]
    )


def test_factorable_cubic_answer_matches_factorization_steps():
    result = solve_math("x^3-x^2+x-1=0")

    expected_roots = {
        "1",
        "I",
        "-I",
    }

    expected_formulas = {
        sp.latex(sp.Integer(1)),
        sp.latex(sp.I),
        sp.latex(-sp.I),
    }

    assert result["success"] is True
    assert set(result["answer"]) == expected_roots
    assert set(result["answer_formulas"]) == expected_formulas
    assert result["verified"] is True

    assert any("x = 1" in step for step in result["steps"])

    assert any("x = I or x = -I" in step for step in result["steps"])

    assert any(
        "x = i" in formula and "x = - i" in formula
        for formula in result["step_formulas"]
    )

    assert len(result["steps"]) == len(result["step_formulas"])
