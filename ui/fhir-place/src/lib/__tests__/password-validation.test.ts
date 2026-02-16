import {
  validatePassword,
  getPasswordRequirementsDescription,
  resetClientCache,
} from "../password-validation";

// Mock fetch for client-side tests
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock environment variables for consistent testing
const originalEnv = process.env;

beforeEach(() => {
  jest.resetModules();
  jest.clearAllMocks();

  // Reset the client cache to prevent test interference
  resetClientCache();

  // Mock fetch to return the expected password configuration
  mockFetch.mockResolvedValue({
    ok: true,
    json: async () => ({
      minLength: 8,
      maxLength: 128,
      requireUppercase: true,
      requireLowercase: true,
      requireNumbers: true,
      requireSpecialChars: true,
      specialChars: "!@#$%^&*()_+-=[]{}|;:,.<>?",
    }),
  });
});

afterAll(() => {
  process.env = originalEnv;
});

describe("validatePassword", () => {
  it("should return valid for a strong password", async () => {
    const result = await validatePassword("StrongPass123!"); // NOSONAR

    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
    expect(result.requirements).toBeDefined();
  });

  it("should reject password that is too short", async () => {
    const result = await validatePassword("Short1!"); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain(
      "Password must be at least 8 characters long"
    );
  });

  it("should reject password without uppercase letter", async () => {
    const result = await validatePassword("lowercase123!"); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain(
      "Password must contain at least one uppercase letter"
    );
  });

  it("should reject password without lowercase letter", async () => {
    const result = await validatePassword("UPPERCASE123!"); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain(
      "Password must contain at least one lowercase letter"
    );
  });

  it("should reject password without numbers", async () => {
    const result = await validatePassword("PasswordNoNumbers!"); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain(
      "Password must contain at least one number"
    );
  });

  it("should reject password without special characters", async () => {
    const result = await validatePassword("PasswordWithNumbers123"); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain(
      "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
    );
  });

  it("should reject password that is too long", async () => {
    const longPassword = "A".repeat(130) + "1!"; // NOSONAR
    const result = await validatePassword(longPassword); // NOSONAR

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain(
      "Password must be no more than 128 characters long"
    );
  });

  it("should accumulate multiple errors", async () => {
    const result = await validatePassword("weak"); // NOSONAR

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

  it("should work with different environment configurations", async () => {
    // Mock fetch to return the updated configuration
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        minLength: 6,
        maxLength: 128,
        requireUppercase: false,
        requireLowercase: true,
        requireNumbers: true,
        requireSpecialChars: false,
        specialChars: "!@#$%^&*()_+-=[]{}|;:,.<>?",
      }),
    });

    const result = await validatePassword("simple123"); // NOSONAR

    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });
});

describe("getPasswordRequirementsDescription", () => {
  it("should generate correct description for default requirements", async () => {
    const description = await getPasswordRequirementsDescription();

    expect(description).toContain("8-128 characters");
    expect(description).toContain("uppercase letter");
    expect(description).toContain("lowercase letter");
    expect(description).toContain("number");
    expect(description).toContain("special character");
  });

  it("should generate simpler description when only length is required", async () => {
    // Mock fetch to return the updated configuration
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        minLength: 8,
        maxLength: 128,
        requireUppercase: false,
        requireLowercase: false,
        requireNumbers: false,
        requireSpecialChars: false,
        specialChars: "!@#$%^&*()_+-=[]{}|;:,.<>?",
      }),
    });

    const description = await getPasswordRequirementsDescription();

    expect(description).toBe("Password must be 8-128 characters");
  });
});
