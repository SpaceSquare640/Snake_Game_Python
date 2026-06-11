/* App version and the GitHub release update check. */

export const APP_VERSION = "1.5.1";
export const GITHUB_REPO = "SpaceSquare640/Snake_Game_Python";

// Parse "v1.2.0" into a zero-padded, lexically-comparable string.
export function parseVersion(text) {
  const parts = String(text).trim().replace(/^v/i, "").split(".").map((c) => {
    const m = c.match(/^\d+/);
    return m ? parseInt(m[0], 10) : 0;
  });
  return parts.map((n) => String(n).padStart(5, "0")).join(".");
}

// Resolve to the latest release tag (or "" on any failure).
export function fetchLatestTag() {
  return fetch("https://api.github.com/repos/" + GITHUB_REPO + "/releases/latest", {
    headers: { "Accept": "application/vnd.github+json" },
  })
    .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
    .then((data) => (data && data.tag_name) || "");
}
