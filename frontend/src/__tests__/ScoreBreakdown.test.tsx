import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ScoreBreakdown } from "../components/feed/ScoreBreakdown";

describe("ScoreBreakdown", () => {
  it("renders root container", () => {
    render(<ScoreBreakdown semanticScore={0.7} ruleScore={0.8} finalScore={0.75} />);
    expect(screen.getByTestId("score-breakdown")).toBeDefined();
  });

  it("displays final score as percentage", () => {
    render(<ScoreBreakdown semanticScore={0.5} ruleScore={0.5} finalScore={0.64} />);
    expect(screen.getByText("64")).toBeDefined();
  });

  it("renders semantic bar with correct width", () => {
    render(<ScoreBreakdown semanticScore={0.6} ruleScore={0.4} finalScore={0.5} />);
    const bar = screen.getByTestId("bar-semantic");
    expect(bar.style.width).toBe("60%");
  });

  it("renders rule bar with correct width", () => {
    render(<ScoreBreakdown semanticScore={0.6} ruleScore={0.9} finalScore={0.75} />);
    const bar = screen.getByTestId("bar-rule");
    expect(bar.style.width).toBe("90%");
  });
});
