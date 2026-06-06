import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EligibilityBadge } from "../components/feed/EligibilityBadge";

describe("EligibilityBadge", () => {
  it("shows Passed when passed=true and no warnings", () => {
    render(<EligibilityBadge passed={true} failedCriteria={[]} warnings={[]} />);
    expect(screen.getByText("Passed")).toBeDefined();
  });

  it("shows Failed when passed=false", () => {
    render(<EligibilityBadge passed={false} failedCriteria={["No ISO cert"]} warnings={[]} />);
    expect(screen.getByText("Failed")).toBeDefined();
  });

  it("shows Warnings when passed=true but has warnings", () => {
    render(<EligibilityBadge passed={true} failedCriteria={[]} warnings={["Expiring soon"]} />);
    expect(screen.getByText("Warnings")).toBeDefined();
  });

  it("reveals failed criteria on hover", () => {
    render(
      <EligibilityBadge passed={false} failedCriteria={["Missing ISO 9001"]} warnings={[]} />,
    );
    const btn = screen.getByRole("button");
    fireEvent.mouseEnter(btn);
    expect(screen.getByText("Missing ISO 9001")).toBeDefined();
    fireEvent.mouseLeave(btn);
    expect(screen.queryByText("Missing ISO 9001")).toBeNull();
  });
});
