import { renderHook, act } from "@testing-library/react";
import { useConfirmationDialog } from "../useConfirmationDialog";
import { toast } from "sonner";

// Mock sonner toast
jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

describe("useConfirmationDialog", () => {
  const mockOnConfirmedAction = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should initialize with dialog closed", () => {
    const { result } = renderHook(() =>
      useConfirmationDialog("DELETE", mockOnConfirmedAction)
    );

    expect(result.current.isDialogOpen).toBe(false);
  });

  it("should return confirmation message", () => {
    const { result } = renderHook(() =>
      useConfirmationDialog("DELETE", mockOnConfirmedAction)
    );

    expect(result.current.confirmationMessage).toBe("DELETE");
  });

  it("should return form object", () => {
    const { result } = renderHook(() =>
      useConfirmationDialog("DELETE", mockOnConfirmedAction)
    );

    expect(result.current.form).toBeDefined();
    expect(result.current.form.control).toBeDefined();
  });

  it("should call onConfirmedAction when confirmation matches", () => {
    const { result } = renderHook(() =>
      useConfirmationDialog("DELETE", mockOnConfirmedAction)
    );

    act(() => {
      result.current.handleConfirm({ confirmInput: "DELETE" });
    });

    expect(mockOnConfirmedAction).toHaveBeenCalledTimes(1);
  });

  it("should show error toast when confirmation does not match", () => {
    const { result } = renderHook(() =>
      useConfirmationDialog("DELETE", mockOnConfirmedAction)
    );

    act(() => {
      result.current.handleConfirm({ confirmInput: "wrong" });
    });

    expect(toast.error).toHaveBeenCalledWith("Confirmation is incorrect");
    expect(mockOnConfirmedAction).not.toHaveBeenCalled();
  });

  it("should close dialog on successful confirmation", () => {
    const { result } = renderHook(() =>
      useConfirmationDialog("DELETE", mockOnConfirmedAction)
    );

    act(() => {
      result.current.handleDialogChange(true);
    });

    expect(result.current.isDialogOpen).toBe(true);

    act(() => {
      result.current.handleConfirm({ confirmInput: "DELETE" });
    });

    expect(result.current.isDialogOpen).toBe(false);
  });

  it("should reset form when dialog is closed", () => {
    const { result } = renderHook(() =>
      useConfirmationDialog("DELETE", mockOnConfirmedAction)
    );

    act(() => {
      result.current.form.setValue("confirmInput", "test");
    });

    expect(result.current.form.getValues("confirmInput")).toBe("test");

    act(() => {
      result.current.handleDialogChange(false);
    });

    expect(result.current.form.getValues("confirmInput")).toBe("");
  });

  it("should not reset form when dialog is opened", () => {
    const { result } = renderHook(() =>
      useConfirmationDialog("DELETE", mockOnConfirmedAction)
    );

    act(() => {
      result.current.form.setValue("confirmInput", "test");
    });

    act(() => {
      result.current.handleDialogChange(true);
    });

    expect(result.current.form.getValues("confirmInput")).toBe("test");
  });
});
