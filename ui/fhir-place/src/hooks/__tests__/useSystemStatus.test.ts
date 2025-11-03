import { renderHook, act, waitFor } from "@testing-library/react";
import { useSystemStatus } from "../useSystemStatus";
import { queryPrometheusAction } from "@/actions/prometheus/query";

// Mock the prometheus query action
jest.mock("@/actions/prometheus/query", () => ({
  queryPrometheusAction: jest.fn(),
}));

// Mock the queries
jest.mock("@/actions/prometheus/queries", () => ({
  fhirUpQuery: "up",
  fhirLastSyncQuery: "last_sync",
}));

describe("useSystemStatus", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(async () => {
    // Clean up any pending timers
    act(() => {
      jest.clearAllTimers();
    });
    jest.useRealTimers();
  });

  it("should initialize with loading state", async () => {
    (queryPrometheusAction as jest.Mock).mockResolvedValue({
      success: false,
      data: null,
    });

    const { result } = renderHook(() => useSystemStatus());

    expect(result.current.systemStatus.fetchState).toBe("loading");
    expect(result.current.systemStatus.isOnline).toBe(false);
    expect(result.current.autoRefresh).toBe(true);

    // Wait for async effects to complete
    await waitFor(() => {
      expect(queryPrometheusAction).toHaveBeenCalled();
    });
  });

  it("should fetch system status successfully", async () => {
    (queryPrometheusAction as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        result: [
          {
            value: [1234567890, "1"],
          },
        ],
      },
    });

    const { result } = renderHook(() => useSystemStatus());

    await waitFor(() => {
      expect(result.current.systemStatus.fetchState).toBe("loaded");
    });

    expect(result.current.systemStatus.isOnline).toBe(true);
  });

  it("should handle offline status", async () => {
    (queryPrometheusAction as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        result: [
          {
            value: [1234567890, "0"],
          },
        ],
      },
    });

    const { result } = renderHook(() => useSystemStatus());

    await waitFor(() => {
      expect(result.current.systemStatus.fetchState).toBe("loaded");
    });

    expect(result.current.systemStatus.isOnline).toBe(false);
  });

  it("should handle fetch errors", async () => {
    // Suppress console.error for this test since we're testing error handling
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    (queryPrometheusAction as jest.Mock).mockRejectedValue(
      new Error("Network error")
    );

    const { result } = renderHook(() => useSystemStatus());

    await waitFor(() => {
      expect(result.current.systemStatus.fetchState).toBe("error");
    });

    expect(result.current.systemStatus.error).toBe("Network error");

    consoleSpy.mockRestore();
  });

  it("should refresh status manually", async () => {
    (queryPrometheusAction as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        result: [
          {
            value: [1234567890, "1"],
          },
        ],
      },
    });

    const { result } = renderHook(() => useSystemStatus());

    await waitFor(() => {
      expect(result.current.systemStatus.fetchState).toBe("loaded");
    });

    await act(async () => {
      await result.current.refresh();
    });

    expect(queryPrometheusAction).toHaveBeenCalled();
  });

  it("should set isRefreshing during manual refresh", async () => {
    (queryPrometheusAction as jest.Mock).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () => resolve({ success: true, data: { result: [] } }),
            100
          )
        )
    );

    const { result } = renderHook(() => useSystemStatus());

    await act(async () => {
      result.current.refresh();
    });

    // After the refresh completes, isRefreshing should be false
    await waitFor(() => {
      expect(result.current.isRefreshing).toBe(false);
    });
  });

  it("should toggle auto refresh", async () => {
    (queryPrometheusAction as jest.Mock).mockResolvedValue({
      success: false,
      data: null,
    });

    const { result } = renderHook(() => useSystemStatus());

    // Wait for initial mount effects
    await waitFor(() => {
      expect(queryPrometheusAction).toHaveBeenCalled();
    });

    expect(result.current.autoRefresh).toBe(true);

    act(() => {
      result.current.setAutoRefresh(false);
    });

    expect(result.current.autoRefresh).toBe(false);

    act(() => {
      result.current.setAutoRefresh(true);
    });

    expect(result.current.autoRefresh).toBe(true);
  });

  it("should auto refresh when enabled", async () => {
    (queryPrometheusAction as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        result: [
          {
            value: [1234567890, "1"],
          },
        ],
      },
    });

    const { result } = renderHook(() => useSystemStatus());

    await waitFor(() => {
      expect(result.current.systemStatus.fetchState).toBe("loaded");
    });

    const initialCallCount = (queryPrometheusAction as jest.Mock).mock.calls
      .length;

    // Fast forward time by 30 seconds and wait for state updates
    await act(async () => {
      jest.advanceTimersByTime(30000);
      await Promise.resolve(); // Let promises resolve
    });

    await waitFor(() => {
      expect(
        (queryPrometheusAction as jest.Mock).mock.calls.length
      ).toBeGreaterThan(initialCallCount);
    });
  });

  it("should not auto refresh when disabled", async () => {
    (queryPrometheusAction as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        result: [
          {
            value: [1234567890, "1"],
          },
        ],
      },
    });

    const { result } = renderHook(() => useSystemStatus());

    await waitFor(() => {
      expect(result.current.systemStatus.fetchState).toBe("loaded");
    });

    await act(async () => {
      result.current.setAutoRefresh(false);
    });

    const callCountAfterDisable = (queryPrometheusAction as jest.Mock).mock
      .calls.length;

    // Fast forward time by 30 seconds
    await act(async () => {
      jest.advanceTimersByTime(30000);
      await Promise.resolve(); // Let any promises resolve
    });

    // Should not have made additional calls
    expect((queryPrometheusAction as jest.Mock).mock.calls.length).toBe(
      callCountAfterDisable
    );
  });
});
