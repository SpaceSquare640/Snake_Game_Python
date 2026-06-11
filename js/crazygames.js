/* A defensive wrapper around the CrazyGames JS SDK (v3).
 *
 * The same build runs on crazygames.com, on GitHub Pages, and from a local
 * file server — so every call here degrades to a harmless no-op when the SDK
 * is absent or we are not actually running inside the CrazyGames portal. Only
 * when `environment === "crazygames"` do real ads ever get requested; that
 * keeps test-ad overlays off GitHub Pages while still wiring the full lifecycle.
 *
 * The SDK itself is loaded by a plain <script> tag in index.html, which exposes
 * window.CrazyGames.SDK before our module boots.
 */

class CrazyGamesAdapter {
  constructor() {
    this.sdk = null;
    this.ready = false;
    this.environment = "disabled"; // "crazygames" | "local" | "disabled"
    this.adInProgress = false;
    this.lastAdTs = 0;
    this.minAdIntervalMs = 70 * 1000; // CrazyGames asks for a gap between ads
    this.muted = false;               // mirrors the portal's mute-audio setting
    this._muteHandlers = [];
  }

  // True only inside the real portal, where requesting ads is appropriate.
  get adsEnabled() {
    return this.ready && this.environment === "crazygames";
  }

  async init() {
    const sdk = window.CrazyGames && window.CrazyGames.SDK;
    if (!sdk) return;
    this.sdk = sdk;
    try {
      await sdk.init();
      this.ready = true;
      this.environment = sdk.environment || "local";
      this._initMute();
    } catch (e) {
      this.ready = false;
    }
  }

  // -- Mute (the portal's audio toggle) ---------------------------------
  // CrazyGames exposes the player's mute preference via game.settings and
  // notifies us when it changes. We mirror it and fan out to listeners so the
  // game can silence its WebAudio output (which the portal can't mute for us).
  _initMute() {
    try {
      this.muted = !!(this.sdk.game.settings && this.sdk.game.settings.muteAudio);
      this.sdk.game.addSettingsChangeListener(() => {
        const m = !!(this.sdk.game.settings && this.sdk.game.settings.muteAudio);
        if (m === this.muted) return;
        this.muted = m;
        this._muteHandlers.forEach((h) => { try { h(m); } catch (e) { /* */ } });
      });
    } catch (e) { /* older SDK shape — leave unmuted */ }
  }

  // Register a mute-state listener; fires immediately with the current state.
  onMuteChange(fn) {
    this._muteHandlers.push(fn);
    try { fn(this.muted); } catch (e) { /* */ }
  }

  // -- Loading lifecycle (tells the portal when our assets are ready) ----
  loadingStart() { this._safe(() => this.sdk.game.sdkGameLoadingStart()); }
  loadingStop() { this._safe(() => this.sdk.game.sdkGameLoadingStop()); }

  // -- Gameplay lifecycle (drives the portal's own pause/ad logic) -------
  gameplayStart() { this._safe(() => this.sdk.game.gameplayStart()); }
  gameplayStop() { this._safe(() => this.sdk.game.gameplayStop()); }

  // Signal a natural "good moment" for an interstitial (level cleared, etc.).
  happytime() { if (this.adsEnabled) this._safe(() => this.sdk.game.happytime()); }

  // -- Ads ----------------------------------------------------------------
  /* Request a midgame (interstitial) ad. Resolves to true if an ad actually
     played, false otherwise. Always resolves — callers must not block on it.
     `onStart` is the moment to pause + mute; `onResume` fires when control
     returns to the game whether or not an ad was shown. */
  requestMidgame({ onStart, onResume } = {}) {
    return new Promise((resolve) => {
      const now = Date.now();
      if (!this.adsEnabled || this.adInProgress ||
          now - this.lastAdTs < this.minAdIntervalMs) {
        resolve(false);
        return;
      }
      this.adInProgress = true;
      let started = false;
      const finish = (shown) => {
        this.adInProgress = false;
        if (shown) this.lastAdTs = Date.now();
        if (onResume) onResume(started);
        resolve(shown);
      };
      try {
        this.sdk.ad.requestAd("midgame", {
          adStarted: () => { started = true; if (onStart) onStart(); },
          adFinished: () => finish(true),
          adError: () => finish(false),
        });
      } catch (e) { finish(false); }
    });
  }

  _safe(fn) {
    if (!this.sdk) return;
    try { fn(); } catch (e) { /* SDK shape changed or unavailable */ }
  }
}

export const CG = new CrazyGamesAdapter();
