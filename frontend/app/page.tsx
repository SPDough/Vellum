import HomePage from '@/components/pages/HomePage';

/**
 * Canonical root entry for the Next.js App Router frontend.
 *
 * Phase 1 refresh: present a search-first homepage instead of redirecting
 * directly to the dashboard.
 */
export default function Page() {
  return <HomePage />;
}
