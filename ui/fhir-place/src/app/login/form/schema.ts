import { z } from "zod";
import { validatePassword } from "@/lib/password-validation";

export const LoginFormSchema = z.object({
  username: z.string().min(1, {
    message: "Username is required",
  }),
  password: z.string().min(1, { message: "Password is required" }),
});

export const RegisterFormSchema = z
  .object({
    firstName: z.string().min(1, {
      message: "First name is required",
    }),
    lastName: z.string().min(1, {
      message: "Last name is required",
    }),
    email: z.string().email({
      message: "Please enter a valid email address",
    }),
    username: z.string().min(3, {
      message: "Username must be at least 3 characters long",
    }),
    password: z.string().superRefine(async (password, ctx) => {
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
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });
