import { registerAction, type RegisterResult } from "../register";
import { createUser } from "@/lib/auth";
import { UserCreationError } from "@/lib/errors";
import { RegisterFormSchema } from "@/app/login/form/schema";
import { signIn } from "../../../../auth";
import { z } from "zod";

// Mock the dependencies
jest.mock("@/lib/auth");
jest.mock("@/app/login/form/schema", () => ({
  RegisterFormSchema: {
    safeParse: jest.fn(),
  },
}));

// Mock the signIn function from auth.ts
jest.mock("../../../../auth", () => ({
  signIn: jest.fn(),
}));

const mockCreateUser = createUser as jest.MockedFunction<typeof createUser>;
const mockRegisterFormSchema = RegisterFormSchema as jest.Mocked<
  typeof RegisterFormSchema
>;
const mockSignIn = signIn as jest.MockedFunction<typeof signIn>;

describe("registerAction", () => {
  const validFormData = {
    username: "testuser",
    password: "StrongPass123!", // NOSONAR
    confirmPassword: "StrongPass123!", // NOSONAR
    firstName: "John",
    lastName: "Doe",
    email: "john.doe@example.com",
  };

  const mockUser = {
    id: "user-123",
    username: "testuser",
    passwordHash: "hashed-password", // NOSONAR
    firstName: "John",
    lastName: "Doe",
    email: "john.doe@example.com",
    isActive: 1,
    createdAt: "2024-01-01T00:00:00.000Z",
    updatedAt: "2024-01-01T00:00:00.000Z",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (mockRegisterFormSchema.safeParse as jest.Mock).mockImplementation(
      (data) => ({
        success: true,
        data,
      })
    );
    mockSignIn.mockRejectedValue(new Error("Auto sign-in failed"));
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  describe("successful registration", () => {
    it("should return success result when user is created successfully", async () => {
      mockCreateUser.mockResolvedValueOnce(mockUser);

      const result: RegisterResult = await registerAction(validFormData);

      expect(result.success).toBe(true);
      expect(result.message).toBe(
        "Registration successful. Please log in with your credentials."
      );
      expect(result.user).toEqual({
        id: "user-123",
        username: "testuser",
      });
      expect(mockRegisterFormSchema.safeParse).toHaveBeenCalledWith(
        validFormData
      );
      expect(mockCreateUser).toHaveBeenCalledWith({
        username: "testuser",
        password: "StrongPass123!", // NOSONAR
        firstName: "John",
        lastName: "Doe",
        email: "john.doe@example.com",
      });
    });
  });

  describe("validation errors", () => {
    it("should return error result when form validation fails", async () => {
      const zodError = new z.ZodError([
        {
          code: "invalid_type",
          expected: "string",
          received: "undefined",
          path: ["username"],
          message: "Username is required",
        },
      ]);
      (mockRegisterFormSchema.safeParse as jest.Mock).mockImplementation(
        () => ({
          success: false,
          error: zodError,
        })
      );

      const result: RegisterResult = await registerAction(validFormData);

      expect(result.success).toBe(false);
      expect(result.message).toBe("Username is required");
      expect(result.user).toBeUndefined();
      expect(mockCreateUser).not.toHaveBeenCalled();
    });

    it("should return all validation errors when multiple errors exist", async () => {
      const zodError = new z.ZodError([
        {
          code: "invalid_type",
          expected: "string",
          received: "undefined",
          path: ["username"],
          message: "Username is required",
        },
        {
          code: "invalid_type",
          expected: "string",
          received: "undefined",
          path: ["email"],
          message: "Email is required",
        },
      ]);
      (mockRegisterFormSchema.safeParse as jest.Mock).mockImplementation(
        () => ({
          success: false,
          error: zodError,
        })
      );

      const result: RegisterResult = await registerAction(validFormData);

      expect(result.success).toBe(false);
      expect(result.message).toBe("Username is required, Email is required");
    });
  });

  describe("user creation errors", () => {
    it("should return error result when UserCreationError is thrown", async () => {
      const userCreationError = new UserCreationError(
        "testuser",
        new Error("Username already exists")
      );
      mockCreateUser.mockRejectedValueOnce(userCreationError);

      const result: RegisterResult = await registerAction(validFormData);

      expect(result.success).toBe(false);
      expect(result.message).toBe("Failed to create user: testuser");
      expect(result.user).toBeUndefined();
    });

    it("should handle UserCreationError with custom message", async () => {
      const customError = new UserCreationError("testuser");
      customError.message = "Email already in use";
      mockCreateUser.mockRejectedValueOnce(customError);

      const result: RegisterResult = await registerAction(validFormData);

      expect(result.success).toBe(false);
      expect(result.message).toBe("Email already in use");
    });
  });

  describe("unexpected errors", () => {
    it("should handle non-Error objects thrown", async () => {
      mockCreateUser.mockRejectedValueOnce("String error");

      const result: RegisterResult = await registerAction(validFormData);

      expect(result.success).toBe(false);
      expect(result.message).toBe(
        "An unexpected error occurred. Please try again."
      );
    });
  });

  describe("edge cases", () => {
    it("should handle empty form data", async () => {
      const emptyFormData = {
        username: "",
        firstName: "",
        lastName: "",
        email: "",
        password: "", // NOSONAR
        confirmPassword: "", // NOSONAR
      };
      const zodError = new z.ZodError([
        {
          code: "invalid_type",
          expected: "string",
          received: "undefined",
          path: ["username"],
          message: "Username is required",
        },
      ]);
      (mockRegisterFormSchema.safeParse as jest.Mock).mockImplementation(
        () => ({
          success: false,
          error: zodError,
        })
      );

      const result: RegisterResult = await registerAction(emptyFormData);

      expect(result.success).toBe(false);
      expect(result.message).toBe("Username is required");
    });
  });
});
