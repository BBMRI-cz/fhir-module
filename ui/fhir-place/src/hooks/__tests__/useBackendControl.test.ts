import { renderHook, act, waitFor } from "@testing-library/react";
import { useBackendControl } from "../useBackendControl";
import * as backendControl from "@/actions/backend/backend-control";
import { toast } from "sonner";
import { BackendActionResult } from "@/actions/backend/backend-control";

// Mock the toast function
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock the backend actions
jest.mock("@/actions/backend/backend-control", () => ({
  syncAction: jest.fn(),
  miabisSyncAction: jest.fn(),
  deleteAllAction: jest.fn(),
  miabisDeleteAction: jest.fn(),
}));

// Helper functions to reduce nesting
const createMockResult = (success: boolean, message: string) => ({
  success,
  message,
});

type UseBackendControlActions = Pick<
  ReturnType<typeof useBackendControl>,
  "handleSync" | "handleMiabisSync" | "handleDeleteAll" | "handleMiabisDelete"
>;

const executeAction = (
  hook: { current: ReturnType<typeof useBackendControl> },
  actionName: keyof UseBackendControlActions
) => {
  act(() => {
    (hook.current[actionName] as () => void)();
  });
};

const waitForActionComplete = async (hook: {
  current: ReturnType<typeof useBackendControl>;
}) => {
  await waitFor(() => {
    expect(hook.current.isLoading).toBe(null);
  });
};

const cleanupTimers = () => {
  act(() => {
    jest.runOnlyPendingTimers();
  });
};

const advanceTimers = (ms: number) => {
  act(() => {
    jest.advanceTimersByTime(ms);
  });
};

const createDelayedPromise = (result: BackendActionResult, delay: number) =>
  new Promise((resolve) => setTimeout(() => resolve(result), delay));

