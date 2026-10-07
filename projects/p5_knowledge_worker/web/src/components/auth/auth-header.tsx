import Image from "next/image";

export function AuthHeader({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <header className="flex flex-col items-center text-center">
      <Image
        className="dark:invert"
        src="/next.svg"
        alt="Next.js logo"
        width={100}
        height={20}
        priority
      />
      <h1 className="mt-6 text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
        {title}
      </h1>
      <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">{description}</p>
    </header>
  );
}
