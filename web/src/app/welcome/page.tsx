import Link from "next/link";

// the initial page the user sees
export default function WelcomePage() {
  return (
    <div className="min-h-full bg-zinc-50 px-4 pt-[20vh] pb-10 dark:bg-zinc-950 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        <header className="mb-8 text-center sm:text-left">
          <p className="mb-2 text-sm font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
            SiteLens
          </p>
          <h1 className="text-5xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Welcome to SiteLens
          </h1>
          <p className="mt-2 max-w-xl text-base text-zinc-600 dark:text-zinc-400">
            SiteLens helps you compare event venues — built for developer and hackathon 
            organizers who need clear, side-by-side venue decisions.
          </p>
        </header>

        <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <section className="px-6 py-6 sm:px-8">
            <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Get started
            </h2>
            <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
              Add your event details and venue candidates to generate map signals,
              nearby places, and a Box checklist — all in one comparison view.
            </p>
          </section>

        {/* redirects to compare page */}
          <div className="border-t border-zinc-100 bg-zinc-50/50 px-6 py-5 dark:border-zinc-800 dark:bg-zinc-950/30 sm:px-8">
            <Link
              href="/compare"
              className="inline-flex w-full items-center justify-center rounded-lg bg-emerald-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-zinc-900 sm:w-auto sm:min-w-[220px]"
            >
              Start comparing venues
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
