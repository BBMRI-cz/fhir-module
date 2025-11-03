"use client";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  BarChart3,
  LogOut,
  Settings,
  Server,
  WandSparkles,
  Menu,
} from "lucide-react";
import Link from "next/link";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useState } from "react";
import { useBackendStatus } from "@/hooks/useBackendStatus";

interface User {
  username: string;
}

interface AuthorizedLayoutClientProps {
  user: User;
  onLogout: () => Promise<void>;
  children: React.ReactNode;
  isMiabisMode: boolean;
}

function NavigationItems() {
  return (
    <>
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
      <Link href="/setup-wizard">
        <Button variant="ghost" className="w-full justify-start">
          <WandSparkles className="mr-2 h-4 w-4" />
          Setup Wizard
        </Button>
      </Link>
    </>
  );
}

export function AuthorizedLayoutClient({
  user,
  onLogout,
  children,
  isMiabisMode,
}: AuthorizedLayoutClientProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const isBackendOnline = useBackendStatus(5000);

  let backendStatusVariant: "outline" | "default" | "destructive";
  let backendStatusIndicatorClass: string;
  let backendStatusText: string;

  if (isBackendOnline === null) {
    backendStatusVariant = "outline";
    backendStatusIndicatorClass = "bg-gray-400 animate-pulse";
    backendStatusText = "Checking...";
  } else if (isBackendOnline) {
    backendStatusVariant = "default";
    backendStatusIndicatorClass = "bg-green-500";
    backendStatusText = "Backend Online";
  } else {
    backendStatusVariant = "destructive";
    backendStatusIndicatorClass = "bg-white";
    backendStatusText = "Backend Offline";
  }

  return (
    <div className="flex h-screen bg-background">
      <header className="fixed top-0 w-full bg-card/50 backdrop-blur z-50">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            {/* Mobile menu button - only visible on small screens */}
            <div className="xl:hidden">
              <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="sm">
                    <Menu className="h-4 w-4" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="w-64">
                  <SheetHeader>
                    <SheetTitle className="flex items-center gap-2">
                      <Activity className="h-5 w-5 text-primary" />
                      FHIR Dashboard
                    </SheetTitle>
                  </SheetHeader>
                  <div className="mt-6">
                    <nav className="space-y-2">
                      <NavigationItems />
                    </nav>
                  </div>
                </SheetContent>
              </Sheet>
            </div>

            <div className="flex items-center gap-2">
              <Activity className="h-6 w-6 text-primary" />
              <h1 className="text-xl font-bold">FHIR Dashboard</h1>
            </div>
            <Badge
              variant={isMiabisMode ? "default" : "secondary"}
              className="hidden md:flex"
            >
              {isMiabisMode ? "MIABIS on FHIR" : "Standard Mode"}
            </Badge>
            <Badge
              variant={backendStatusVariant}
              className="hidden md:flex items-center gap-1"
            >
              <span
                className={`h-2 w-2 rounded-full ${backendStatusIndicatorClass}`}
              />
              {backendStatusText}
            </Badge>
            <p className="hidden sm:block text-sm text-muted-foreground">
              Welcome, {user.username}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/settings">
              <Button variant="ghost" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
            </Link>
            <form action={onLogout}>
              <Button variant="ghost" size="sm" type="submit">
                <LogOut className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </div>
      </header>

      <div className="flex mt-10 2xl:mt-12 w-full min-h-[calc(100vh-2rem)]">
        {/* Desktop sidebar - hidden on mobile */}
        <aside className="hidden xl:block w-64 min-w-64 bg-card/30 backdrop-blur flex-shrink-0">
          <div className="p-6">
            <nav className="space-y-2">
              <NavigationItems />
            </nav>
          </div>
        </aside>

        <main className="flex-1 p-0 2xl:p-6 min-w-0 h-[calc(100vh-4rem)] overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
