import {
  createUser,
  getUserById,
  getUserByUsername,
  authenticateUser,
  type CreateUserData,
  type LoginCredentials,
} from "../auth";
import bcrypt from "bcryptjs";
import { eq } from "drizzle-orm";
import { db } from "../db";
import { users, type User } from "../schema";
import {
  UserNotFoundError,
  UserCreationError,
  InvalidCredentialsError,
  DatabaseError,
} from "../errors";
import { validatePassword } from "../password-validation";
import crypto from "crypto";

// Mock all dependencies
jest.mock("bcryptjs");
jest.mock("drizzle-orm");
jest.mock("../db");
jest.mock("../schema");
jest.mock("../password-validation");
jest.mock("crypto");

const mockBcrypt = bcrypt as jest.Mocked<typeof bcrypt>;
const mockEq = eq as jest.MockedFunction<typeof eq>;
const mockDb = db as jest.Mocked<typeof db>;
const mockValidatePassword = validatePassword as jest.MockedFunction<
  typeof validatePassword
>;
const mockCrypto = crypto as jest.Mocked<typeof crypto>;

// Helper functions to reduce nesting
const createValidationResult = (isValid: boolean, errors: string[] = []) => ({
  isValid,
  errors,
  requirements: {
    minLength: 8,
    maxLength: 128,
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSpecialChars: true,
    specialChars: "!@#$%^&*()_+-=[]{}|;:,.<>?",
  },
});

const setupSuccessfulPasswordValidation = () => {
  mockValidatePassword.mockReturnValueOnce(createValidationResult(true));
};

const setupFailedPasswordValidation = (errors: string[]) => {
  mockValidatePassword.mockReturnValueOnce(
    createValidationResult(false, errors)
  );
};

const setupBcryptHash = (hashedPassword = "hashed-password") => {
  (mockBcrypt.hash as jest.Mock).mockResolvedValueOnce(hashedPassword);
};

const setupBcryptCompareSuccess = () => {
  (mockBcrypt.compare as jest.Mock).mockResolvedValueOnce(true);
};

const setupBcryptCompareFailed = () => {
  (mockBcrypt.compare as jest.Mock).mockResolvedValueOnce(false);
};

const setupCryptoUUID = (uuid = "user-123") => {
  (mockCrypto.randomUUID as jest.Mock).mockReturnValueOnce(uuid);
};

const setupSuccessfulDbInsert = (returnUser: User) => {
  (mockDb.insert as jest.Mock).mockReturnValueOnce({
    values: jest.fn().mockReturnValueOnce({
      returning: jest.fn().mockResolvedValueOnce([returnUser]),
    }),
  });
};

const setupFailedDbInsert = () => {
  (mockDb.insert as jest.Mock).mockReturnValueOnce({
    values: jest.fn().mockReturnValueOnce({
      returning: jest.fn().mockResolvedValueOnce([]),
    }),
  });
};

const setupSuccessfulDbSelect = (returnUser: User) => {
  (mockDb.select as jest.Mock).mockReturnValueOnce({
    from: jest.fn().mockReturnValueOnce({
      where: jest.fn().mockResolvedValueOnce([returnUser]),
    }),
  });
};

const setupFailedDbSelect = () => {
  (mockDb.select as jest.Mock).mockReturnValueOnce({
    from: jest.fn().mockReturnValueOnce({
      where: jest.fn().mockResolvedValueOnce([]),
    }),
  });
};

const setupDbError = (error: Error) => {
  (mockDb.select as jest.Mock).mockImplementationOnce(() => {
    throw error;
  });
};

