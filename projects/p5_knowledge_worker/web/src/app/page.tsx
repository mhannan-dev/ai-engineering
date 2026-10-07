import { AuthCard } from "@/components/auth/auth-card";
import { AuthDivider } from "@/components/auth/auth-divider";
import { AuthFooter } from "@/components/auth/auth-footer";
import { AuthHeader } from "@/components/auth/auth-header";
import { SignInForm } from "@/components/auth/sign-in-form";
import { SocialSignInButtons } from "@/components/auth/social-sign-in-buttons";

export default function LoginPage() {
  return (
    <AuthCard>
      <AuthHeader title="Welcome back" description="Sign in to your account to continue" />
      <SignInForm />
      <AuthDivider />
      <SocialSignInButtons />
      <AuthFooter prompt="Don't have an account?" linkText="Sign up" href="#" />
    </AuthCard>
  );
}
