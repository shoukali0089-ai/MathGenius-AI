
import { useState } from "react";
import { MathJax, MathJaxContext } from "better-react-mathjax";
import "./App.css";

const mathJaxConfig = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
  },
  options: {
    skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code"],
  },
};
type SolveResponse = {
  success: boolean;
  type: string;
  problem: string;
  answer: string | string[];
  answer_formulas?: string[];
  answer_approximations?: string[];
  steps: string[];
  step_formulas?: string[];
  verified: boolean;
  message: string;
};


function App() {
  const [equation, setEquation] = useState("");
  const [category, setCategory] = useState("Auto Detect");
  const [language, setLanguage] = useState("English");
  const [result, setResult] = useState<SolveResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedAnswer, setCopiedAnswer] = useState<number | "single" | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);

  async function handleCopyAnswer(
  text: string,
  key: number | "single"
) {
  try {
    await navigator.clipboard.writeText(text);
    setCopiedAnswer(key);
  } catch {
    setError("Unable to copy answer. Please try again.");
  }
}
async function handleCopyAllAnswers() {
  if (!result) return;

  const answers = Array.isArray(result.answer)
    ? result.answer
    : [result.answer];

  const allAnswers = answers.map((answer, index) => {
    const approximation = result.answer_approximations?.[index];

    return [
`Answer ${index + 1}: ${result.answer_formulas?.[index] ?? answer}`,
      ...(approximation
        ? [`Approximation: ${approximation.replace(/\*I/g, "i")}`]
        : []),
    ].join("\n");
  });

  try {
    await navigator.clipboard.writeText(allAnswers.join("\n\n"));
    setCopiedAll(true);
  } catch {
    setError("Unable to copy all answers. Please try again.");
  }
}
  async function handleSolve() {
    if (!equation.trim()) {
      setError("Please enter a mathematical equation first.");
      setResult(null);
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("/api/solve", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          problem: equation.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to solve this problem.");
      }

      setResult(data as SolveResponse);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <MathJaxContext config={mathJaxConfig}>
    <div className="app">
      <header className="navbar">
        <a className="brand" href="#">
          <span className="brand-icon">∑</span>
          MathGenius <span>AI</span>
        </a>

        <nav>
          <a href="#solver">Math Solver</a>
          <a href="#features">Features</a>
          <a href="#about">About</a>
        </nav>

        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          aria-label="Select language"
        >
          <option>English</option>
          <option>Urdu</option>
          <option>Arabic</option>
          <option>French</option>
          <option>Spanish</option>
          <option>Chinese</option>
        </select>
      </header>

      <main>
        <section className="hero">
          <div className="tag">✦ YOUR INTELLIGENT MATH ASSISTANT</div>

          <h1>
            Solve Any Math Problem
            <span> With Intelligence.</span>
          </h1>

          <p>
            From simple arithmetic to advanced mathematics.
            Enter your equation and discover the solution
            with clear step-by-step explanations.
          </p>

          <div className="ad-slot">
            <small>ADVERTISEMENT</small>
            <span>Advertisement space</span>
          </div>
        </section>

        <section className="solver-card" id="solver">
          <div className="solver-heading">
            <div>
              <span className="eyebrow">MATH SOLVER</span>
              <h2>What would you like to solve?</h2>
            </div>
            <span className="ai-badge">✦ AI Powered</span>
          </div>

          <label htmlFor="category">Mathematics category</label>

          <select
            id="category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option>Auto Detect</option>
            <option>Arithmetic</option>
            <option>Algebra</option>
            <option>Calculus</option>
            <option>Geometry</option>
            <option>Trigonometry</option>
            <option>Statistics</option>
            <option>Linear Algebra</option>
            <option>Differential Equations</option>
          </select>

          <label htmlFor="equation">Enter your equation</label>

          <textarea
            id="equation"
            value={equation}
            onChange={(e) => setEquation(e.target.value)}
            placeholder="Example: x^2 + 5*x + 6 = 0"
            rows={4}
          />

          <div className="input-hint">
            Use * for multiplication and ^ for powers.
            Example: x^2 + 5*x + 6 = 0
          </div>

          <button
            className="solve-button"
            onClick={handleSolve}
            disabled={loading}
          >
            {loading ? "Solving..." : "✦ Solve Mathematics"}
          </button>

          {loading && (
            <div className="solve-loading" role="status">
              Calculating your answer. Please wait...
            </div>
          )}

          {error && (
            <div className="solve-error" role="alert">
              <h3>Unable to solve</h3>
              <p>{error}</p>
            </div>
          )}


{result && (
  <div className="result-box" aria-live="polite">
    <h3>Solution</h3>

   <p>
  <strong>Question:</strong>{" "}
  <MathJax dynamic>
    {`\\(${result.problem.replace(/\*/g, "\\cdot ").replace(/\^(\d+)/g, "^{$1}")}\\)`}
  </MathJax>
</p>

    <p>
      <strong>Category selected:</strong> {category}
    </p>

   <div className="solution-answer">
  <strong>Final Answer:</strong>
  <button
  className="copy-answer-button copy-all-button"
  onClick={handleCopyAllAnswers}
  type="button"
>
  {copiedAll ? "✓ All Answers Copied!" : "Copy All Answers"}
</button>

  {Array.isArray(result.answer) ? (
    result.answer.length > 0 ? (
      <ul>
        {result.answer.map((answer, index) => (
          <li className="answer-item" key={index}>
            <div className="exact-answer">
              <span className="answer-label">Exact Answer</span>
              <MathJax dynamic>
                {`\\(${result.answer_formulas?.[index] ?? answer}\\)`}
              </MathJax>
<button
  className="copy-answer-button"
  onClick={() => handleCopyAnswer(answer, index)}
  type="button"
>
  {copiedAnswer === index ? "✓ Copied!" : "Copy Answer"}
</button>
            </div>

            {result.answer_approximations?.[index] && (
              <p className="answer-approximation">
                <strong>Approximation:</strong>{" "}
                {result.answer_approximations[index].replace(/\*I/g, "i")}
              </p>
            )}
          </li>
        ))}
      </ul>
    ) : (
      <p>No solutions found.</p>
    )
  ) : (
    <div className="exact-answer">
      <span className="answer-label">Exact Answer</span>
      <MathJax dynamic>
        {`\\(${result.answer}\\)`}
      </MathJax>
      <button
  className="copy-answer-button"
  onClick={() => handleCopyAnswer(result.answer as string, "single")}
  type="button"
>
  {copiedAnswer === "single" ? "✓ Copied!" : "Copy Answer"}
</button>
    </div>
  )}
</div>
    {result.steps.length > 0 && (
      <div className="solution-steps">
        <h3>Step-by-Step Explanation</h3>

        <ol>
  {result.steps.map((step, index) => (
    <li key={index}>
      <p>{step}</p>

      {result.step_formulas?.[index] && (
        <MathJax dynamic>
          {`\\[${result.step_formulas[index]}\\]`}
        </MathJax>
      )}
    </li>
  ))}
</ol>
      </div>
    )}

    {result.steps.length === 0 && (
      <p>
        Detailed steps are not available for this problem yet.
      </p>
    )}


    <p>{result.message}</p>

    <div className="verification-status">
      {result.verified
        ? "✓ Mathematical verification passed"
        : "Verification not confirmed"}
    </div>
  </div>
)}

        </section>

        <div className="ad-slot middle-ad">
          <small>ADVERTISEMENT</small>
          <span>Responsive advertisement space</span>
        </div>

        <section className="features" id="features">
          <div className="section-heading">
            <span className="eyebrow">POWERFUL MATH TOOLS</span>
            <h2>Everything Mathematics Needs</h2>
            <p>One platform for every level of mathematics.</p>
          </div>

          <div className="feature-grid">
            {[
              ["＋", "Algebra", "Equations, expressions and polynomials."],
              ["∫", "Calculus", "Limits, derivatives and integrals."],
              ["△", "Geometry", "Shapes, angles and measurements."],
              ["π", "Trigonometry", "Functions, identities and angles."],
              ["Σ", "Statistics", "Probability and statistical analysis."],
              ["▦", "Linear Algebra", "Matrices, vectors and determinants."]
            ].map(([icon, title, description]) => (
              <article className="feature-card" key={title}>
                <div className="feature-icon">{icon}</div>
                <h3>{title}</h3>
                <p>{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="bottom-ad">
          <div className="ad-slot">
            <small>ADVERTISEMENT</small>
            <span>Advertisement space</span>
          </div>
        </section>

        <section className="about" id="about">
          <h2>Making Mathematics Easier for Everyone</h2>
          <p>
            MathGenius AI aims to make mathematics accessible
            through intelligent tools, understandable explanations
            and multilingual learning.
          </p>
        </section>
      </main>

      <footer>
        <a className="brand" href="#">
          ∑ MathGenius <span>AI</span>
        </a>
        <p>Making Mathematics Smarter and Simpler.</p>
        <div className="footer-links">
          <a href="#about">About</a>
          <a href="#contact">Contact</a>
          <a href="#privacy">Privacy Policy</a>
          <a href="#terms">Terms</a>
        </div>
        <small>© 2026 MathGenius AI. All rights reserved.</small>
      </footer>
      </div>
</MathJaxContext>
  );
}

export default App;
