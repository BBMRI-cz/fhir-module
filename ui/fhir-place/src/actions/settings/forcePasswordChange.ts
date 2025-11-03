"use server";

import { z } from "zod";
import bcrypt from "bcryptjs";
import { UserDetails } from "@/lib/auth/auth-utils";
import { users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";
import { db } from "@/lib/db/db";
import { validatePassword } from "@/lib/auth/password-validation";

const ForcePasswordChangeSchema = z
  .object({
    newPassword: z.string().superRefine(async (password, ctx) => {
      const validation = await validatePassword(password);
      if (!validation.isValid) {
        for (const error of validation.errors) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: error,
            path: [],
          });
        }
      }
    }),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

export async function forcePasswordChange(
  formData: z.infer<typeof ForcePasswordChangeSchema>,
  userDetails: UserDetails
) {
  try {
    const validatedData = await ForcePasswordChangeSchema.parseAsync(formData);

    const saltRounds = 12;
    const newPasswordHash = await bcrypt.hash(
      validatedData.newPassword,
      saltRounds
    );

    await db
      .update(users)
      .set({
        passwordHash: newPasswordHash,
        mustChangePassword: 0,
        updatedAt: new Date().toISOString(),
      })
      .where(eq(users.id, userDetails.id));

    return { success: true };
  } catch (error) {
    console.error("Force password change error:", error);
    return {
      success: false,
      error:
        error instanceof Error ? error.message : "Failed to change password",
    };
  }
}
