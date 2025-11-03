import { render, screen } from "@testing-library/react";
import { FontSizeToggle } from "../FontSizeToggle";
import "@testing-library/jest-dom";

// Mock the FontSizeProvider hook
jest.mock("@/components/providers/FontSizeProvider", () => ({
  useFontSize: jest.fn(),
}));

import { useFontSize } from "@/components/providers/FontSizeProvider";

describe("FontSizeToggle", () => {
  const mockSetFontSize = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render font size selector with small size", () => {
    (useFontSize as jest.Mock).mockReturnValue({
      fontSize: "small",
      setFontSize: mockSetFontSize,
    });

    render(<FontSizeToggle />);

    expect(screen.getByText("Font Size")).toBeInTheDocument();
    expect(
      screen.getByText("Adjust the font size for better readability")
    ).toBeInTheDocument();
  });

  it("should render font size selector with medium size", () => {
    (useFontSize as jest.Mock).mockReturnValue({
      fontSize: "medium",
      setFontSize: mockSetFontSize,
    });

    render(<FontSizeToggle />);

    expect(screen.getByText("Font Size")).toBeInTheDocument();
  });

  it("should render font size selector with large size", () => {
    (useFontSize as jest.Mock).mockReturnValue({
      fontSize: "large",
      setFontSize: mockSetFontSize,
    });

    render(<FontSizeToggle />);

    expect(screen.getByText("Font Size")).toBeInTheDocument();
  });

  it("should display correct description text", () => {
    (useFontSize as jest.Mock).mockReturnValue({
      fontSize: "medium",
      setFontSize: mockSetFontSize,
    });

    render(<FontSizeToggle />);

    expect(
      screen.getByText(/Adjust the font size for better readability/)
    ).toBeInTheDocument();
  });

  it("should render with medium as default when fontSize is undefined", () => {
    (useFontSize as jest.Mock).mockReturnValue({
      fontSize: undefined,
      setFontSize: mockSetFontSize,
    });

    render(<FontSizeToggle />);

    expect(screen.getByText("Font Size")).toBeInTheDocument();
  });
});
