import { eq } from "drizzle-orm";
import { db } from "@/lib/db/db";
import { users, type User } from "@/lib/db/schema";
import { UserNotFoundError, DatabaseError } from "@/lib/errors";

export async function getUserById(id: string): Promise<User> {
  try {
    const result = await db.select().from(users).where(eq(users.id, id));
    if (!result[0]) {
      throw new UserNotFoundError(id);
    }
    return result[0];
  } catch (error) {
    if (error instanceof UserNotFoundError) {
      throw error;
    }
    throw new DatabaseError(`Failed to get user by ID: ${id}`, error);
  }
}

export async function getUserByUsername(username: string): Promise<User> {
  try {
    const result = await db
      .select()
      .from(users)
      .where(eq(users.username, username));
    if (!result[0]) {
      throw new UserNotFoundError(username);
    }
    return result[0];
  } catch (error) {
    if (error instanceof UserNotFoundError) {
      throw error;
    }
    throw new DatabaseError(
      `Failed to get user by username: ${username}`,
      error
    );
  }
}

export async function userExistsById(id: string): Promise<boolean> {
  try {
    const result = await db.select().from(users).where(eq(users.id, id));
    return !!result[0] && !!result[0].isActive;
  } catch {
    return false;
  }
}
