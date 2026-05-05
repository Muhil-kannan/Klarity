import type { Session } from "next-auth";

interface HeaderProps {
  user: Session["user"] | null;
}

export function Header({ user }: HeaderProps) {
  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-6 flex-shrink-0">
      <div />
      <div className="flex items-center gap-3">
        {user?.image && (
          <img
            src={user.image}
            alt={user.name ?? "User"}
            className="w-7 h-7 rounded-full"
          />
        )}
        {user?.name && (
          <span className="text-sm text-muted-foreground">{user.name}</span>
        )}
        {!user && (
          <a
            href="/login"
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Sign in
          </a>
        )}
      </div>
    </header>
  );
}
