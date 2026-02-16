/* eslint-disable @typescript-eslint/no-explicit-any */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useForm } from "react-hook-form";
import { CheckedFormInput } from "../CheckedFormInput";
import "@testing-library/jest-dom";

// Mock the UI components
jest.mock("@/components/ui/input", () => ({
  Input: ({ className, ...props }: any) => (
    <input className={className} {...props} data-testid="input" />
  ),
}));

jest.mock("@/components/ui/button", () => ({
  Button: ({ children, onClick, ...props }: any) => (
    <button onClick={onClick} {...props} data-testid="button">
      {children}
    </button>
  ),
}));

jest.mock("@/components/ui/label", () => ({
  Label: ({ children, ...props }: any) => (
    <label {...props} data-testid="label">
      {children}
    </label>
  ),
}));

jest.mock("@/components/ui/form", () => ({
  FormControl: ({ children }: any) => (
    <div data-testid="form-control">{children}</div>
  ),
  FormField: ({ render }: any) => render({ field: {} }),
  FormItem: ({ children }: any) => (
    <div data-testid="form-item">{children}</div>
  ),
}));

jest.mock("@/components/ui/hover-card", () => ({
  HoverCard: ({ children }: any) => (
    <div data-testid="hover-card">{children}</div>
  ),
  HoverCardContent: ({ children }: any) => (
    <div data-testid="hover-card-content">{children}</div>
  ),
  HoverCardTrigger: ({ children }: any) => (
    <div data-testid="hover-card-trigger">{children}</div>
  ),
}));

// Test wrapper component that uses react-hook-form
const TestWrapper = ({ defaultValue = "", errors = {}, ...props }: any) => {
  const { control } = useForm({
    defaultValues: { testField: defaultValue },
  });

  return (
    <CheckedFormInput
      control={control}
      name="testField"
      placeholder="Test placeholder"
      errors={errors}
      {...props}
    />
  );
};

describe("CheckedFormInput", () => {
  const user = userEvent.setup();

  it("should render with basic props", () => {
    render(<TestWrapper />);

    expect(screen.getByTestId("input")).toBeInTheDocument();
    expect(screen.getByTestId("input")).toHaveAttribute(
      "placeholder",
      "Test placeholder"
    );
  });

  it("should render with label when label prop is provided", () => {
    render(<TestWrapper label="Test Label" />);

    expect(screen.getByTestId("label")).toBeInTheDocument();
    expect(screen.getByTestId("label")).toHaveTextContent("Test Label");
  });

  it("should render as password type when isPassword is true", () => {
    render(<TestWrapper isPassword={true} />);

    const input = screen.getByTestId("input");
    expect(input).toHaveAttribute("type", "password");
  });

  it("should render as text type by default", () => {
    render(<TestWrapper />);

    const input = screen.getByTestId("input");
    expect(input).toHaveAttribute("type", "text");
  });

  it("should show password toggle button when isPassword is true", () => {
    render(<TestWrapper isPassword={true} />);

    const toggleButtons = screen.getAllByTestId("button");
    expect(toggleButtons.length).toBeGreaterThan(0);
  });

  it("should toggle password visibility when password toggle is clicked", async () => {
    render(<TestWrapper isPassword={true} />);

    const input = screen.getByTestId("input");
    const toggleButtons = screen.getAllByTestId("button");
    const passwordToggle = toggleButtons[0]; // Assuming first button is password toggle

    // Initially should be password type
    expect(input).toHaveAttribute("type", "password");

    // Click toggle
    await user.click(passwordToggle);

    // Should now be text type
    expect(input).toHaveAttribute("type", "text");

    // Click again
    await user.click(passwordToggle);

    // Should be password type again
    expect(input).toHaveAttribute("type", "password");
  });

  it("should display error when errors are provided", () => {
    const errors = {
      testField: { types: { required: "This field is required" } },
    };

    render(<TestWrapper errors={errors} />);

    expect(screen.getByTestId("hover-card")).toBeInTheDocument();
    const errorElements = screen.getAllByText("This field is required");
    expect(errorElements.length).toBeGreaterThan(0);
  });

  it("should apply error styling when there are errors", () => {
    const errors = {
      testField: { types: { required: "This field is required" } },
    };

    render(<TestWrapper errors={errors} />);

    const input = screen.getByTestId("input");
    expect(input).toHaveClass("border-red-400");
  });

  it("should not show error styling when no errors", () => {
    render(<TestWrapper />);

    const input = screen.getByTestId("input");
    expect(input).not.toHaveClass("border-red-400");
  });

  it("should handle user input correctly", async () => {
    render(<TestWrapper />);

    const input = screen.getByTestId("input");

    await user.type(input, "test input");

    expect(input).toHaveValue("test input");
  });

  it("should show both password toggle and error when isPassword and has errors", () => {
    const errors = {
      testField: { types: { required: "Password is required" } },
    };

    render(<TestWrapper isPassword={true} errors={errors} />);

    expect(screen.getByTestId("hover-card")).toBeInTheDocument();
    expect(screen.getAllByTestId("button").length).toBeGreaterThan(0);
    const errorElements = screen.getAllByText("Password is required");
    expect(errorElements.length).toBeGreaterThan(0);
  });

  it("should handle different error message types", () => {
    const stringError = {
      testField: { types: { custom: "String error message" } },
    };

    render(<TestWrapper errors={stringError} />);

    const errorElements = screen.getAllByText("String error message");
    expect(errorElements.length).toBeGreaterThan(0);
  });

  it("should not render error elements when no error", () => {
    render(<TestWrapper />);

    expect(screen.queryByTestId("hover-card")).not.toBeInTheDocument();
  });
});
