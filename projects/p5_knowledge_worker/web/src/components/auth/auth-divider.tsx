export function AuthDivider() {
  return (
    <div className="relative">
      <div className="absolute inset-0 flex items-center">
        <div className="w-full border-t border-zinc-300 dark:border-zinc-700" />
      </div>
      <div className="relative flex justify-center text-sm">
        <span className="bg-white px-2 text-zinc-500 dark:bg-zinc-900 dark:text-zinc-400">
          Or continue with
        </span>
      </div>
    </div>
  );
}
