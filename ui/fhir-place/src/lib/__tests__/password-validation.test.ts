import {
  validatePassword,
  getPasswordRequirementsDescription,
} from "../password-validation";

// Mock environment variables for consistent testing
const originalEnv = process.env;

beforeEach(() => {
  jest.resetModules();
  process.env = {
    ...originalEnv,
    NEXT_PUBLIC_PASSWORD_MIN_LENGTH: "8", // NOSONAR
    NEXT_PUBLIC_PASSWORD_MAX_LENGTH: "128", // NOSONAR
    NEXT_PUBLIC_PASSWORD_REQUIRE_UPPERCASE: "true", // NOSONAR
    NEXT_PUBLIC_PASSWORD_REQUIRE_LOWERCASE: "true", // NOSONAR
    NEXT_PUBLIC_PASSWORD_REQUIRE_NUMBERS: "true", // NOSONAR
    NEXT_PUBLIC_PASSWORD_REQUIRE_SPECIAL_CHARS: "true", // NOSONAR
    NEXT_PUBLIC_PASSWORD_SPECIAL_CHARS: "!@#$%^&*()_+-=[]{}|;:,.<>?", // NOSONAR
  };
});

afterAll(() => {
  process.env = originalEnv;
});

describe("validatePassword", () => {
  it("should return valid for a strong password", () => {
    const result = validatePassword("StrongPass123!"); // NOSONAR

    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
    expect(result.requirements).toBeDefined();
  });

  it("should reject password that is too short", () => {
    const result = validatePassword("Short1!"); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain(
      "Password must be at least 8 characters long"
    );
  });

  it("should reject password without uppercase letter", () => {
    const result = validatePassword("lowercase123!"); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain(
      "Password must contain at least one uppercase letter"
    );
  });

  it("should reject password without lowercase letter", () => {
    const result = validatePassword("UPPERCASE123!"); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain(
      "Password must contain at least one lowercase letter"
    );
  });

  it("should reject password without numbers", () => {
    const result = validatePassword("PasswordNoNumbers!"); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain(
      "Password must contain at least one number"
    );
  });

  it("should reject password without special characters", () => {
    const result = validatePassword("PasswordWithNumbers123"); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain(
      "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
    );
  });

  it("should reject password that is too long", () => {
    const longPassword = "A".repeat(130) + "1!"; // NOSONAR
    const result = validatePassword(longPassword); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain(
      "Password must be no more than 128 characters long"
    );
  });

  it("should accumulate multiple errors", () => {
    const result = validatePassword("weak"); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(1);
    expect(result.errors).toContain(
      "Password must be at least 8 characters long"
    );
    expect(result.errors).toContain(
      "Password must contain at least one uppercase letter"
    );
    expect(result.errors).toContain(
      "Password must contain at least one number"
    );
    expect(result.errors).toContain(
      "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
    );
  });

  it("should work with different environment configurations", () => {
    // Test with less strict requirements
    process.env.NEXT_PUBLIC_PASSWORD_MIN_LENGTH = "6"; // NOSONAR
    process.env.NEXT_PUBLIC_PASSWORD_REQUIRE_UPPERCASE = "false"; // NOSONAR
    process.env.NEXT_PUBLIC_PASSWORD_REQUIRE_SPECIAL_CHARS = "false"; // NOSONAR

    // Re-import to get new env values
    jest.resetModules();

    const result = validatePassword("simple123"); // NOSONAR

    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });
});

describe("getPasswordRequirementsDescription", () => {
  it("should generate correct description for default requirements", () => {
    const description = getPasswordRequirementsDescription();

    expect(description).toContain("8-128 characters");
    expect(description).toContain("uppercase letter");
    expect(description).toContain("lowercase letter");
    expect(description).toContain("number");
    expect(description).toContain("special character");
  });

  it("should generate simpler description when only length is required", () => {
    process.env.NEXT_PUBLIC_PASSWORD_REQUIRE_UPPERCASE = "false"; // NOSONAR
    process.env.NEXT_PUBLIC_PASSWORD_REQUIRE_LOWERCASE = "false"; // NOSONAR
    process.env.NEXT_PUBLIC_PASSWORD_REQUIRE_NUMBERS = "false"; // NOSONAR
    process.env.NEXT_PUBLIC_PASSWORD_REQUIRE_SPECIAL_CHARS = "false"; // NOSONAR

    jest.resetModules();

    const description = getPasswordRequirementsDescription();

    expect(description).toBe("Password must be 8-128 characters");
  });
});
