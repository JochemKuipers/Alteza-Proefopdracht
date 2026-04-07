const { useState, useEffect, useCallback } = React;

function stripQueryParam(qs, key) {
  const re = new RegExp(`([?&])${key}=[^&]*`, "g");
  let out = (qs || "").replace(re, "$1").replace(/[?&]$/, "");
  out = out.replace(/[?&]{2,}/g, "&").replace("?&", "?");
  if (out === "?") return "";
  return out;
}

function formatWhen(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
      hour12: false,
    });
  } catch (e) {
    return String(iso);
  }
}

function CommitItem({ c, groupedMode }) {
  const sha = c.sha7 || (c.sha || "").slice(0, 7) || "";
  const when = formatWhen(c.date);
  const metaBits = [sha, when].filter(Boolean).join(" · ");
  const author = c.author || "Unknown";
  const hasMsg = !!c.message;

  if (groupedMode) {
    return (
      <li className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs text-slate-500 dark:text-slate-400">{metaBits}</p>
        </div>
        <p
          className="mt-1 text-xs text-slate-700 line-clamp-2 dark:text-slate-300"
          title={hasMsg ? c.message : undefined}
        >
          {c.message || ""}
        </p>
      </li>
    );
  }

  return (
    <li className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">{author}</p>
        <p className="text-xs text-slate-500 dark:text-slate-400">{metaBits}</p>
      </div>
      <p
        className="mt-1 text-xs text-slate-700 line-clamp-2 dark:text-slate-300"
        title={hasMsg ? c.message : undefined}
      >
        {c.message || ""}
      </p>
    </li>
  );
}

function AuthorGroup({ g }) {
  const n = typeof g.count === "number" ? g.count : 0;
  const latest = g.latest
    ? {
        message: g.latest.message,
        date: g.latest.date,
        sha7: g.latest.sha7 || (g.latest.sha || "").slice(0, 7),
      }
    : null;
  const recent = Array.isArray(g.recent) ? g.recent : [];

  const latestLine = latest
    ? `Latest: ${latest.sha7 || ""}${latest.date ? " · " + formatWhen(latest.date) : ""} — ${latest.message || ""}`
    : "";

  return (
    <li className="list-none">
      <details className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <summary className="cursor-pointer list-none outline-none marker:content-none [&::-webkit-details-marker]:hidden">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                {g.author || "Unknown"}
              </p>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                {n} commit{n === 1 ? "" : "s"}
              </p>
              {latestLine ? (
                <p className="mt-1 text-xs text-slate-600 commit-clamp-2 dark:text-slate-300">
                  {latestLine}
                </p>
              ) : null}
              <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                Show recent commits from scan
              </p>
            </div>
          </div>
        </summary>
        <div className="mt-3 border-t border-slate-100 pt-3 dark:border-slate-700">
          <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
            Recent commits (from scan)
          </p>
          {recent.length > 0 ? (
            <ul className="mt-2 space-y-2 border-l-2 border-slate-200 pl-3 dark:border-slate-600">
              {recent.map((c, i) => (
                <CommitItem key={i} c={c} groupedMode />
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
              No recent commits in this scan.
            </p>
          )}
        </div>
      </details>
    </li>
  );
}

function CommitResults({ apiUrl }) {
  const PER_PAGE_KEY = "commitResultsPerPage";

  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(() => {
    const stored = sessionStorage.getItem(PER_PAGE_KEY);
    if (stored && ["10", "25", "50"].includes(stored)) {
      return parseInt(stored, 10);
    }
    return 25;
  });
  const [loading, setLoading] = useState(false);
  const [count, setCount] = useState(null);
  const [groupedMode, setGroupedMode] = useState(false);
  const [results, setResults] = useState([]);
  const [status, setStatus] = useState("");
  const [metaText, setMetaText] = useState("Loading…");
  const [hasPrev, setHasPrev] = useState(false);
  const [hasNext, setHasNext] = useState(false);

  const totalPages = useCallback(() => {
    if (typeof count !== "number" || count < 0) return null;
    return Math.max(1, Math.ceil(count / perPage));
  }, [count, perPage]);

  const loadPage = useCallback(
    async (pageNum) => {
      setLoading(true);
      setStatus("Loading…");
      setHasPrev(false);
      setHasNext(false);

      let qs = window.location.search || "";
      qs = stripQueryParam(stripQueryParam(qs, "page"), "per_page");
      const joiner = qs.includes("?") ? "&" : "?";
      const url = `${apiUrl}${qs}${joiner}page=${pageNum}&per_page=${perPage}`;

      try {
        const resp = await fetch(url, {
          headers: { Accept: "application/json" },
        });
        const data = await resp.json();
        if (!resp.ok) {
          throw new Error(
            data && data.detail
              ? data.detail
              : `Request failed (${resp.status})`,
          );
        }

        const p = data.page || pageNum;
        const pp = data.per_page || perPage;
        setPage(p);
        setPerPage(pp);
        setCount(typeof data.count === "number" ? data.count : null);
        setGroupedMode(!!data.grouped);
        setResults(Array.isArray(data.results) ? data.results : []);
        setHasPrev(!!data.previous);
        setHasNext(!!data.next);

        const tp = (() => {
          const c = typeof data.count === "number" ? data.count : null;
          if (c == null || c < 0) return null;
          return Math.max(1, Math.ceil(c / pp));
        })();

        const label = data.grouped ? "authors" : "commits";
        if (data.grouped) {
          if (tp != null && typeof data.count === "number") {
            setMetaText(
              `Authors — page ${p} of ${tp} (${data.count} ${label})`,
            );
          } else {
            setMetaText(`Authors — page ${p}`);
          }
        } else {
          if (tp != null && typeof data.count === "number") {
            setMetaText(`Page ${p} of ${tp} (${data.count} ${label})`);
          } else {
            setMetaText(`Page ${p} · total not available for this filter`);
          }
        }

        const itemsLen = (data.results || []).length;
        setStatus(
          itemsLen
            ? ""
            : data.grouped
              ? "No authors on this page."
              : "No commits on this page.",
        );
      } catch (e) {
        setStatus(e && e.message ? e.message : "Failed to load commits.");
        setResults([]);
        setMetaText("Failed to load results.");
        setHasPrev(false);
        setHasNext(false);
      } finally {
        setLoading(false);
      }
    },
    [apiUrl, perPage],
  );

  useEffect(() => {
    loadPage(page);
  }, [page, perPage, loadPage]);

  const onPerPageChange = (e) => {
    const v = parseInt(e.target.value, 10) || 25;
    sessionStorage.setItem(PER_PAGE_KEY, String(v));
    setPerPage(v);
    setPage(1);
  };

  const tp = totalPages();
  const firstDisabled = page <= 1;
  const lastDisabled = tp == null ? true : page >= tp;
  const prevDisabled = !hasPrev;
  const nextDisabled = !hasNext;

  return (
    <>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Results</h2>
          <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">{metaText}</p>
        </div>
      </div>
      <div id="commit-results-scroll" className="commit-scroll mt-4">
        <ul className="space-y-2">
          {groupedMode
            ? results.map((g, i) => <AuthorGroup key={i} g={g} />)
            : results.map((c, i) => (
                <CommitItem key={i} c={c} groupedMode={false} />
              ))}
        </ul>
      </div>
      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <label
            htmlFor="commit-per-page"
            className="text-xs font-medium text-slate-600 dark:text-slate-400"
          >
            Per page
          </label>
          <select
            id="commit-per-page"
            className="form-control max-w-[5.5rem] py-1.5 text-sm"
            value={String(perPage)}
            onChange={onPerPageChange}
          >
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
          </select>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="btn-secondary"
            disabled={firstDisabled || loading}
            onClick={() => setPage(1)}
          >
            First
          </button>
          <button
            type="button"
            className="btn-secondary"
            disabled={prevDisabled || loading}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </button>
          <button
            type="button"
            className="btn-secondary"
            disabled={nextDisabled || loading}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
          <button
            type="button"
            className="btn-secondary"
            disabled={lastDisabled || loading}
            onClick={() => {
              const t = totalPages();
              if (t != null) setPage(t);
            }}
          >
            Last
          </button>
          <span className="text-xs text-slate-500 dark:text-slate-400">{status}</span>
        </div>
      </div>
    </>
  );
}

const rootEl = document.getElementById("commit-results-root");
if (rootEl && window.ReactDOM && window.React) {
  const { createRoot } = ReactDOM;
  const apiUrl = rootEl.dataset.apiUrl || "";
  createRoot(rootEl).render(<CommitResults apiUrl={apiUrl} />);
}
