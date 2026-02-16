import { z } from "zod";

export const ChangeUserDetailsSchema = z.object({
  firstName: z.string().optional(),
  lastName: z.string().optional(),
  email: z
    .string()
    .email("Please enter a valid email address")
    .optional()
    .or(z.literal("")),
});
