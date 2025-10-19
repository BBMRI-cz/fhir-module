import { getFormatIcon } from "../format-utils";
import { DataFormat } from "@/types/context/setup-wizard-context/types";
import { render } from "@testing-library/react";
import "@testing-library/jest-dom";

describe("getFormatIcon", () => {
  it("should return Code icon for json format", () => {
    const { container } = render(getFormatIcon("json"));
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });

  it("should return Database icon for csv format", () => {
    const { container } = render(getFormatIcon("csv"));
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });

  it("should return FileText icon for xml format", () => {
    const { container } = render(getFormatIcon("xml"));
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });

  it("should return FileText icon for unknown format", () => {
    const { container } = render(getFormatIcon("unknown" as DataFormat));
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });

  it("should apply default className", () => {
    const { container } = render(getFormatIcon("json"));
    const svg = container.querySelector("svg");
    expect(svg).toHaveClass("w-4", "h-4");
  });

  it("should apply custom className", () => {
    const { container } = render(getFormatIcon("json", "w-8 h-8 custom-class"));
    const svg = container.querySelector("svg");
    expect(svg).toHaveClass("w-8", "h-8", "custom-class");
  });

  it("should handle all format types", () => {
    const formats: DataFormat[] = ["json", "csv", "xml"];

    for (const format of formats) {
      const { container } = render(getFormatIcon(format));
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
    }
  });
});
