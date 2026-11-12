
import pytest

from backend.app.math_engine import solve_math


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
    assert any(
        "multiplicity 3" in step.lower()
        for step in result["steps"]
    )
    assert len(result["steps"]) == len(result["step_formulas"])


def test_cubic_double_root_multiplicity():
    result = solve_math("x^3-5x^2+8x-4=0")

    assert result["answer"] == ["1", "2"]
    assert result["verified"] is True
    assert any(
        "multiplicity 2" in step.lower()
        for step in result["steps"]
    )
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

    assert any(
        "cos" in formula
        for formula in result["step_formulas"]
    )


def test_cubic_equation_with_one_real_and_two_complex_roots():
    result = solve_math("x^3+x+1=0")

    assert result["success"] is True
    assert len(result["answer"]) == 3
    assert result["verified"] is True
    assert len(result["steps"]) == 9
    assert len(result["step_formulas"]) == 9
    assert len(result["steps"]) == len(result["step_formulas"])
    assert "successfully" in result["message"].lower()

    assert any(
        "Cardano" in step
        for step in result["steps"]
    )
