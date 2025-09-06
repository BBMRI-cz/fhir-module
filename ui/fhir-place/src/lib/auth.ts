import bcrypt from "bcryptjs";
import { eq } from "drizzle-orm";
import { db } from "./db";
import { users, type User, type NewUser } from "./schema";
import {
  UserNotFoundError,
  UserCreationError,
  InvalidCredentialsError,
  AuthenticationError,
  DatabaseError,
} from "./errors";
import { validatePassword } from "./password-validation";
import crypto from "crypto";

export interface CreateUserData {
  username: string;
  password: string;
  firstName: string;
  lastName: string;
  email: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export async function createUser(userData: CreateUserData): Promise<User> {
  const { username, password, firstName, lastName, email } = userData;

  try {
    const passwordValidation = await validatePassword(password);
    if (!passwordValidation.isValid) {
      throw new UserCreationError(
        username,
        new Error(passwordValidation.errors.join(", "))
      );
    }

    const saltRounds = 12;
    const passwordHash = await bcrypt.hash(password, saltRounds);

    const newUser: NewUser = {
      id: crypto.randomUUID(),
      username,
      passwordHash,
      firstName,
      lastName,
      email,
    };

    const result = await db.insert(users).values(newUser).returning();
    if (!result[0]) {
      throw new UserCreationError(username);
    }
    return result[0];
  } catch (error) {
    if (error instanceof UserCreationError) {
      throw error;
    }
    throw new UserCreationError(username, error);
  }
}

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

export async function authenticateUser(
  credentials: LoginCredentials
): Promise<User> {
  try {
    const { username, password } = credentials;

    let user: User;
    try {
      user = await getUserByUsername(username);
    } catch (error) {
      if (error instanceof UserNotFoundError) {
        throw new InvalidCredentialsError();
      }
      throw error;
    }

    const isValidPassword = await bcrypt.compare(password, user.passwordHash);

    if (!isValidPassword) {
      throw new InvalidCredentialsError();
    }

    return user;
  } catch (error) {
    if (error instanceof InvalidCredentialsError) {
      throw error;
    }
    throw new AuthenticationError("Authentication failed", error);
  }
}
