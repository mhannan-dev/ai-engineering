import Link from "next/link";

export function AuthFooter({
  prompt,
  linkText,
  href,
}: {
  prompt: string;
  linkText: string;
  href: string;
}) {
  return (
    <p className="text-center text-sm text-zinc-600 dark:text-zinc-400">
      {prompt}{" "}
      <Link
        href={href}
        className="font-semibold text-zinc-900 hover:text-zinc-700 dark:text-zinc-300 dark:hover:text-zinc-100"
      >
        {linkText}
      </Link>
    </p>
  );
}
