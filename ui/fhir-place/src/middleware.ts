import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";

async function verifyUserExists(
  userId: string,
  baseUrl: string
): Promise<boolean> {
  try {
    const response = await fetch(`${baseUrl}/api/auth/verify-user`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userId }),
    });
    if (!response.ok) return false;
    const data = await response.json();
    return data.exists === true;
  } catch {
    return false;
  }
}

export async function middleware(req: NextRequest) {
  const path = req.nextUrl.pathname;
  const isPublicRoute =
    path === "/login" || path === "/register" || path === "/";

  const token = await getToken({
    req,
    secret: process.env.NEXTAUTH_SECRET,
  });

  const hasToken = !!token?.id;

  if (hasToken) {
    const baseUrl = req.nextUrl.origin;
    const userExists = await verifyUserExists(token.id as string, baseUrl);
    if (!userExists) {
      const response = NextResponse.redirect(new URL("/login", req.nextUrl));
      response.cookies.delete("next-auth.session-token");
      response.cookies.delete("__Secure-next-auth.session-token");
      return response;
    }
  }

  if (isPublicRoute && !hasToken) {
    return NextResponse.next();
  }

  if (isPublicRoute && hasToken) {
    return NextResponse.redirect(new URL("/dashboard", req.nextUrl));
  }

  if (!isPublicRoute && !hasToken) {
    const response = NextResponse.redirect(new URL("/login", req.nextUrl));
    response.cookies.delete("next-auth.session-token");
    response.cookies.delete("__Secure-next-auth.session-token");
    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - Static files with extensions (.png, .jpg, .svg, etc.)
     */
    "/((?!api|_next/static|_next/image|favicon.ico|.*\\.png$|.*\\.jpg$|.*\\.jpeg$|.*\\.svg$|.*\\.gif$|.*\\.ico$).*)",
  ],
};
