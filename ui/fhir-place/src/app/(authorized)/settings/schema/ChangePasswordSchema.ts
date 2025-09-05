import { z } from "zod";
import { validatePassword } from "@/lib/password-validation";

export const ChangePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, {
      message: "Current password is required",
    }),
    newPassword: z.string().superRefine(async (password, ctx) => {
      const validation = await validatePassword(password);
      if (!validation.isValid) {
        validation.errors.forEach((error) => {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: error,
            path: [],
          });
        });
      }
    }),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });
