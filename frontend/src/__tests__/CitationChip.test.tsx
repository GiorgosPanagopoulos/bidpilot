import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CitationChip } from "../components/workspace/CitationChip";

describe("CitationChip", () => {
  it("renders locator text", () => {
    render(<CitationChip locator="§3.1" snippet="The procurement threshold is 50 000 EUR." />);
    expect(screen.getByText("§3.1")).toBeDefined();
  });

  it("snippet is hidden initially", () => {
    render(<CitationChip locator="§3.1" snippet="Some snippet text" />);
    expect(screen.queryByText("Some snippet text")).toBeNull();
  });

  it("toggles snippet open on click", () => {
    render(<CitationChip locator="§3.1" snippet="Some snippet text" />);
    const btn = screen.getByRole("button");
    expect(btn.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(btn);
    expect(screen.getByText("Some snippet text")).toBeDefined();
    expect(btn.getAttribute("aria-expanded")).toBe("true");
  });

  it("closes snippet on second click", () => {
    render(<CitationChip locator="§3.1" snippet="Some snippet text" />);
    const btn = screen.getByRole("button");
    fireEvent.click(btn);
    fireEvent.click(btn);
    expect(screen.queryByText("Some snippet text")).toBeNull();
    expect(btn.getAttribute("aria-expanded")).toBe("false");
  });
});
