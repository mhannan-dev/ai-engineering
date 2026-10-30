import type { Metadata } from "next";

import { AuthCard } from "@/components/auth/auth-card";
import { AuthFooter } from "@/components/auth/auth-footer";
import { AuthHeader } from "@/components/auth/auth-header";
import { SignUpForm } from "@/components/auth/sign-up-form";

export const metadata: Metadata = {
  title: "Sign up · Enterprise Knowledge Worker",
};

export default function RegisterPage() {
  return (
    <AuthCard>
      <AuthHeader
        title="Create your account"
        description="Your documents stay private to your account"
      />
      <SignUpForm />
      <AuthFooter prompt="Already have an account?" linkText="Sign in" href="/login" />
    </AuthCard>
  );
}
