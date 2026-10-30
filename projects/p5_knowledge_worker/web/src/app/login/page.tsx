import type { Metadata } from "next";

import { AuthCard } from "@/components/auth/auth-card";
import { AuthFooter } from "@/components/auth/auth-footer";
import { AuthHeader } from "@/components/auth/auth-header";
import { SignInForm } from "@/components/auth/sign-in-form";

export const metadata: Metadata = {
  title: "Sign in · Enterprise Knowledge Worker",
};

export default function LoginPage() {
  return (
    <AuthCard>
      <AuthHeader title="Welcome back" description="Sign in to search and ask your documents" />
      <SignInForm />
      <AuthFooter prompt="Don't have an account?" linkText="Sign up" href="/register" />
    </AuthCard>
  );
}
