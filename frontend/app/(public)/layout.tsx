import React from 'react';

export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col min-h-screen bg-white text-slate-900">
      <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="container flex h-14 items-center">
          <div className="mr-4 hidden md:flex">
            <a className="mr-6 flex items-center space-x-2" href="/">
              <span className="hidden font-bold sm:inline-block">TSM99</span>
            </a>
            <nav className="flex items-center space-x-6 text-sm font-medium">
              <a href="/pricing" className="transition-colors hover:text-foreground/80 text-foreground/60">Pricing</a>
              <a href="/docs" className="transition-colors hover:text-foreground/80 text-foreground/60">Docs</a>
              <a href="/trust" className="transition-colors hover:text-foreground/80 text-foreground/60">Trust</a>
              <a href="/about" className="transition-colors hover:text-foreground/80 text-foreground/60">About</a>
            </nav>
          </div>
          <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
            <nav className="flex items-center">
              <a href="/dashboard" className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-4 py-2">
                Login
              </a>
            </nav>
          </div>
        </div>
      </header>
      <main className="flex-1">
        {children}
      </main>
      <footer className="py-6 md:px-8 md:py-0 border-t">
        <div className="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row">
          <p className="text-balance text-center text-sm leading-loose text-muted-foreground md:text-left">
            Built by TSM99.
          </p>
        </div>
      </footer>
    </div>
  );
}
