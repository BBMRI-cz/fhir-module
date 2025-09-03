import { changePassword } from "../changePassword";
import bcrypt from "bcryptjs";
import { ChangePasswordSchema } from "@/app/(authorized)/settings/schema/ChangePasswordSchema";
import { UserDetails } from "@/lib/auth-utils";
import { users } from "@/lib/schema";
import { db } from "@/lib/db";
import { z } from "zod";

// Mock the dependencies
jest.mock("bcryptjs");
jest.mock("@/app/(authorized)/settings/schema/ChangePasswordSchema");
jest.mock("@/lib/schema");
jest.mock("drizzle-orm");
jest.mock("@/lib/db");

// Type for partial db mock
type PartialDbQuery = {
  users: {
    findFirst: jest.Mock;
  };
};

const mockBcrypt = bcrypt as jest.Mocked<typeof bcrypt>;
const mockChangePasswordSchema = ChangePasswordSchema as jest.Mocked<
  typeof ChangePasswordSchema
>;
const mockDb = db as jest.Mocked<typeof db>;

describe("changePassword", () => {
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

  const mockFormData = {
    currentPassword: "OldPass123!", // NOSONAR
    newPassword: "NewPass456!", // NOSONAR
    confirmPassword: "NewPass456!", // NOSONAR
  };

  const mockUser = {
    id: "user-123",
    username: "testuser",
    passwordHash: "old-hashed-password", // NOSONAR
    firstName: "John",
    lastName: "Doe",
    email: "john.doe@example.com",
    isActive: true,
    createdAt: "2024-01-01T00:00:00.000Z",
    updatedAt: "2024-01-01T00:00:00.000Z",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockChangePasswordSchema.parse = jest
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

  describe("successful password change", () => {
    it("should return true when password is changed successfully", async () => {
      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };
      (mockBcrypt.compare as jest.Mock).mockResolvedValueOnce(true);
      (mockBcrypt.hash as jest.Mock).mockResolvedValueOnce(
        "new-hashed-password"
      );
      (mockDb.update as jest.Mock).mockReturnValueOnce({
        set: jest.fn().mockReturnValueOnce({
          where: jest.fn().mockResolvedValueOnce(undefined),
        }),
      });

      const result = await changePassword(mockFormData, mockUserDetails);

      expect(result).toBe(true);
      expect(mockChangePasswordSchema.parse).toHaveBeenCalledWith(mockFormData);
      expect(mockBcrypt.compare).toHaveBeenCalledWith(
        "OldPass123!",
        "old-hashed-password"
      );
      expect(mockBcrypt.hash).toHaveBeenCalledWith("NewPass456!", 12);
      expect(mockDb.update).toHaveBeenCalledWith(users);
    });

    it("should update password hash and updatedAt timestamp", async () => {
      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };
      (mockBcrypt.compare as jest.Mock).mockResolvedValueOnce(true);
      (mockBcrypt.hash as jest.Mock).mockResolvedValueOnce(
        "new-hashed-password"
      );

      const mockSet = jest.fn().mockReturnValueOnce({
        where: jest.fn().mockResolvedValueOnce(undefined),
      });
      (mockDb.update as jest.Mock).mockReturnValueOnce({
        set: mockSet,
      });

      await changePassword(mockFormData, mockUserDetails);

      expect(mockSet).toHaveBeenCalledWith({
        passwordHash: "new-hashed-password", // NOSONAR
        updatedAt: "2024-01-02T00:00:00.000Z",
      });
    });
  });

  describe("validation errors", () => {
    it("should return false when form validation fails", async () => {
      const zodError = new z.ZodError([
        {
          code: "invalid_type",
          expected: "string",
          received: "undefined",
          path: ["currentPassword"],
          message: "Current password is required",
        },
      ]);
      mockChangePasswordSchema.parse.mockImplementation(() => {
        throw zodError;
      });

      const result = await changePassword(mockFormData, mockUserDetails);

      expect(result).toBe(false);
      expect(mockDb.query.users?.findFirst).not.toHaveBeenCalled();
    });
  });

  describe("user lookup errors", () => {
    it("should return false when user is not found", async () => {
      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(null),
        },
      };
      const result = await changePassword(mockFormData, mockUserDetails);

      expect(result).toBe(false);
      expect(mockBcrypt.compare).not.toHaveBeenCalled();
    });

    it("should return false when user lookup throws error", async () => {
      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest
            .fn()
            .mockRejectedValueOnce(new Error("Database error")),
        },
      };

      const result = await changePassword(mockFormData, mockUserDetails);

      expect(result).toBe(false);
    });
  });

  describe("current password verification", () => {
    it("should return false when current password is incorrect", async () => {
      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };
      (mockBcrypt.compare as jest.Mock).mockResolvedValueOnce(false);

      const result = await changePassword(mockFormData, mockUserDetails);

      expect(result).toBe(false);
      expect(mockBcrypt.hash).not.toHaveBeenCalled();
      expect(mockDb.update).not.toHaveBeenCalled();
    });

    it("should return false when password comparison throws error", async () => {
      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };
      (mockBcrypt.compare as jest.Mock).mockRejectedValueOnce(
        new Error("bcrypt error")
      );

      const result = await changePassword(mockFormData, mockUserDetails);

      expect(result).toBe(false);
    });
  });

  describe("password hashing errors", () => {
    it("should return false when password hashing fails", async () => {
      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };
      (mockBcrypt.compare as jest.Mock).mockResolvedValueOnce(true);
      (mockBcrypt.hash as jest.Mock).mockRejectedValueOnce(
        new Error("Hashing failed")
      );

      const result = await changePassword(mockFormData, mockUserDetails);

      expect(result).toBe(false);
      expect(mockDb.update).not.toHaveBeenCalled();
    });
  });

  describe("database update errors", () => {
    it("should return false when database update fails", async () => {
      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };
      (mockBcrypt.compare as jest.Mock).mockResolvedValueOnce(true);
      (mockBcrypt.hash as jest.Mock).mockResolvedValueOnce(
        "new-hashed-password"
      );
      (mockDb.update as jest.Mock).mockImplementationOnce(() => {
        throw new Error("Update failed");
      });

      const result = await changePassword(mockFormData, mockUserDetails);

      expect(result).toBe(false);
    });
  });

  describe("edge cases", () => {
    it("should handle same current and new password", async () => {
      const samePasswordData = {
        currentPassword: "SamePass123!", // NOSONAR
        newPassword: "SamePass123!", // NOSONAR
        confirmPassword: "SamePass123!", // NOSONAR
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };
      (mockBcrypt.compare as jest.Mock).mockResolvedValueOnce(true);
      (mockBcrypt.hash as jest.Mock).mockResolvedValueOnce(
        "same-hashed-password"
      );
      (mockDb.update as jest.Mock).mockReturnValueOnce({
        set: jest.fn().mockReturnValueOnce({
          where: jest.fn().mockResolvedValueOnce(undefined),
        }),
      });

      const result = await changePassword(samePasswordData, mockUserDetails);

      expect(result).toBe(true);
    });

    it("should handle empty password fields", async () => {
      const emptyPasswordData = {
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      };

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(mockUser),
        },
      };
      (mockBcrypt.compare as jest.Mock).mockResolvedValueOnce(false);

      const result = await changePassword(emptyPasswordData, mockUserDetails);

      expect(result).toBe(false);
    });

    it("should handle user with missing passwordHash", async () => {
      const userWithoutHash = { ...mockUser, passwordHash: undefined };
      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockResolvedValueOnce(userWithoutHash),
        },
      };

      const result = await changePassword(mockFormData, mockUserDetails);

      expect(result).toBe(false);
    });
  });

  describe("console logging", () => {
    it("should log errors to console", async () => {
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();
      const testError = new Error("Test error");

      (mockDb.query as unknown as PartialDbQuery) = {
        users: {
          findFirst: jest.fn().mockRejectedValueOnce(testError),
        },
      };

      await changePassword(mockFormData, mockUserDetails);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Password change error:",
        testError
      );
    });
  });
});
