import { render, screen } from "@testing-library/react";
import { ThemeToggle } from "../ThemeToggle";
import "@testing-library/jest-dom";

// Mock the ThemeProvider hook
jest.mock("@/components/providers/ThemeProvider", () => ({
  useTheme: jest.fn(),
}));

import { useTheme } from "@/components/providers/ThemeProvider";

describe("ThemeToggle", () => {
  const mockSetTheme = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render theme selector with light theme", () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: "light",
      setTheme: mockSetTheme,
    });

    render(<ThemeToggle />);

    expect(screen.getByText("Theme")).toBeInTheDocument();
    expect(
      screen.getByText("Choose between light and dark mode")
    ).toBeInTheDocument();
  });

  it("should render theme selector with dark theme", () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: "dark",
      setTheme: mockSetTheme,
    });

    render(<ThemeToggle />);

    expect(screen.getByText("Theme")).toBeInTheDocument();
  });

  it("should render theme selector with system theme", () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: "system",
      setTheme: mockSetTheme,
    });

    render(<ThemeToggle />);

    expect(screen.getByText("Theme")).toBeInTheDocument();
  });

  it("should display correct label text", () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: "light",
      setTheme: mockSetTheme,
    });

    render(<ThemeToggle />);

    expect(screen.getByText("Theme")).toBeInTheDocument();
    expect(
      screen.getByText(/Choose between light and dark mode/)
    ).toBeInTheDocument();
  });

  it("should render with system theme as default when theme is undefined", () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: undefined,
      setTheme: mockSetTheme,
    });

    render(<ThemeToggle />);

    expect(screen.getByText("Theme")).toBeInTheDocument();
  });
});
