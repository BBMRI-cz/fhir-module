import { logout } from "@/actions/auth-management/logout";
import { Button } from "@/components/ui/button";
import { getCurrentUser } from "@/lib/auth-utils";
import { Activity, BarChart3, LogOut, Settings, Server } from "lucide-react";
import { redirect } from "next/navigation";
import Link from "next/link";

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const user = await getCurrentUser();

  if (!user) {
    redirect("/login");
  }

  async function handleLogout() {
    "use server";
    await logout();
  }

  return (
    <div className="flex h-screen bg-background">
      <header className="fixed top-0 w-full bg-card/50 backdrop-blur">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Activity className="h-6 w-6 text-primary" />
              <h1 className="text-xl font-bold">FHIR Dashboard</h1>
            </div>
            <p className="text-sm text-muted-foreground">
              Welcome, {user.username}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/settings">
              <Button variant="ghost" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
            </Link>
            <form action={handleLogout}>
              <Button variant="ghost" size="sm" type="submit">
                <LogOut className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </div>
      </header>

      <div className="flex mt-16 w-full">
        <aside className="w-64  bg-card/30 backdrop-blur h-full">
          <div className="p-6">
            <nav className="space-y-2">
              <Link href="/dashboard">
                <Button variant="ghost" className="w-full justify-start">
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Dashboard
                </Button>
              </Link>
              <Link href="/backend-control">
                <Button variant="ghost" className="w-full justify-start">
                  <Server className="mr-2 h-4 w-4" />
                  Backend Control
                </Button>
              </Link>
            </nav>
          </div>
        </aside>

        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
