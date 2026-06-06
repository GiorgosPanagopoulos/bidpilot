import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WinRatesChart } from "../components/analytics/WinRatesChart";
import { TrendsChart } from "../components/analytics/TrendsChart";
import { PricingChart } from "../components/analytics/PricingChart";
import type { PricingStats } from "../api/types";

const emptyPricing: PricingStats = {
  cpv: null,
  count: 0,
  min: null,
  max: null,
  mean: null,
  median: null,
  p25: null,
  p75: null,
  currency: "EUR",
};

describe("Analytics empty states", () => {
  it("WinRatesChart shows empty state when rates is empty", () => {
    render(<WinRatesChart rates={[]} />);
    expect(screen.getByText("No data available")).toBeDefined();
  });

  it("TrendsChart shows empty state when series is null", () => {
    render(<TrendsChart series={null} />);
    expect(screen.getByText("No data available")).toBeDefined();
  });

  it("TrendsChart shows empty state when points array is empty", () => {
    render(<TrendsChart series={{ interval: "month", points: [] }} />);
    expect(screen.getByText("No data available")).toBeDefined();
  });

  it("PricingChart shows empty state when count is 0", () => {
    render(<PricingChart stats={emptyPricing} />);
    expect(screen.getByText("No data available")).toBeDefined();
  });
});
