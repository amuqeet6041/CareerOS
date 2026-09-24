"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Loading from "@/components/shared/Loading";
import { useAuth } from "@/hooks/useAuth";

export default function DashboardLayout({ children }) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas">
        <Loading label="Loading your dashboard..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // redirecting to /login
  }

  return children;
}