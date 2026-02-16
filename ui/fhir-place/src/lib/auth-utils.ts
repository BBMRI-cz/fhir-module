import { auth } from "../../auth";
import { getUserById } from "./auth";

export async function getCurrentUser() {
  const session = await auth();

  if (!session?.user?.id) {
    return null;
  }

  try {
    const user = await getUserById(session.user.id);

    if (!user.isActive) {
      return null;
    }

    return {
      id: user.id,
      username: user.username,
      firstName: user.firstName,
      lastName: user.lastName,
      email: user.email,
      isActive: user.isActive,
      createdAt: user.createdAt,
      updatedAt: user.updatedAt,
    };
  } catch {
    return null;
  }
}

export async function verifyAuthentication() {
  const user = await getCurrentUser();
  return user !== null;
}

export async function getSessionData() {
  const session = await auth();
  const user = await getCurrentUser();

  if (!session?.user?.id || !user) {
    return null;
  }

  return {
    user,
    sessionId: session.user.id,
  };
}

export interface UserDetails {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}
