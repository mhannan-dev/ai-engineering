import { AuthCard } from "@/components/auth/auth-card";
import { AuthFooter } from "@/components/auth/auth-footer";
import { AuthHeader } from "@/components/auth/auth-header";
import { ForgotPasswordForm } from "@/components/auth/forgot-password-form";

export default function ForgotPasswordPage() {
  return (
    <AuthCard>
      <AuthHeader
        title="Forgot your password?"
        description="No worries. Enter your email and we'll send you a link to reset it."
      />
      <ForgotPasswordForm />
      <AuthFooter prompt="Remembered it?" linkText="Back to sign in" href="/" />
    </AuthCard>
  );
}
