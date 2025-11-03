import { render, screen } from "@testing-library/react";
import { OperationCard } from "../OperationCard";
import { Database } from "lucide-react";
import "@testing-library/jest-dom";

describe("OperationCard", () => {
  it("should render with title and description", () => {
    render(
      <OperationCard
        title="Database Operations"
        description="Manage your database"
        icon={Database}
      >
        <div>Content</div>
      </OperationCard>
    );

    expect(screen.getByText("Database Operations")).toBeInTheDocument();
    expect(screen.getByText("Manage your database")).toBeInTheDocument();
  });

  it("should render children content", () => {
    render(
      <OperationCard
        title="Test Card"
        description="Test description"
        icon={Database}
      >
        <button>Action Button</button>
        <p>Additional content</p>
      </OperationCard>
    );

    expect(screen.getByText("Action Button")).toBeInTheDocument();
    expect(screen.getByText("Additional content")).toBeInTheDocument();
  });

  it("should render icon", () => {
    const { container } = render(
      <OperationCard
        title="Icon Test"
        description="Testing icon rendering"
        icon={Database}
      >
        <div>Content</div>
      </OperationCard>
    );

    const icon = container.querySelector("svg");
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass("h-5", "w-5");
  });

  it("should display title with icon", () => {
    const { container } = render(
      <OperationCard
        title="Combined Test"
        description="Test title with icon"
        icon={Database}
      >
        <div>Content</div>
      </OperationCard>
    );

    const title = screen.getByText("Combined Test");
    expect(title).toBeInTheDocument();
    const icon = container.querySelector("svg");
    expect(icon).toBeInTheDocument();
  });

  it("should handle empty children", () => {
    render(
      <OperationCard
        title="Empty Card"
        description="No content"
        icon={Database}
      >
        {null}
      </OperationCard>
    );

    expect(screen.getByText("Empty Card")).toBeInTheDocument();
    expect(screen.getByText("No content")).toBeInTheDocument();
  });
});
