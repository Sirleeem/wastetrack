/* WasteTrack PWA helpers: install prompt + push notification opt-in. */
(function () {
  "use strict";

  var DISMISS_KEY = "wt-pwa-dismiss";
  var DISMISS_DAYS = 7;

  function dismissed(kind) {
    try {
      var raw = localStorage.getItem(DISMISS_KEY + ":" + kind);
      if (!raw) return false;
      return Date.now() - parseInt(raw, 10) < DISMISS_DAYS * 864e5;
    } catch (e) {
      return false;
    }
  }

  function dismiss(kind) {
    try {
      localStorage.setItem(DISMISS_KEY + ":" + kind, String(Date.now()));
    } catch (e) { /* ignore */ }
    hideBanner();
  }

  var banner, bannerTitle, bannerSub, bannerAction, bannerDismiss;
  var bannerKind = null;

  function hideBanner() {
    if (banner) banner.hidden = true;
    bannerKind = null;
  }

  function showBanner(kind, title, sub, actionLabel, onAction) {
    if (!banner || bannerKind) return;
    bannerKind = kind;
    bannerTitle.textContent = title;
    bannerSub.textContent = sub || "";
    if (actionLabel) {
      bannerAction.hidden = false;
      bannerAction.textContent = actionLabel;
      bannerAction.onclick = onAction;
    } else {
      bannerAction.hidden = true;
    }
    bannerDismiss.onclick = function () { dismiss(kind); };
    banner.hidden = false;
  }

  function urlBase64ToUint8Array(base64String) {
    var padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    var base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    var raw = window.atob(base64);
    var out = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
    return out;
  }

  function csrfToken() {
    var el = document.querySelector('meta[name="csrf-token"]');
    return el ? el.getAttribute("content") : "";
  }

  document.addEventListener("DOMContentLoaded", function () {
    banner = document.getElementById("pwa-banner");
    if (!banner) return;
    bannerTitle = document.getElementById("pwa-banner-title");
    bannerSub = document.getElementById("pwa-banner-sub");
    bannerAction = document.getElementById("pwa-banner-action");
    bannerDismiss = document.getElementById("pwa-banner-dismiss");

    var isStandalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true;
    var isIOS = /iphone|ipad|ipod/i.test(window.navigator.userAgent);
    var deferredPrompt = null;

    /* ---- Install prompt (Chromium / Android) ---- */
    window.addEventListener("beforeinstallprompt", function (e) {
      e.preventDefault();
      deferredPrompt = e;
      if (!isStandalone && !dismissed("install")) {
        showBanner(
          "install",
          "Install WasteTrack",
          "Add it to your home screen for quick access, even offline.",
          "Install",
          function () {
            if (!deferredPrompt) return;
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then(function () {
              deferredPrompt = null;
              dismiss("install");
            });
          }
        );
      }
    });

    /* ---- Install hint (iOS Safari has no beforeinstallprompt) ---- */
    window.addEventListener("load", function () {
      setTimeout(function () {
        if (isIOS && !isStandalone && !dismissed("install") && !bannerKind) {
          showBanner(
            "install",
            "Install WasteTrack",
            'Tap Share, then "Add to Home Screen".',
            null
          );
        }
      }, 2000);
    });

    /* ---- Push notification opt-in (logged-in users) ---- */
    var authed = document.body.getAttribute("data-authenticated") === "1";
    if (
      authed &&
      "serviceWorker" in navigator &&
      "PushManager" in window &&
      "Notification" in window
    ) {
      navigator.serviceWorker.ready.then(function (reg) {
        return reg.pushManager.getSubscription();
      }).then(function (sub) {
        if (sub || Notification.permission === "denied") return;
        if (dismissed("push") || bannerKind) return;
        showBanner(
          "push",
          "Stay updated",
          "Get notified on this device when tasks are assigned to you.",
          "Enable",
          function () {
            Notification.requestPermission().then(function (perm) {
              if (perm !== "granted") {
                dismiss("push");
                return;
              }
              subscribePush();
            });
          }
        );
      }).catch(function () { /* push unsupported here */ });
    }

    function subscribePush() {
      fetch("/push/vapid-key")
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.publicKey) throw new Error("push not configured");
          return navigator.serviceWorker.ready.then(function (reg) {
            return reg.pushManager.subscribe({
              userVisibleOnly: true,
              applicationServerKey: urlBase64ToUint8Array(d.publicKey),
            });
          });
        })
        .then(function (sub) {
          return fetch("/push/subscribe", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken(),
            },
            body: JSON.stringify(sub.toJSON()),
          });
        })
        .then(function () { dismiss("push"); })
        .catch(function () { dismiss("push"); });
    }
  });
})();
