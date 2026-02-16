import { changeUserDetails } from "../changeUserDetails";
import { ChangeUserDetailsSchema } from "@/app/(authorized)/settings/schema/ChangeUserDetailsSchema";
import { UserDetails } from "@/lib/auth-utils";
import { db } from "@/lib/db";
import { z } from "zod";

// Mock the dependencies
jest.mock("@/app/(authorized)/settings/schema/ChangeUserDetailsSchema");
jest.mock("@/lib/schema");
jest.mock("drizzle-orm");
jest.mock("@/lib/db");

// Type for partial db mock
type PartialDbQuery = {
  users: {
    findFirst: jest.Mock;
  };
};

const mockChangeUserDetailsSchema = ChangeUserDetailsSchema as jest.Mocked<
  typeof ChangeUserDetailsSchema
>;
const mockDb = db as jest.Mocked<typeof db>;

describe("changeUserDetails", () => {
  const mockUserDetails: UserDetails = {
    id: "user-123",
    username: "testuser",
    firstName: "John",
    lastName: "Doe",
    email: "john.doe@example.com",
    isActive: true,
    createdAt: "2024-01-01T00:00:00.000Z",
    updatedAt: "2024-01-01T00:00:00.000Z",
  };

  const mockUser = {
    id: "user-123",
    username: "testuser",
    passwordHash: "hashed-password", // NOSONAR
    firstName: "John",
    lastName: "Doe",
    email: "john.doe@example.com",
    isActive: true,
    createdAt: "2024-01-01T00:00:00.000Z",
    updatedAt: "2024-01-01T00:00:00.000Z",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockChangeUserDetailsSchema.parse = jest
      .fn()
      .mockImplementation((data) => data);

    // Mock console.error to suppress error logs in tests
    jest.spyOn(console, "error").mockImplementation(() => {});

    // Mock Date.prototype.toISOString to return a consistent value
    jest
      .spyOn(Date.prototype, "toISOString")
      .mockReturnValue("2024-01-02T00:00:00.000Z");
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe("successful user details change", () => {
    it("should return true when all details are updated successfully", async () => {
      const formData = {
        firstName: "Jane",
        lastName: "Smith",
        email: "jane.smith@example.com",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };
      (mockDb.update as jest.Mock).mockReturnValueOnce({
        set: jest.fn().mockReturnValueOnce({
          where: jest.fn().mockResolvedValueOnce(undefined),
        }),
      });

      const result = await changeUserDetails(formData, mockUserDetails);

      expect(result).toBe(true);
      expect(mockChangeUserDetailsSchema.parse).toHaveBeenCalledWith(formData);
    });

    it("should update only non-empty fields", async () => {
      const formData = {
        firstName: "Jane",
        lastName: "",
        email: "jane.smith@example.com",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };

      const mockSet = jest.fn().mockReturnValueOnce({
        where: jest.fn().mockResolvedValueOnce(undefined),
      });
      (mockDb.update as jest.Mock).mockReturnValueOnce({
        set: mockSet,
      });

      await changeUserDetails(formData, mockUserDetails);

      expect(mockSet).toHaveBeenCalledWith({
        updatedAt: "2024-01-02T00:00:00.000Z",
        firstName: "Jane",
        email: "jane.smith@example.com",
      });
    });

    it("should trim whitespace from field values", async () => {
      const formData = {
        firstName: "  Jane  ",
        lastName: "  Smith  ",
        email: "  jane.smith@example.com  ",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };

      const mockSet = jest.fn().mockReturnValueOnce({
        where: jest.fn().mockResolvedValueOnce(undefined),
      });
      (mockDb.update as jest.Mock).mockReturnValueOnce({
        set: mockSet,
      });

      await changeUserDetails(formData, mockUserDetails);

      expect(mockSet).toHaveBeenCalledWith({
        updatedAt: "2024-01-02T00:00:00.000Z",
        firstName: "Jane",
        lastName: "Smith",
        email: "jane.smith@example.com",
      });
    });

    it("should return true when no changes are made (only updatedAt)", async () => {
      const formData = {
        firstName: "",
        lastName: "",
        email: "",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };

      const result = await changeUserDetails(formData, mockUserDetails);

      expect(result).toBe(true);
      expect(mockDb.update).not.toHaveBeenCalled();
    });
  });

  describe("validation errors", () => {
    it("should return false when form validation fails", async () => {
      const formData = {
        firstName: "Jane",
        lastName: "Smith",
        email: "invalid-email",
      };

      const zodError = new z.ZodError([
        {
          code: "invalid_string",
          validation: "email",
          path: ["email"],
          message: "Invalid email format",
        },
      ]);
      mockChangeUserDetailsSchema.parse.mockImplementation(() => {
        throw zodError;
      });

      const result = await changeUserDetails(formData, mockUserDetails);

      expect(result).toBe(false);
      expect(mockDb.query.users?.findFirst).not.toHaveBeenCalled();
    });
  });

  describe("user lookup errors", () => {
    it("should return false when user is not found", async () => {
      const formData = {
        firstName: "Jane",
        lastName: "Smith",
        email: "jane.smith@example.com",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(null),
        },
      };

      const result = await changeUserDetails(formData, mockUserDetails);

      expect(result).toBe(false);
      expect(mockDb.update).not.toHaveBeenCalled();
    });

    it("should return false when user lookup throws error", async () => {
      const formData = {
        firstName: "Jane",
        lastName: "Smith",
        email: "jane.smith@example.com",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest
            .fn()
            .mockRejectedValueOnce(new Error("Database error")),
        },
      };

      const result = await changeUserDetails(formData, mockUserDetails);

      expect(result).toBe(false);
    });
  });

  describe("database update errors", () => {
    it("should return false when database update fails", async () => {
      const formData = {
        firstName: "Jane",
        lastName: "Smith",
        email: "jane.smith@example.com",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };
      (mockDb.update as jest.Mock).mockImplementationOnce(() => {
        throw new Error("Update failed");
      });

      const result = await changeUserDetails(formData, mockUserDetails);

      expect(result).toBe(false);
    });
  });

  describe("edge cases", () => {
    it("should handle partial updates (only firstName)", async () => {
      const formData = {
        firstName: "Jane",
        lastName: "",
        email: "",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };

      const mockSet = jest.fn().mockReturnValueOnce({
        where: jest.fn().mockResolvedValueOnce(undefined),
      });
      (mockDb.update as jest.Mock).mockReturnValueOnce({
        set: mockSet,
      });

      const result = await changeUserDetails(formData, mockUserDetails);

      expect(result).toBe(true);
      expect(mockSet).toHaveBeenCalledWith({
        updatedAt: "2024-01-02T00:00:00.000Z",
        firstName: "Jane",
      });
    });

    it("should handle partial updates (only lastName)", async () => {
      const formData = {
        firstName: "",
        lastName: "Smith",
        email: "",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };

      const mockSet = jest.fn().mockReturnValueOnce({
        where: jest.fn().mockResolvedValueOnce(undefined),
      });
      (mockDb.update as jest.Mock).mockReturnValueOnce({
        set: mockSet,
      });

      const result = await changeUserDetails(formData, mockUserDetails);

      expect(result).toBe(true);
      expect(mockSet).toHaveBeenCalledWith({
        updatedAt: "2024-01-02T00:00:00.000Z",
        lastName: "Smith",
      });
    });

    it("should handle partial updates (only email)", async () => {
      const formData = {
        firstName: "",
        lastName: "",
        email: "new.email@example.com",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };

      const mockSet = jest.fn().mockReturnValueOnce({
        where: jest.fn().mockResolvedValueOnce(undefined),
      });
      (mockDb.update as jest.Mock).mockReturnValueOnce({
        set: mockSet,
      });

      const result = await changeUserDetails(formData, mockUserDetails);

      expect(result).toBe(true);
      expect(mockSet).toHaveBeenCalledWith({
        updatedAt: "2024-01-02T00:00:00.000Z",
        email: "new.email@example.com",
      });
    });

    it("should handle undefined values in form data", async () => {
      const formData = {
        firstName: undefined as string | undefined,
        lastName: undefined as string | undefined,
        email: undefined as string | undefined,
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };

      const result = await changeUserDetails(formData, mockUserDetails);

      expect(result).toBe(true);
      expect(mockDb.update).not.toHaveBeenCalled();
    });

    it("should handle null values in form data", async () => {
      const formData = {
        firstName: null as unknown as string,
        lastName: null as unknown as string,
        email: null as unknown as string,
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };

      const result = await changeUserDetails(formData, mockUserDetails);

      expect(result).toBe(true);
      expect(mockDb.update).not.toHaveBeenCalled();
    });

    it("should handle whitespace-only values", async () => {
      const formData = {
        firstName: "   ",
        lastName: "   ",
        email: "   ",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };

      const result = await changeUserDetails(formData, mockUserDetails);

      expect(result).toBe(true);
      expect(mockDb.update).not.toHaveBeenCalled();
    });
  });

  describe("console logging", () => {
    it("should log errors to console", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();
      const testError = new Error("Test error");

      const formData = {
        firstName: "Jane",
        lastName: "Smith",
        email: "jane.smith@example.com",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockRejectedValueOnce(testError),
        },
      };

      await changeUserDetails(formData, mockUserDetails);

      expect(consoleSpy).toHaveBeenCalledWith(
        "User details change error:",
        testError
      );
      consoleSpy.mockRestore();
    });
  });
});
