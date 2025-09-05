"use server";

import { z } from "zod";
import { createUser } from "@/lib/auth";
import { UserCreationError } from "@/lib/errors";
import { RegisterFormSchema } from "../../app/login/form/schema";
import { signIn } from "../../../auth";

export interface RegisterResult {
  success: boolean;
  message: string;
  user?: {
    id: string;
    username: string;
  };
}

export async function registerAction(
  formData: z.infer<typeof RegisterFormSchema>
): Promise<RegisterResult> {
  try {
    const validatedData = await RegisterFormSchema.safeParseAsync(formData);

    if (!validatedData.success) {
      const errorMessage = validatedData.error.errors
        .map((error) => error.message)
        .join(", ");
      return {
        success: false,
        message: errorMessage,
      };
    }

    const user = await createUser({
      username: validatedData.data.username,
      password: validatedData.data.password,
      firstName: validatedData.data.firstName,
      lastName: validatedData.data.lastName,
      email: validatedData.data.email,
    });

    try {
      await signIn("credentials", {
        username: validatedData.data.username,
        password: validatedData.data.password,
        redirect: false,
      });
    } catch (signInError) {
      console.error("Auto sign-in failed after registration:", signInError);
      return {
        success: true,
        message:
          "Registration successful. Please log in with your credentials.",
        user: {
          id: user.id,
          username: user.username,
        },
      };
    }

    return {
      success: true,
      message: "Registration successful. You are now logged in.",
      user: {
        id: user.id,
        username: user.username,
      },
    };
  } catch (error) {
    if (error instanceof UserCreationError) {
      return {
        success: false,
        message: error.message,
      };
    }

    if (error instanceof z.ZodError) {
      return {
        success: false,
        message: error.errors[0].message,
      };
    }

    return {
      success: false,
      message: "An unexpected error occurred. Please try again.",
    };
  }
}
