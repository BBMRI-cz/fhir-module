import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";

const protectedRoutes = new Set([
  "/dashboard",
  "/mappings",
  "/setup-wizard",
  "/settings",
  "/backend-control",
]);

export async function middleware(req: NextRequest) {
  const path = req.nextUrl.pathname;
  const isProtectedRoute = protectedRoutes.has(path);
  const isPublicRoute =
    path === "/login" || path === "/register" || path === "/";

  const token = await getToken({
    req,
    secret: process.env.NEXTAUTH_SECRET,
  });

  const isValidToken = token?.id;

  if (isPublicRoute && !isValidToken) {
    return NextResponse.next();
  }

  if (isPublicRoute && isValidToken) {
    return NextResponse.redirect(new URL("/dashboard", req.nextUrl));
  }

  if (isProtectedRoute && !isValidToken) {
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
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
