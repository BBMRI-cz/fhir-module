import { renderHook, act } from "@testing-library/react";
import { useDeleteDialog } from "../useDeleteDialog";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

// Mock react-hook-form
jest.mock("react-hook-form", () => ({
  useForm: jest.fn(() => ({
    handleSubmit: jest.fn((fn) => fn),
    reset: jest.fn(),
    formState: { errors: {} },
    control: {},
  })),
}));

// Mock @hookform/resolvers/zod
jest.mock("@hookform/resolvers/zod", () => ({
  zodResolver: jest.fn(),
}));

// Mock sonner toast
jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
  },
}));

// Mock the schema
jest.mock("@/app/(authorized)/backend-control/form/schema", () => ({
  ConfirmDeleteSchema: {},
}));

describe("useDeleteDialog", () => {
  const mockOnConfirmedDelete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should initialize with correct default values", () => {
    const { result } = renderHook(() => useDeleteDialog(mockOnConfirmedDelete));

    expect(result.current.isDeleteDialogOpen).toBe(false);
    expect(result.current.deleteAllConfirmMessage).toBe("DELETE ALL");
    expect(result.current.form).toBeDefined();
    expect(result.current.handleDelete).toBeDefined();
    expect(result.current.handleDialogChange).toBeDefined();
  });

  it("should open and close dialog correctly", () => {
    const { result } = renderHook(() => useDeleteDialog(mockOnConfirmedDelete));

    // Initially closed
    expect(result.current.isDeleteDialogOpen).toBe(false);

    // Open dialog
    act(() => {
      result.current.handleDialogChange(true);
    });

    expect(result.current.isDeleteDialogOpen).toBe(true);

    // Close dialog
    act(() => {
      result.current.handleDialogChange(false);
    });

    expect(result.current.isDeleteDialogOpen).toBe(false);
  });

  it("should reset form when dialog is closed", () => {
    const mockReset = jest.fn();
    (useForm as jest.Mock).mockReturnValue({
      handleSubmit: jest.fn((fn) => fn),
      reset: mockReset,
      formState: { errors: {} },
      control: {},
    });

    const { result } = renderHook(() => useDeleteDialog(mockOnConfirmedDelete));

    act(() => {
      result.current.handleDialogChange(false);
    });

    expect(mockReset).toHaveBeenCalled();
  });

  it("should call onConfirmedDelete when correct confirmation is provided", () => {
    const { result } = renderHook(() => useDeleteDialog(mockOnConfirmedDelete));

    const formData = { confirmInput: "DELETE ALL" };

    act(() => {
      result.current.handleDelete(formData);
    });

    expect(mockOnConfirmedDelete).toHaveBeenCalled();
    expect(result.current.isDeleteDialogOpen).toBe(false);
  });

  it("should show error toast when incorrect confirmation is provided", () => {
    const { result } = renderHook(() => useDeleteDialog(mockOnConfirmedDelete));

    const formData = { confirmInput: "WRONG TEXT" };

    act(() => {
      result.current.handleDelete(formData);
    });

    expect(toast.error).toHaveBeenCalledWith("Confirmation is incorrect");
    expect(mockOnConfirmedDelete).not.toHaveBeenCalled();
    expect(result.current.isDeleteDialogOpen).toBe(false); // Dialog should still close
  });

  it("should show error toast when empty confirmation is provided", () => {
    const { result } = renderHook(() => useDeleteDialog(mockOnConfirmedDelete));

    const formData = { confirmInput: "" };

    act(() => {
      result.current.handleDelete(formData);
    });

    expect(toast.error).toHaveBeenCalledWith("Confirmation is incorrect");
    expect(mockOnConfirmedDelete).not.toHaveBeenCalled();
  });

  it("should be case sensitive for confirmation text", () => {
    const { result } = renderHook(() => useDeleteDialog(mockOnConfirmedDelete));

    const formData = { confirmInput: "delete all" }; // lowercase

    act(() => {
      result.current.handleDelete(formData);
    });

    expect(toast.error).toHaveBeenCalledWith("Confirmation is incorrect");
    expect(mockOnConfirmedDelete).not.toHaveBeenCalled();
  });

  it("should handle multiple dialog state changes correctly", () => {
    const { result } = renderHook(() => useDeleteDialog(mockOnConfirmedDelete));

    // Open and close multiple times
    act(() => {
      result.current.handleDialogChange(true);
    });
    expect(result.current.isDeleteDialogOpen).toBe(true);

    act(() => {
      result.current.handleDialogChange(false);
    });
    expect(result.current.isDeleteDialogOpen).toBe(false);

    act(() => {
      result.current.handleDialogChange(true);
    });
    expect(result.current.isDeleteDialogOpen).toBe(true);
  });
});
