import { forcePasswordChange } from "../forcePasswordChange";
import { db } from "@/lib/db/db";
import bcrypt from "bcryptjs";
import { validatePassword } from "@/lib/auth/password-validation";

// Mock dependencies
jest.mock("@/lib/db/db", () => ({
  db: {
    update: jest.fn(),
  },
}));

jest.mock("bcryptjs", () => ({
  hash: jest.fn(),
}));

jest.mock("@/lib/auth/password-validation", () => ({
  validatePassword: jest.fn(),
}));

describe("forcePasswordChange", () => {
  const mockUserDetails = {
    id: "1",
    username: "testuser",
    firstName: "John",
    lastName: "Doe",
    email: "test@example.com",
    isActive: true,
    mustChangePassword: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock db.update to return a chainable object
    const mockWhere = jest.fn().mockResolvedValue(undefined);
    const mockSet = jest.fn().mockReturnValue({ where: mockWhere });
    (db.update as jest.Mock).mockReturnValue({ set: mockSet });
  });

  it("should successfully change password", async () => {
    (validatePassword as jest.Mock).mockResolvedValue({
      isValid: true,
      errors: [],
    });
    (bcrypt.hash as jest.Mock).mockResolvedValue("hashed_password");

    const formData = {
      newPassword: "NewPassword123!", // NOSONAR
      confirmPassword: "NewPassword123!", // NOSONAR
    };

    const result = await forcePasswordChange(formData, mockUserDetails);

    expect(result.success).toBe(true);
    expect(bcrypt.hash).toHaveBeenCalledWith("NewPassword123!", 12); // NOSONAR
  });

  it("should fail when passwords don't match", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    (validatePassword as jest.Mock).mockResolvedValue({
      isValid: true,
      errors: [],
    });

    const formData = {
      newPassword: "NewPassword123!", // NOSONAR
      confirmPassword: "DifferentPassword123!", // NOSONAR
    };

    const result = await forcePasswordChange(formData, mockUserDetails);

    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();

    consoleSpy.mockRestore();
  });

  it("should fail with invalid password", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    (validatePassword as jest.Mock).mockResolvedValue({
      isValid: false,
      errors: ["Password must be at least 8 characters"],
    });

    const formData = {
      newPassword: "weak", // NOSONAR
      confirmPassword: "weak", // NOSONAR
    };

    const result = await forcePasswordChange(formData, mockUserDetails);

    expect(result.success).toBe(false);

    consoleSpy.mockRestore();
  });

  it("should handle database errors", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    (validatePassword as jest.Mock).mockResolvedValue({
      isValid: true,
      errors: [],
    });
    (bcrypt.hash as jest.Mock).mockResolvedValue("hashed_password");

    const mockWhere = jest.fn().mockRejectedValue(new Error("Database error"));
    const mockSet = jest.fn().mockReturnValue({ where: mockWhere });
    (db.update as jest.Mock).mockReturnValue({ set: mockSet });

    const formData = {
      newPassword: "NewPassword123!", // NOSONAR
      confirmPassword: "NewPassword123!", // NOSONAR
    };

    const result = await forcePasswordChange(formData, mockUserDetails);

    expect(result.success).toBe(false);
    expect(result.error).toContain("Database error");

    consoleSpy.mockRestore();
  });

  it("should reset mustChangePassword flag", async () => {
    (validatePassword as jest.Mock).mockResolvedValue({
      isValid: true,
      errors: [],
    });
    (bcrypt.hash as jest.Mock).mockResolvedValue("hashed_password");

    const mockWhere = jest.fn().mockResolvedValue(undefined);
    const mockSet = jest.fn().mockReturnValue({ where: mockWhere });
    (db.update as jest.Mock).mockReturnValue({ set: mockSet });

    const formData = {
      newPassword: "NewPassword123!", // NOSONAR
      confirmPassword: "NewPassword123!", // NOSONAR
    };

    await forcePasswordChange(formData, mockUserDetails);

    expect(mockSet).toHaveBeenCalledWith(
      expect.objectContaining({
        mustChangePassword: 0,
      })
    );
  });
});