describe("useBackendControl", () => {
  const mockSyncAction = jest.mocked(backendControl.syncAction);
  const mockMiabisSyncAction = jest.mocked(backendControl.miabisSyncAction);
  const mockDeleteAllAction = jest.mocked(backendControl.deleteAllAction);
  const mockMiabisDeleteAction = jest.mocked(backendControl.miabisDeleteAction);

  jest.useFakeTimers();

  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it("should initialize with correct default values", () => {
    const { result } = renderHook(() => useBackendControl());

    expect(result.current.isLoading).toBe(null);
    expect(result.current.lastResults).toEqual({});
    expect(result.current.fadingBadges).toEqual({});
    expect(typeof result.current.handleSync).toBe("function");
    expect(typeof result.current.handleMiabisSync).toBe("function");
    expect(typeof result.current.handleDeleteAll).toBe("function");
    expect(typeof result.current.handleMiabisDelete).toBe("function");
  });

  describe("successful actions", () => {
    it("should handle successful sync action", async () => {
      const mockResult = createMockResult(true, "Sync completed successfully");
      mockSyncAction.mockResolvedValue(mockResult);

      const { result } = renderHook(() => useBackendControl());

      executeAction(result, "handleSync");

      expect(result.current.isLoading).toBe("Sync");
      expect(mockSyncAction).toHaveBeenCalledTimes(1);

      await waitForActionComplete(result);

      expect(result.current.lastResults["Sync"]).toEqual(mockResult);
      expect(toast.success).toHaveBeenCalledWith("Sync Success", {
        description: "Sync completed successfully",
      });

      cleanupTimers();
    });

    it("should handle successful MIABIS sync action", async () => {
      const mockResult = createMockResult(true, "MIABIS sync completed");
      mockMiabisSyncAction.mockResolvedValue(mockResult);

      const { result } = renderHook(() => useBackendControl());

      executeAction(result, "handleMiabisSync");

      expect(mockMiabisSyncAction).toHaveBeenCalledTimes(1);

      await waitFor(() => {
        expect(result.current.lastResults["MIABIS Sync"]).toEqual(mockResult);
      });

      expect(toast.success).toHaveBeenCalledWith("MIABIS Sync Success", {
        description: "MIABIS sync completed",
      });

      cleanupTimers();
    });

    it("should handle successful delete all action", async () => {
      const mockResult = createMockResult(true, "All data deleted");
      mockDeleteAllAction.mockResolvedValue(mockResult);

      const { result } = renderHook(() => useBackendControl());

      executeAction(result, "handleDeleteAll");

      expect(mockDeleteAllAction).toHaveBeenCalledTimes(1);

      await waitFor(() => {
        expect(result.current.lastResults["Delete All"]).toEqual(mockResult);
      });

      expect(toast.success).toHaveBeenCalledWith("Delete All Success", {
        description: "All data deleted",
      });

      cleanupTimers();
    });

    it("should handle successful MIABIS delete action", async () => {
      const mockResult = createMockResult(true, "MIABIS data deleted");
      mockMiabisDeleteAction.mockResolvedValue(mockResult);

      const { result } = renderHook(() => useBackendControl());

      executeAction(result, "handleMiabisDelete");

      expect(mockMiabisDeleteAction).toHaveBeenCalledTimes(1);

      await waitFor(() => {
        expect(result.current.lastResults["MIABIS Delete"]).toEqual(mockResult);
      });

      expect(toast.success).toHaveBeenCalledWith("MIABIS Delete Success", {
        description: "MIABIS data deleted",
      });

      cleanupTimers();
    });
  });

  describe("failed actions", () => {
    it("should handle failed sync action", async () => {
      const mockResult = createMockResult(false, "Sync failed");
      mockSyncAction.mockResolvedValue(mockResult);

      const { result } = renderHook(() => useBackendControl());

      executeAction(result, "handleSync");

      await waitFor(() => {
        expect(result.current.lastResults["Sync"]).toEqual(mockResult);
      });

      expect(toast.error).toHaveBeenCalledWith("Sync Failed", {
        description: "Sync failed",
      });

      cleanupTimers();
    });

    it("should handle action that throws an error", async () => {
      mockSyncAction.mockRejectedValue(new Error("Network error"));

      const { result } = renderHook(() => useBackendControl());

      executeAction(result, "handleSync");

      await waitForActionComplete(result);

      expect(toast.error).toHaveBeenCalledWith("Sync Failed", {
        description: "An unexpected error occurred",
      });

      cleanupTimers();
    });
  });

  describe("loading states", () => {
    it("should set loading state during action execution", async () => {
      const mockResult = createMockResult(true, "Success");

      mockSyncAction.mockImplementation(
        () =>
          createDelayedPromise(
            mockResult,
            100
          ) as unknown as Promise<BackendActionResult>
      );

      const { result } = renderHook(() => useBackendControl());

      executeAction(result, "handleSync");

      expect(result.current.isLoading).toBe("Sync");

      await act(async () => {
        advanceTimers(100);
      });

      await waitForActionComplete(result);

      cleanupTimers();
    });

    it("should not allow multiple concurrent actions", async () => {
      const mockResult = createMockResult(true, "Success");
      mockSyncAction.mockResolvedValue(mockResult);
      mockMiabisSyncAction.mockResolvedValue(mockResult);

      const { result } = renderHook(() => useBackendControl());

      await act(async () => {
        result.current.handleSync();
        result.current.handleMiabisSync();
      });

      expect(mockSyncAction).toHaveBeenCalledTimes(1);
      expect(mockMiabisSyncAction).toHaveBeenCalledTimes(1);

      cleanupTimers();
    });
  });

  describe("result cleanup and fading", () => {
    it("should set fading badges and clean up results after timeout", async () => {
      const mockResult = createMockResult(true, "Success");
      mockSyncAction.mockResolvedValue(mockResult);

      const { result } = renderHook(() => useBackendControl());

      executeAction(result, "handleSync");

      await waitFor(() => {
        expect(result.current.lastResults["Sync"]).toEqual(mockResult);
      });

      advanceTimers(3000);

      await waitFor(() => {
        expect(result.current.fadingBadges["Sync"]).toBe(true);
      });

      advanceTimers(1000);

      await waitFor(() => {
        expect(result.current.lastResults["Sync"]).toBeUndefined();
        expect(result.current.fadingBadges["Sync"]).toBeUndefined();
      });

      cleanupTimers();
    });
  });
});
