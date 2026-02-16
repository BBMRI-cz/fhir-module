"use server";

import { z } from "zod";
import bcrypt from "bcryptjs";
import { ChangePasswordSchema } from "@/app/(authorized)/settings/schema/ChangePasswordSchema";
import { UserDetails } from "@/lib/auth-utils";
import { users } from "@/lib/schema";
import { eq } from "drizzle-orm";
import { db } from "@/lib/db";

export async function changePassword(
  formData: z.infer<typeof ChangePasswordSchema>,
  userDetails: UserDetails
) {
  try {
    const validatedData = ChangePasswordSchema.parse(formData);

    const user = await db.query.users.findFirst({
      where: eq(users.id, userDetails.id),
    });

    if (!user) {
      throw new Error("User not found");
    }

    const isCurrentPasswordValid = await bcrypt.compare(
      validatedData.currentPassword,
      user.passwordHash
    );

    if (!isCurrentPasswordValid) {
      throw new Error("Current password is incorrect");
    }

    const saltRounds = 12;
    const newPasswordHash = await bcrypt.hash(
      validatedData.newPassword,
      saltRounds
    );

    await db
      .update(users)
      .set({
        passwordHash: newPasswordHash,
        updatedAt: new Date().toISOString(),
      })
      .where(eq(users.id, userDetails.id));

    return true;
  } catch (error) {
    console.error("Password change error:", error);
    return false;
  }
}
