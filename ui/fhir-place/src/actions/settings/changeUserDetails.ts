"use server";

import { z } from "zod";
import { ChangeUserDetailsSchema } from "@/app/(authorized)/settings/schema/ChangeUserDetailsSchema";
import { UserDetails } from "@/lib/auth-utils";
import { users } from "@/lib/schema";
import { eq } from "drizzle-orm";
import { db } from "@/lib/db";

export async function changeUserDetails(
  formData: z.infer<typeof ChangeUserDetailsSchema>,
  userDetails: UserDetails
) {
  try {
    const validatedData = ChangeUserDetailsSchema.parse(formData);

    const user = await db.query.users.findFirst({
      where: eq(users.id, userDetails.id),
    });

    if (!user) {
      throw new Error("User not found");
    }

    const updateData: {
      updatedAt: string;
      firstName?: string;
      lastName?: string;
      email?: string;
    } = {
      updatedAt: new Date().toISOString(),
    };

    if (validatedData.firstName && validatedData.firstName.trim() !== "") {
      updateData.firstName = validatedData.firstName.trim();
    }

    if (validatedData.lastName && validatedData.lastName.trim() !== "") {
      updateData.lastName = validatedData.lastName.trim();
    }

    if (validatedData.email && validatedData.email.trim() !== "") {
      updateData.email = validatedData.email.trim();
    }

    if (Object.keys(updateData).length > 1) {
      await db
        .update(users)
        .set(updateData)
        .where(eq(users.id, userDetails.id));
    }

    return true;
  } catch (error) {
    console.error("User details change error:", error);
    return false;
  }
}
