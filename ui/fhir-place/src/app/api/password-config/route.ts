// src/app/api/password/password-config.ts
import type { PasswordRequirements } from "@/lib/password-validation";

let configCache: PasswordRequirements | null = null;
let cacheTime = 0;
const CACHE_DURATION = 60000;

export async function GET() {
  const now = Date.now();

  if (!configCache || now - cacheTime > CACHE_DURATION) {
    configCache = {
      minLength: parseInt(process.env.PASSWORD_MIN_LENGTH || "8"),
      maxLength: parseInt(process.env.PASSWORD_MAX_LENGTH || "128"),
      requireUppercase: process.env.PASSWORD_REQUIRE_UPPERCASE === "true",
      requireLowercase: process.env.PASSWORD_REQUIRE_LOWERCASE === "true",
      requireNumbers: process.env.PASSWORD_REQUIRE_NUMBERS === "true",
      requireSpecialChars:
        process.env.PASSWORD_REQUIRE_SPECIAL_CHARS === "true",
      specialChars:
        process.env.PASSWORD_SPECIAL_CHARS || "!@#$%^&*()_+-=[]{}|;:,.<>?",
    };
    cacheTime = now;
  }

  return Response.json(configCache);
}