describe("auth library", () => {
  const mockUser: User = {
    id: "user-123",
    username: "testuser",
    passwordHash: "hashed-password", // NOSONAR
    firstName: "John",
    lastName: "Doe",
    email: "john.doe@example.com",
    isActive: 1, // Changed from boolean to number to match schema
    createdAt: "2024-01-01T00:00:00.000Z",
    updatedAt: "2024-01-01T00:00:00.000Z",
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("createUser", () => {
    const validUserData: CreateUserData = {
      username: "testuser",
      password: "StrongPass123!", // NOSONAR
      firstName: "John",
      lastName: "Doe",
      email: "john.doe@example.com",
    };

    describe("successful user creation", () => {
      it("should create user successfully with valid data", async () => {
        setupSuccessfulPasswordValidation();
        setupBcryptHash();
        setupCryptoUUID();
        setupSuccessfulDbInsert(mockUser);

        const result = await createUser(validUserData);

        expect(result).toEqual(mockUser);
        expect(mockValidatePassword).toHaveBeenCalledWith("StrongPass123!"); // NOSONAR
        expect(mockBcrypt.hash).toHaveBeenCalledWith("StrongPass123!", 12); // NOSONAR
        expect(mockCrypto.randomUUID).toHaveBeenCalled();
      });
    });

    describe("password validation errors", () => {
      it("should throw UserCreationError when password is invalid", async () => {
        setupFailedPasswordValidation([
          "Password must be at least 8 characters long",
        ]);

        await expect(createUser(validUserData)).rejects.toThrow(
          UserCreationError
        );
        expect(mockBcrypt.hash).not.toHaveBeenCalled();
      });

      it("should include all validation errors in UserCreationError", async () => {
        const validationErrors = [
          "Password must be at least 8 characters long",
          "Password must contain at least one uppercase letter",
        ];
        setupFailedPasswordValidation(validationErrors);

        await expect(createUser(validUserData)).rejects.toThrow(
          expect.objectContaining({
            message: expect.stringContaining("testuser"),
          })
        );
      });
    });

    describe("database errors", () => {
      it("should throw UserCreationError when database insert fails", async () => {
        setupSuccessfulPasswordValidation();
        setupBcryptHash();
        setupCryptoUUID();
        setupFailedDbInsert();

        await expect(createUser(validUserData)).rejects.toThrow(
          UserCreationError
        );
      });

      it("should wrap unexpected errors in UserCreationError", async () => {
        setupSuccessfulPasswordValidation();
        (mockBcrypt.hash as jest.Mock).mockRejectedValueOnce(
          new Error("Hashing failed")
        );

        await expect(createUser(validUserData)).rejects.toThrow(
          UserCreationError
        );
      });
    });
  });

  describe("getUserById", () => {
    describe("successful retrieval", () => {
      it("should return user when found", async () => {
        setupSuccessfulDbSelect(mockUser);

        const result = await getUserById("user-123");

        expect(result).toEqual(mockUser);
        expect(mockEq).toHaveBeenCalledWith(users.id, "user-123");
      });
    });

    describe("user not found", () => {
      it("should throw UserNotFoundError when user does not exist", async () => {
        setupFailedDbSelect();

        await expect(getUserById("nonexistent")).rejects.toThrow(
          UserNotFoundError
        );
      });
    });

    describe("database errors", () => {
      it("should throw DatabaseError when database query fails", async () => {
        setupDbError(new Error("Database connection failed"));

        await expect(getUserById("user-123")).rejects.toThrow(DatabaseError);
      });

      it("should preserve UserNotFoundError when explicitly thrown", async () => {
        const userNotFoundError = new UserNotFoundError("user-123");
        (mockDb.select as jest.Mock).mockReturnValueOnce({
          from: jest.fn().mockReturnValueOnce({
            where: jest.fn().mockRejectedValueOnce(userNotFoundError),
          }),
        });

        await expect(getUserById("user-123")).rejects.toThrow(
          UserNotFoundError
        );
      });
    });
  });

  describe("getUserByUsername", () => {
    describe("successful retrieval", () => {
      it("should return user when found", async () => {
        setupSuccessfulDbSelect(mockUser);

        const result = await getUserByUsername("testuser");

        expect(result).toEqual(mockUser);
        expect(mockEq).toHaveBeenCalledWith(users.username, "testuser");
      });
    });

    describe("user not found", () => {
      it("should throw UserNotFoundError when user does not exist", async () => {
        setupFailedDbSelect();

        await expect(getUserByUsername("nonexistent")).rejects.toThrow(
          UserNotFoundError
        );
      });
    });
  });

  describe("authenticateUser", () => {
    const validCredentials: LoginCredentials = {
      username: "testuser",
      password: "StrongPass123!", // NOSONAR
    };

    describe("successful authentication", () => {
      it("should return user when credentials are valid", async () => {
        setupSuccessfulDbSelect(mockUser);
        setupBcryptCompareSuccess();

        const result = await authenticateUser(validCredentials);

        expect(result).toEqual(mockUser);
        expect(mockBcrypt.compare).toHaveBeenCalledWith(
          "StrongPass123!", // NOSONAR
          "hashed-password" // NOSONAR
        );
      });
    });

    describe("invalid credentials", () => {
      it("should throw InvalidCredentialsError when user not found", async () => {
        setupFailedDbSelect();

        await expect(authenticateUser(validCredentials)).rejects.toThrow(
          InvalidCredentialsError
        );
        expect(mockBcrypt.compare).not.toHaveBeenCalled();
      });

      it("should throw InvalidCredentialsError when password is incorrect", async () => {
        setupSuccessfulDbSelect(mockUser);
        setupBcryptCompareFailed();

        await expect(authenticateUser(validCredentials)).rejects.toThrow(
          InvalidCredentialsError
        );
      });
    });

    describe("edge cases", () => {
      it("should handle empty username", async () => {
        const emptyCredentials = { username: "", password: "password" }; // NOSONAR
        setupFailedDbSelect();

        await expect(authenticateUser(emptyCredentials)).rejects.toThrow(
          InvalidCredentialsError
        );
      });

      it("should handle empty password", async () => {
        const emptyPasswordCredentials = { username: "testuser", password: "" }; // NOSONAR
        setupSuccessfulDbSelect(mockUser);
        setupBcryptCompareFailed();

        await expect(
          authenticateUser(emptyPasswordCredentials)
        ).rejects.toThrow(InvalidCredentialsError);
      });
    });
  });
});
