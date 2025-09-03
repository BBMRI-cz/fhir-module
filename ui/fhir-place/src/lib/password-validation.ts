export interface PasswordRequirements {
  minLength: number;
  maxLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  specialChars: string;
}

export interface PasswordValidationResult {
  isValid: boolean;
  errors: string[];
  requirements: PasswordRequirements;
}

function getPasswordRequirements(): PasswordRequirements {
  return {
    minLength: parseInt(process.env.NEXT_PUBLIC_PASSWORD_MIN_LENGTH || "8"),
    maxLength: parseInt(process.env.NEXT_PUBLIC_PASSWORD_MAX_LENGTH || "128"),
    requireUppercase:
      process.env.NEXT_PUBLIC_PASSWORD_REQUIRE_UPPERCASE === "true",
    requireLowercase:
      process.env.NEXT_PUBLIC_PASSWORD_REQUIRE_LOWERCASE === "true",
    requireNumbers: process.env.NEXT_PUBLIC_PASSWORD_REQUIRE_NUMBERS === "true",
    requireSpecialChars:
      process.env.NEXT_PUBLIC_PASSWORD_REQUIRE_SPECIAL_CHARS === "true",
    specialChars:
      process.env.NEXT_PUBLIC_PASSWORD_SPECIAL_CHARS ||
      "!@#$%^&*()_+-=[]{}|;:,.<>?",
  };
}

export function validatePassword(password: string): PasswordValidationResult {
  const requirements = getPasswordRequirements();
  const errors: string[] = [];

  if (password.length < requirements.minLength) {
    errors.push(
      `Password must be at least ${requirements.minLength} characters long`
    );
  }

  if (password.length > requirements.maxLength) {
    errors.push(
      `Password must be no more than ${requirements.maxLength} characters long`
    );
  }

  if (requirements.requireUppercase && !/[A-Z]/.test(password)) {
    errors.push("Password must contain at least one uppercase letter");
  }

  if (requirements.requireLowercase && !/[a-z]/.test(password)) {
    errors.push("Password must contain at least one lowercase letter");
  }

  if (requirements.requireNumbers && !/\d/.test(password)) {
    errors.push("Password must contain at least one number");
  }

  if (requirements.requireSpecialChars) {
    const specialChars = requirements.specialChars.split("");
    if (!specialChars.some((char) => password.includes(char))) {
      errors.push(
        `Password must contain at least one special character (${requirements.specialChars})`
      );
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    requirements,
  };
}

export function getPasswordRequirementsDescription(): string {
  const requirements = getPasswordRequirements();
  const descriptions: string[] = [];

  descriptions.push(
    `${requirements.minLength}-${requirements.maxLength} characters`
  );

  if (requirements.requireUppercase) {
    descriptions.push("uppercase letter");
  }

  if (requirements.requireLowercase) {
    descriptions.push("lowercase letter");
  }

  if (requirements.requireNumbers) {
    descriptions.push("number");
  }

  if (requirements.requireSpecialChars) {
    descriptions.push("special character");
  }

  if (descriptions.length === 1) {
    return `Password must be ${descriptions[0]}`;
  }

  const lastItem = descriptions.pop();
  return `Password must contain ${descriptions.join(", ")} and ${lastItem}`;
}
