"use client";

import { Button } from "@/components/ui/button";
import { Activity, Home, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-8">
      <div className="text-center space-y-6 max-w-2xl">
        <div className="flex justify-center mb-8">
          <Activity className="h-20 w-20 text-primary animate-pulse" />
        </div>

        <h1 className="text-8xl font-bold text-primary">404</h1>

        <h2 className="text-3xl font-semibold tracking-tight">
          Page Not Found
        </h2>

        <p className="text-lg text-muted-foreground max-w-md mx-auto">
          Oops! The page you&apos;re looking for doesn&apos;t exist. It might
          have been moved or deleted.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
          <Link href="/">
            <Button size="lg" className="gap-2">
              <Home className="h-4 w-4" />
              Go Home
            </Button>
          </Link>
          <Button
            size="lg"
            variant="outline"
            className="gap-2"
            onClick={() => globalThis.history.back()}
          >
            <ArrowLeft className="h-4 w-4" />
            Go Back
          </Button>
        </div>
      </div>
    </div>
  );
}
