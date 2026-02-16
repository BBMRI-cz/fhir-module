import bcrypt from "bcryptjs";
import { db } from "@/lib/db/db";
import { users, type User, type NewUser } from "@/lib/db/schema";
import {
  UserNotFoundError,
  UserCreationError,
  InvalidCredentialsError,
  AuthenticationError,
} from "@/lib/errors";
import { validatePassword } from "@/lib/auth/password-validation";
import { getUserByUsername } from "@/lib/db/user-queries";
import crypto from "node:crypto";

export { getUserById, getUserByUsername } from "@/lib/db/user-queries";

export interface CreateUserData {
  username: string;
  password: string;
  firstName: string;
  lastName: string;
  email: string;
  mustChangePassword?: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export async function createUser(
  userData: CreateUserData,
  isSeed: boolean = false
): Promise<User> {
  const {
    username,
    password,
    firstName,
    lastName,
    email,
    mustChangePassword = false,
  } = userData;

  try {
    if (!isSeed) {
      const passwordValidation = await validatePassword(password);
      if (!passwordValidation.isValid) {
        throw new UserCreationError(
          username,
          new Error(passwordValidation.errors.join(", "))
        );
      }
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
      mustChangePassword: mustChangePassword ? 1 : 0,
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
