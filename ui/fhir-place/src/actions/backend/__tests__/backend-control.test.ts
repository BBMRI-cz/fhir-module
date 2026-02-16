import {
  syncAction,
  miabisSyncAction,
  deleteAllAction,
  miabisDeleteAction,
} from "../backend-control";

// Mock fetch globally
global.fetch = jest.fn() as jest.MockedFunction<typeof fetch>;

describe("Backend Control Actions", () => {
  let consoleSpy: jest.SpyInstance;
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset environment variable
    process.env.BACKEND_API_URL = "http://test-backend:5000";
    consoleSpy = jest.spyOn(console, "error").mockImplementation();
  });

  afterEach(() => {
    delete process.env.BACKEND_API_URL;
    consoleSpy.mockRestore();
  });

  describe("successful API calls", () => {
    beforeEach(() => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          message: "Operation successful",
          data: { count: 10 },
        }),
      } as Response);
    });

    it("should call sync endpoint successfully", async () => {
      const result = await syncAction();

      expect(mockFetch).toHaveBeenCalledWith("http://test-backend:5000/sync", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      expect(result).toEqual({
        success: true,
        message: "Operation successful",
        data: { message: "Operation successful", data: { count: 10 } },
      });
    });

    it("should call miabis-sync endpoint successfully", async () => {
      const result = await miabisSyncAction();

      expect(mockFetch).toHaveBeenCalledWith(
        "http://test-backend:5000/miabis-sync",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      expect(result.success).toBe(true);
      expect(result.message).toBe("Operation successful");
    });

    it("should call delete endpoint successfully", async () => {
      const result = await deleteAllAction();

      expect(mockFetch).toHaveBeenCalledWith(
        "http://test-backend:5000/delete",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      expect(result.success).toBe(true);
    });

    it("should call miabis-delete endpoint successfully", async () => {
      const result = await miabisDeleteAction();

      expect(mockFetch).toHaveBeenCalledWith(
        "http://test-backend:5000/miabis-delete",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      expect(result.success).toBe(true);
    });
  });

  describe("API error responses", () => {
    it("should handle 404 errors", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
      } as Response);

      const result = await syncAction();

      expect(result).toEqual({
        success: false,
        message: "Backend API request failed: 404 Not Found",
      });
    });

    it("should handle 500 errors", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
      } as Response);

      const result = await deleteAllAction();

      expect(result).toEqual({
        success: false,
        message: "Backend API request failed: 500 Internal Server Error",
      });
    });

    it("should handle 401 unauthorized errors", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
      } as Response);

      const result = await miabisSyncAction();

      expect(result).toEqual({
        success: false,
        message: "Backend API request failed: 401 Unauthorized",
      });
    });
  });

  describe("network errors", () => {
    it("should handle fetch network errors", async () => {
      mockFetch.mockRejectedValue(new Error("Network error"));

      const result = await syncAction();

      expect(result).toEqual({
        success: false,
        message: "Network error",
      });
    });

    it("should handle fetch timeout errors", async () => {
      mockFetch.mockRejectedValue(new Error("Request timeout"));

      const result = await miabisSyncAction();

      expect(result).toEqual({
        success: false,
        message: "Request timeout",
      });
    });

    it("should handle unknown errors", async () => {
      mockFetch.mockRejectedValue("Unknown error");

      const result = await deleteAllAction();

      expect(result).toEqual({
        success: false,
        message: "An unexpected error occurred while calling the backend API",
      });
    });
  });

  describe("environment configuration", () => {
    it("should use default backend URL when environment variable is not set", async () => {
      delete process.env.BACKEND_API_URL;

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ message: "Success" }),
      } as Response);

      await syncAction();

      expect(mockFetch).toHaveBeenCalledWith("http://localhost:5000/sync", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
    });

    it("should use custom backend URL from environment variable", async () => {
      process.env.BACKEND_API_URL = "https://custom-backend.com:8080";

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ message: "Success" }),
      } as Response);

      await miabisSyncAction();

      expect(mockFetch).toHaveBeenCalledWith(
        "https://custom-backend.com:8080/miabis-sync",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
    });
  });

  describe("response data handling", () => {
    it("should handle response with custom message", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          message: "Custom success message",
          result: "done",
        }),
      } as Response);

      const result = await syncAction();

      expect(result.message).toBe("Custom success message");
      expect(result.data).toEqual({
        message: "Custom success message",
        result: "done",
      });
    });

    it("should use default message when response has no message", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ result: "completed" }),
      } as Response);

      const result = await deleteAllAction();

      expect(result.message).toBe("Operation completed successfully");
      expect(result.data).toEqual({ result: "completed" });
    });

    it("should handle empty response body", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
      } as Response);

      const result = await miabisDeleteAction();

      expect(result.success).toBe(true);
      expect(result.message).toBe("Operation completed successfully");
      expect(result.data).toEqual({});
    });

    it("should handle JSON parsing errors", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => {
          throw new Error("Invalid JSON");
        },
      } as unknown as Response);

      const result = await syncAction();

      expect(result.success).toBe(false);
      expect(result.message).toBe("Invalid JSON");
    });
  });

  describe("request headers", () => {
    it("should send correct content-type header", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ message: "Success" }),
      } as Response);

      await syncAction();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: {
            "Content-Type": "application/json",
          },
        })
      );
    });

    it("should use POST method for all actions", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ message: "Success" }),
      } as Response);

      await Promise.all([
        syncAction(),
        miabisSyncAction(),
        deleteAllAction(),
        miabisDeleteAction(),
      ]);

      expect(mockFetch).toHaveBeenCalledTimes(4);
      mockFetch.mock.calls.forEach((call) => {
        expect(call[1]).toMatchObject({ method: "POST" });
      });
    });
  });

  describe("concurrent requests", () => {
    it("should handle multiple concurrent requests", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ message: "Success" }),
      } as Response);

      const promises = [syncAction(), miabisSyncAction(), deleteAllAction()];

      const results = await Promise.all(promises);

      expect(results).toHaveLength(3);
      results.forEach((result) => {
        expect(result.success).toBe(true);
      });
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });

    it("should handle mixed success and failure responses", async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ message: "Success" }),
        } as Response)
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          statusText: "Error",
        } as Response);

      const [successResult, errorResult] = await Promise.all([
        syncAction(),
        deleteAllAction(),
      ]);

      expect(successResult.success).toBe(true);
      expect(errorResult.success).toBe(false);
    });
  });
});
