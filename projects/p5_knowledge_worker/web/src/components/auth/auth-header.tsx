export function AuthHeader({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <header className="flex flex-col items-center text-center">
      <p className="text-sm font-semibold tracking-tight text-zinc-500 dark:text-zinc-400">
        Knowledge Worker
      </p>
      <h1 className="mt-4 text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
        {title}
      </h1>
      <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">{description}</p>
    </header>
  );
}
