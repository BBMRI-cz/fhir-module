import NextAuth from "next-auth";
import type { JWT } from "next-auth/jwt";
import type { Session, User } from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { authenticateUser, getUserById } from "@/lib/auth";
import { InvalidCredentialsError, AuthenticationError } from "@/lib/errors";
import { LoginFormSchema } from "@/app/login/form/schema";

const config = {
  trustHost:
    process.env.NODE_ENV === "development" ||
    process.env.AUTH_TRUST_HOST === "true",
  providers: [
    Credentials({
      name: "credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        try {
          const validatedCredentials = LoginFormSchema.parse({
            username: credentials?.username,
            password: credentials?.password,
          });

          const user = await authenticateUser({
            username: validatedCredentials.username,
            password: validatedCredentials.password,
          });

          if (user) {
            return {
              id: user.id,
              name: user.username,
              email: user.email || "",
              username: user.username,
              firstName: user.firstName || "",
              lastName: user.lastName || "",
              isActive: !!user.isActive,
            };
          }

          return null;
        } catch (error) {
          if (
            error instanceof InvalidCredentialsError ||
            error instanceof AuthenticationError
          ) {
            return null;
          }
          throw error;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }: { token: JWT; user: User | null }) {
      if (user) {
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }: { session: Session; token: JWT }) {
      if (token?.id) {
        session.user.id = token.id as string;

        try {
          const user = await getUserById(token.id as string);
          if (!user.isActive) {
            throw new Error("User is inactive");
          }

          session.user.name = user.username;
          session.user.email = user.email || "";
          session.user.firstName = user.firstName || "";
          session.user.lastName = user.lastName || "";
          session.user.username = user.username;
          session.user.isActive = !!user.isActive;
        } catch {
          throw new Error("User not found or inactive");
        }
      }
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt" as const,
  },
  secret: process.env.NEXTAUTH_SECRET,
};

export const { handlers, signIn, signOut, auth } = NextAuth(config);
