import { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface User {
    id: string;
    username: string;
    firstName: string;
    lastName: string;
    email: string;
    isActive: boolean;
    mustChangePassword: boolean;
  }

  interface Session {
    user: {
      id: string;
      username: string;
      firstName: string;
      lastName: string;
      isActive: boolean;
      mustChangePassword: boolean;
    } & DefaultSession["user"];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id?: string;
    mustChangePassword?: boolean;
  }
}
