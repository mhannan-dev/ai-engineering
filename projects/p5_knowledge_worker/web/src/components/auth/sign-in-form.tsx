import Link from "next/link";

import { FormField } from "@/components/auth/form-field";
import { PasswordField } from "@/components/auth/password-field";
import { SubmitButton } from "@/components/auth/submit-button";

function AccountOptions() {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center">
        <input
          id="remember-me"
          name="remember-me"
          type="checkbox"
          className="h-4 w-4 rounded border-zinc-300 text-zinc-900 focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:ring-offset-zinc-900 dark:focus:ring-zinc-400"
        />
        <label
          htmlFor="remember-me"
          className="ml-2 block text-sm text-zinc-700 dark:text-zinc-300"
        >
          Remember me
        </label>
      </div>
      <Link
        href="/forgot-password"
        className="text-sm font-medium text-zinc-900 hover:text-zinc-700 dark:text-zinc-300 dark:hover:text-zinc-100"
      >
        Forgot password?
      </Link>
    </div>
  );
}

export function SignInForm() {
  return (
    <form className="mt-8 space-y-6" action="#" method="POST">
      <div className="space-y-4 rounded-md shadow-sm">
        <FormField
          id="email"
          label="Email address"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
        />
        <PasswordField />
      </div>
      <AccountOptions />
      <SubmitButton>Sign in</SubmitButton>
    </form>
  );
}
