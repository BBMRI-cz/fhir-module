import { render, screen, fireEvent } from "@testing-library/react";
import { ActionButton } from "../ActionButton";
import { RefreshCw } from "lucide-react";
import "@testing-library/jest-dom";

describe("ActionButton", () => {
  const mockOnClick = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render with basic props", () => {
    render(<ActionButton onClick={mockOnClick}>Test Button</ActionButton>);

    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent("Test Button");
    expect(button).not.toBeDisabled();
  });

  it("should call onClick when clicked", () => {
    render(<ActionButton onClick={mockOnClick}>Click Me</ActionButton>);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  it("should be disabled when disabled prop is true", () => {
    render(
      <ActionButton onClick={mockOnClick} disabled={true}>
        Disabled Button
      </ActionButton>
    );

    const button = screen.getByRole("button");
    expect(button).toBeDisabled();

    fireEvent.click(button);
    expect(mockOnClick).not.toHaveBeenCalled();
  });

  it("should render with icon when icon prop is provided", () => {
    render(
      <ActionButton onClick={mockOnClick} icon={RefreshCw}>
        Button with Icon
      </ActionButton>
    );

    const button = screen.getByRole("button");
    const icon = button.querySelector("svg");
    expect(icon).toBeInTheDocument();
  });

  it("should apply different variants correctly", () => {
    const { rerender } = render(
      <ActionButton onClick={mockOnClick} variant="destructive">
        Destructive Button
      </ActionButton>
    );

    let button = screen.getByRole("button");
    expect(button).toHaveClass("bg-destructive"); // Assuming this class is applied

    rerender(
      <ActionButton onClick={mockOnClick} variant="outline">
        Outline Button
      </ActionButton>
    );

    button = screen.getByRole("button");
    expect(button).toHaveClass("border"); // Assuming outline variant has border
  });

  it("should apply custom className", () => {
    render(
      <ActionButton onClick={mockOnClick} className="custom-class">
        Custom Button
      </ActionButton>
    );

    const button = screen.getByRole("button");
    expect(button).toHaveClass("custom-class");
  });

  it("should have default min-width class", () => {
    render(<ActionButton onClick={mockOnClick}>Default Button</ActionButton>);

    const button = screen.getByRole("button");
    expect(button).toHaveClass("min-w-[100px]");
  });

  it("should handle multiple clicks correctly", () => {
    render(<ActionButton onClick={mockOnClick}>Multi Click</ActionButton>);

    const button = screen.getByRole("button");
    fireEvent.click(button);
    fireEvent.click(button);
    fireEvent.click(button);

    expect(mockOnClick).toHaveBeenCalledTimes(3);
  });

  it("should render children correctly", () => {
    render(
      <ActionButton onClick={mockOnClick}>
        <span>Complex Children</span>
        <span>Multiple Elements</span>
      </ActionButton>
    );

    expect(screen.getByText("Complex Children")).toBeInTheDocument();
    expect(screen.getByText("Multiple Elements")).toBeInTheDocument();
  });
});
