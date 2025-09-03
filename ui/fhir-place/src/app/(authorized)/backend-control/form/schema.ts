import { z } from "zod";

export const ConfirmDeleteSchema = z.object({
  confirmInput: z.string().min(1, {
    message: "Confirmation is required",
  }),
});
