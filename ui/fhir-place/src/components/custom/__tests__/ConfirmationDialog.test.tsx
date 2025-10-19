import { render, screen } from "@testing-library/react";
import { ConfirmationDialog } from "../ConfirmationDialog";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import "@testing-library/jest-dom";

const ConfirmDeleteSchema = z.object({
  confirmInput: z.string(),
});

function TestWrapper() {
  const form = useForm<z.infer<typeof ConfirmDeleteSchema>>({
    resolver: zodResolver(ConfirmDeleteSchema),
    defaultValues: {
      confirmInput: "",
    },
  });

  const mockOnConfirm = jest.fn();
  const mockOnOpenChange = jest.fn();

  return (
    <ConfirmationDialog
      isOpen={true}
      onOpenChange={mockOnOpenChange}
      title="Delete Confirmation"
      description="This action cannot be undone."
      confirmationMessage="DELETE"
      confirmButtonText="Delete"
      form={form}
      onConfirm={mockOnConfirm}
    >
      <button>Open Dialog</button>
    </ConfirmationDialog>
  );
}

describe("ConfirmationDialog", () => {
  it("should render with correct title and description", () => {
    render(<TestWrapper />);

    expect(screen.getByText("Delete Confirmation")).toBeInTheDocument();
    expect(
      screen.getByText(/This action cannot be undone/)
    ).toBeInTheDocument();
  });

  it("should render trigger children", () => {
    render(<TestWrapper />);

    expect(screen.getByText("Open Dialog")).toBeInTheDocument();
  });

  it("should display confirmation message in description", () => {
    render(<TestWrapper />);

    expect(screen.getByText(/DELETE/)).toBeInTheDocument();
  });

  it("should render cancel and confirm buttons", () => {
    render(<TestWrapper />);

    expect(screen.getByText("Cancel")).toBeInTheDocument();
    expect(screen.getByText("Delete")).toBeInTheDocument();
  });

  it("should render input field with placeholder", () => {
    render(<TestWrapper />);

    const input = screen.getByPlaceholderText("DELETE");
    expect(input).toBeInTheDocument();
  });

  it("should disable confirm button when isLoading is true", () => {
    function TestWrapperWithLoading() {
      const form = useForm<z.infer<typeof ConfirmDeleteSchema>>({
        resolver: zodResolver(ConfirmDeleteSchema),
        defaultValues: { confirmInput: "" },
      });

      return (
        <ConfirmationDialog
          isOpen={true}
          onOpenChange={jest.fn()}
          title="Test"
          description="Test description"
          confirmationMessage="TEST"
          confirmButtonText="Confirm"
          form={form}
          onConfirm={jest.fn()}
          isLoading={true}
        >
          <button>Trigger</button>
        </ConfirmationDialog>
      );
    }

    render(<TestWrapperWithLoading />);

    const confirmButton = screen.getByText("Confirm");
    expect(confirmButton).toBeDisabled();
  });

  it("should have destructive variant on confirm button", () => {
    render(<TestWrapper />);

    const confirmButton = screen.getByText("Delete");
    expect(confirmButton).toHaveClass("bg-destructive");
  });
});
