
import { useState } from "react";
import "./App.css";

type SolveResponse = {
  success: boolean;
  type: string;
  problem: string;
  answer: string | string[];
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
                <strong>Question:</strong> {equation}
              </p>

              <p>
                <strong>Category selected:</strong> {category}
              </p>

              <div className="solution-answer">
                <strong>Answer:</strong>
                {Array.isArray(result.answer) ? (
                  result.answer.length > 0 ? (
                    <ul>
                      {result.answer.map((answer, index) => (
                        <li key={index}>{answer}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No solutions found.</p>
                  )
                ) : (
                  <p>{result.answer}</p>
                )}
              </div>

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
  );
}

export default App;
