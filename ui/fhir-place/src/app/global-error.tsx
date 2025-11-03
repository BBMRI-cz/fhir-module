"use client";

import { Button } from "@/components/ui/button";
import { Activity, Home, Link } from "lucide-react";

export default function GlobalError() {
  return (
    <main>
      <body>
        <div className="flex min-h-screen flex-col items-center justify-center bg-background p-8">
          <div className="text-center space-y-6 max-w-2xl">
            <div className="flex justify-center mb-8">
              <Activity className="h-20 w-20 text-destructive animate-pulse" />
            </div>

            <h1 className="text-6xl font-bold text-destructive">
              Critical Error
            </h1>

            <h2 className="text-3xl font-semibold tracking-tight">
              Application Error
            </h2>

            <p className="text-lg text-muted-foreground max-w-md mx-auto">
              We&apos;re experiencing a critical issue. Please refresh the page
              or contact support if the problem persists.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
              <Button
                size="lg"
                className="gap-2"
                onClick={() => globalThis.location.reload()}
              >
                Refresh Page
              </Button>
              <Link href="/">
                <Button size="lg" variant="outline" className="gap-2">
                  <Home className="h-4 w-4" />
                  Go Home
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </body>
    </main>
  );
}
