import { render, screen, fireEvent } from "@testing-library/react";
import { ActionItem } from "../ActionItem";
import { RefreshCw } from "lucide-react";
import "@testing-library/jest-dom";

describe("ActionItem", () => {
  const mockOnAction = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render with title and description", () => {
    render(
      <ActionItem
        title="Sync Data"
        description="Synchronize data with backend"
        buttonText="Sync"
        onAction={mockOnAction}
        isLoading={false}
      />
    );

    expect(screen.getByText("Sync Data")).toBeInTheDocument();
    expect(
      screen.getByText("Synchronize data with backend")
    ).toBeInTheDocument();
    expect(screen.getByText("Sync")).toBeInTheDocument();
  });

  it("should call onAction when button is clicked", () => {
    render(
      <ActionItem
        title="Test Action"
        description="Test description"
        buttonText="Click Me"
        onAction={mockOnAction}
        isLoading={false}
      />
    );

    const button = screen.getByText("Click Me");
    fireEvent.click(button);

    expect(mockOnAction).toHaveBeenCalledTimes(1);
  });

  it("should display success badge", () => {
    render(
      <ActionItem
        title="Test Action"
        description="Test description"
        buttonText="Action"
        onAction={mockOnAction}
        isLoading={false}
        result={{ success: true, message: "Operation successful" }}
      />
    );

    expect(screen.getByText("Success")).toBeInTheDocument();
  });

  it("should display failed badge", () => {
    render(
      <ActionItem
        title="Test Action"
        description="Test description"
        buttonText="Action"
        onAction={mockOnAction}
        isLoading={false}
        result={{ success: false, message: "Operation failed" }}
      />
    );

    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("should apply fading class to badge when isFading is true", () => {
    render(
      <ActionItem
        title="Test Action"
        description="Test description"
        buttonText="Action"
        onAction={mockOnAction}
        isLoading={false}
        result={{ success: true, message: "Success" }}
        isFading={true}
      />
    );

    const badge = screen.getByText("Success");
    expect(badge).toHaveClass("opacity-0");
  });

  it("should not apply fading class when isFading is false", () => {
    render(
      <ActionItem
        title="Test Action"
        description="Test description"
        buttonText="Action"
        onAction={mockOnAction}
        isLoading={false}
        result={{ success: true, message: "Success" }}
        isFading={false}
      />
    );

    const badge = screen.getByText("Success");
    expect(badge).toHaveClass("opacity-100");
  });

  it("should render with icon", () => {
    const { container } = render(
      <ActionItem
        title="Test Action"
        description="Test description"
        buttonText="Action"
        onAction={mockOnAction}
        isLoading={false}
        icon={RefreshCw}
      />
    );

    const icon = container.querySelector("svg");
    expect(icon).toBeInTheDocument();
  });

  it("should render with custom variant", () => {
    render(
      <ActionItem
        title="Test Action"
        description="Test description"
        buttonText="Delete"
        onAction={mockOnAction}
        isLoading={false}
        variant="destructive"
      />
    );

    const button = screen.getByText("Delete");
    expect(button).toHaveClass("bg-destructive");
  });

  it("should disable button when disabled prop is true", () => {
    render(
      <ActionItem
        title="Test Action"
        description="Test description"
        buttonText="Action"
        onAction={mockOnAction}
        isLoading={false}
        disabled={true}
      />
    );

    const button = screen.getByText("Action");
    expect(button).toBeDisabled();
  });

  it("should render custom children instead of button", () => {
    render(
      <ActionItem
        title="Test Action"
        description="Test description"
        buttonText="Action"
        onAction={mockOnAction}
        isLoading={false}
      >
        <button>Custom Button</button>
      </ActionItem>
    );

    expect(screen.getByText("Custom Button")).toBeInTheDocument();
    expect(screen.queryByText("Action")).not.toBeInTheDocument();
  });

  it("should not render badge when result is undefined", () => {
    render(
      <ActionItem
        title="Test Action"
        description="Test description"
        buttonText="Action"
        onAction={mockOnAction}
        isLoading={false}
      />
    );

    expect(screen.queryByText("Success")).not.toBeInTheDocument();
    expect(screen.queryByText("Failed")).not.toBeInTheDocument();
  });

  it("should apply green styling to success badge", () => {
    render(
      <ActionItem
        title="Test Action"
        description="Test description"
        buttonText="Action"
        onAction={mockOnAction}
        isLoading={false}
        result={{ success: true, message: "Success" }}
      />
    );

    const badge = screen.getByText("Success");
    expect(badge).toHaveClass("text-green-400", "border-green-400");
  });

  it("should apply red styling to failed badge", () => {
    render(
      <ActionItem
        title="Test Action"
        description="Test description"
        buttonText="Action"
        onAction={mockOnAction}
        isLoading={false}
        result={{ success: false, message: "Failed" }}
      />
    );

    const badge = screen.getByText("Failed");
    expect(badge).toHaveClass("text-red-400", "border-red-400");
  });
});
