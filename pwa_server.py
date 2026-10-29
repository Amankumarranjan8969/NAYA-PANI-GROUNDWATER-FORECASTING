"""pwa_server.py — Starlette/Tornado Root-Scope PWA Route Injector & Multi-Platform Installer for Naya Pani.

Injects root-level routes ('/manifest.json', '/nayapani_manifest.json', '/service_worker.js',
'/icon-192.png', '/icon-512.png') directly into Streamlit's running Starlette ASGI router
at index 0 so they take priority over Streamlit's catch-all static file handler.
"""

from __future__ import annotations

import base64
import gc
from pathlib import Path

import streamlit as st

_STATIC_DIR = Path(__file__).resolve().parent / "static"


def get_brand_logo_base64(size: int = 192) -> str:
    """Return Base64 data URI for the Naya Pani PNG brand icon."""
    icon_path = _STATIC_DIR / f"icon-{size}.png"
    if not icon_path.exists():
        icon_path = _STATIC_DIR / "icon-192.png"
    if icon_path.exists():
        b64 = base64.b64encode(icon_path.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    return ""


def _mount_starlette_pwa_routes() -> bool:
    """Prepend PWA routes to Streamlit's active Starlette router so root URLs serve PWA assets."""
    try:
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import Response
        from starlette.routing import Route

        async def serve_manifest(request: Request) -> Response:
            manifest_path = _STATIC_DIR / "manifest.json"
            content = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else "{}"
            return Response(
                content=content,
                media_type="application/manifest+json; charset=utf-8",
                headers={"Cache-Control": "no-cache"},
            )

        async def serve_service_worker(request: Request) -> Response:
            sw_path = _STATIC_DIR / "service_worker.js"
            content = sw_path.read_text(encoding="utf-8") if sw_path.exists() else "// missing sw"
            return Response(
                content=content,
                media_type="application/javascript; charset=utf-8",
                headers={
                    "Service-Worker-Allowed": "/",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                },
            )

        async def serve_icon_192(request: Request) -> Response:
            p = _STATIC_DIR / "nayapani-icon-192.png"
            if not p.exists():
                p = _STATIC_DIR / "icon-192.png"
            data = p.read_bytes() if p.exists() else b""
            return Response(
                content=data,
                media_type="image/png",
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )

        async def serve_icon_512(request: Request) -> Response:
            p = _STATIC_DIR / "nayapani-icon-512.png"
            if not p.exists():
                p = _STATIC_DIR / "icon-512.png"
            data = p.read_bytes() if p.exists() else b""
            return Response(
                content=data,
                media_type="image/png",
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )

        async def serve_favicon_ico(request: Request) -> Response:
            p = _STATIC_DIR / "favicon.ico"
            data = p.read_bytes() if p.exists() else b""
            return Response(
                content=data,
                media_type="image/x-icon",
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )

        mounted_any = False
        for obj in gc.get_objects():
            if isinstance(obj, Starlette):
                if not getattr(obj, "_nayapani_starlette_pwa_v4", False):
                    pwa_routes = [
                        Route("/nayapani_manifest.json", endpoint=serve_manifest, methods=["GET", "HEAD"]),
                        Route("/manifest.json", endpoint=serve_manifest, methods=["GET", "HEAD"]),
                        Route("/app/static/manifest.json", endpoint=serve_manifest, methods=["GET", "HEAD"]),
                        Route("/service_worker.js", endpoint=serve_service_worker, methods=["GET", "HEAD"]),
                        Route("/app/static/service_worker.js", endpoint=serve_service_worker, methods=["GET", "HEAD"]),
                        Route("/nayapani-icon-192.png", endpoint=serve_icon_192, methods=["GET", "HEAD"]),
                        Route("/icon-192.png", endpoint=serve_icon_192, methods=["GET", "HEAD"]),
                        Route("/app/static/icon-192.png", endpoint=serve_icon_192, methods=["GET", "HEAD"]),
                        Route("/nayapani-icon-512.png", endpoint=serve_icon_512, methods=["GET", "HEAD"]),
                        Route("/icon-512.png", endpoint=serve_icon_512, methods=["GET", "HEAD"]),
                        Route("/app/static/icon-512.png", endpoint=serve_icon_512, methods=["GET", "HEAD"]),
                        Route("/favicon.png", endpoint=serve_icon_192, methods=["GET", "HEAD"]),
                        Route("/favicon.ico", endpoint=serve_favicon_ico, methods=["GET", "HEAD"]),
                    ]
                    obj.router.routes[:0] = pwa_routes
                    setattr(obj, "_nayapani_starlette_pwa_v4", True)
                mounted_any = True
        return mounted_any
    except Exception:
        return False


def ensure_pwa_root_routes() -> bool:
    """Mount PWA root routes on Starlette (Streamlit 1.44+) and Tornado fallback."""
    return _mount_starlette_pwa_routes()


def inject_pwa_head_and_sidebar_installer() -> None:
    """Mount root Starlette PWA routes, configure Streamlit logo, and initialize parent PWA listeners."""
    ensure_pwa_root_routes()

    icon_192 = _STATIC_DIR / "nayapani-icon-192.png"
    if not icon_192.exists():
        icon_192 = _STATIC_DIR / "icon-192.png"
    if icon_192.exists() and hasattr(st, "logo"):
        try:
            st.logo(str(icon_192))
        except Exception:
            pass

    logo_b64 = get_brand_logo_base64(192)

    st.components.v1.html(
        f"""
        <script>
        (function() {{
          try {{
            const pWin = window.parent;
            const doc = pWin.document;
            const head = doc.head;

            // 1. Point <link rel="manifest"> to our cache-busted root Naya Pani manifest
            let manifestLink = head.querySelector('link[rel="manifest"]');
            if (!manifestLink) {{
              manifestLink = doc.createElement('link');
              manifestLink.rel = 'manifest';
              head.appendChild(manifestLink);
            }}
            if (!manifestLink.href.includes('nayapani_manifest.json?v=4')) {{
              manifestLink.href = '/nayapani_manifest.json?v=4';
            }}

            // 2. Ensure theme-color, apple-mobile-web-app-capable, and icons exist
            const metaDefs = [
              ['theme-color', '#0071E3'],
              ['apple-mobile-web-app-capable', 'yes'],
              ['apple-mobile-web-app-status-bar-style', 'default'],
              ['apple-mobile-web-app-title', 'NayaPani'],
              ['mobile-web-app-capable', 'yes']
            ];
            metaDefs.forEach(function(pair) {{
              let m = head.querySelector('meta[name="' + pair[0] + '"]');
              if (!m) {{
                m = doc.createElement('meta');
                m.name = pair[0];
                head.appendChild(m);
              }}
              m.content = pair[1];
            }});

            // Override ALL icon / shortcut icon links so browser tab & Windows taskbar use the new Naya-Pani logo
            function enforceFavicon() {{
              const iconLinks = head.querySelectorAll('link[rel*="icon"]');
              if (iconLinks.length === 0) {{
                const l = doc.createElement('link');
                l.rel = 'shortcut icon';
                l.type = 'image/png';
                l.href = '/nayapani-icon-192.png?v=4';
                head.appendChild(l);
              }} else {{
                iconLinks.forEach(function(l) {{
                  if (!l.href.includes('nayapani-icon-192.png?v=4') && !l.href.startsWith('data:image/png')) {{
                    l.type = 'image/png';
                    l.href = '/nayapani-icon-192.png?v=4';
                  }}
                }});
              }}
            }}
            enforceFavicon();

            let appleIcon = head.querySelector('link[rel="apple-touch-icon"]');
            if (!appleIcon) {{
              appleIcon = doc.createElement('link');
              appleIcon.rel = 'apple-touch-icon';
              head.appendChild(appleIcon);
            }}
            appleIcon.href = '/nayapani-icon-192.png?v=4';

            // Purge any legacy Service Worker caches so old icons are never served
            if ('caches' in pWin) {{
              pWin.caches.keys().then(function(keys) {{
                keys.forEach(function(k) {{
                  if (k !== 'naya-pani-pwa-v4') {{
                    pWin.caches.delete(k);
                  }}
                }});
              }}).catch(function() {{}});
            }}

            // 3. Single idempotent global listener registration on window.parent
            if (!pWin.__nayaPaniPwaInitialized) {{
              pWin.__nayaPaniPwaInitialized = true;
              pWin.__nayaPaniInstalled = false;

              pWin.addEventListener('beforeinstallprompt', function(e) {{
                e.preventDefault();
                pWin.__nayaPaniDeferredPrompt = e;
                pWin.dispatchEvent(new CustomEvent('nayapani:pwa-state-change'));
              }});

              pWin.addEventListener('appinstalled', function() {{
                pWin.__nayaPaniInstalled = true;
                pWin.__nayaPaniDeferredPrompt = null;
                pWin.dispatchEvent(new CustomEvent('nayapani:pwa-state-change'));
              }});
            }}

            // 4. Register & force-update single Root-Scope Service Worker ('/service_worker.js?v=4')
            if ('serviceWorker' in pWin.navigator) {{
              pWin.navigator.serviceWorker.register('/service_worker.js?v=4', {{ scope: '/' }})
                .then(function(reg) {{
                  reg.update();
                  pWin.__nayaPaniSwReady = true;
                  pWin.dispatchEvent(new CustomEvent('nayapani:pwa-state-change'));
                }})
                .catch(function(err) {{
                  pWin.__nayaPaniSwError = String(err);
                }});
            }}
          }} catch (err) {{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def render_sidebar_pwa_button() -> None:
    """Render the responsive, accessible '📲 Install Naya Pani' PWA component in the sidebar."""
    logo_b64 = get_brand_logo_base64(192)
    st.components.v1.html(
        f"""
        <style>
          * {{ box-sizing: border-box; }}
          body {{ margin: 0; padding: 0; background: transparent; font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
          .np-pwa-card {{
            background: #FFFFFF;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 14px;
            padding: 10px 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
          }}
          .np-brand-row {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
          }}
          .np-logo {{
            width: 44px;
            height: 44px;
            border-radius: 10px;
            object-fit: contain;
            flex-shrink: 0;
            box-shadow: 0 2px 8px rgba(0, 113, 227, 0.18);
          }}
          .np-title {{
            font-weight: 800;
            font-size: 13.5px;
            color: #1D1D1F;
            letter-spacing: -0.02em;
            line-height: 1.2;
          }}
          .np-sub {{
            font-size: 11px;
            color: #6E6E73;
            font-weight: 500;
            margin-top: 2px;
          }}
          .np-install-btn {{
            width: 100%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 9px 14px;
            border-radius: 10px;
            border: 1px solid #0071E3;
            background: #0071E3;
            color: #FFFFFF;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: background 0.16s ease, transform 0.1s ease;
            outline: none;
          }}
          .np-install-btn:hover:not(:disabled) {{
            background: #0058B0;
          }}
          .np-install-btn:focus-visible {{
            box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.35);
          }}
          .np-install-btn:disabled {{
            cursor: default;
            opacity: 0.95;
          }}
          .np-install-btn.installed {{
            background: #E8F8EE;
            color: #1E7E34;
            border-color: #A3E4B7;
          }}
          .np-hint {{
            display: none;
            margin-top: 8px;
            padding: 8px 10px;
            border-radius: 8px;
            background: #F5F5F7;
            color: #1D1D1F;
            font-size: 11.5px;
            line-height: 1.45;
            border: 1px solid rgba(0, 0, 0, 0.08);
          }}
        </style>
        <div class="np-pwa-card" role="region" aria-label="Naya Pani App Installation">
          <div class="np-brand-row">
            <img src="{logo_b64}" alt="Naya Pani Logo" class="np-logo" />
            <div>
              <div class="np-title">NAYA-PANI</div>
              <div class="np-sub">Groundwater AI · PWA</div>
            </div>
          </div>
          <button
            type="button"
            id="nayapani-pwa-install-btn"
            class="np-install-btn"
            aria-label="Install Naya Pani"
          >📲 Install Naya Pani</button>
          <div id="nayapani-pwa-msg" class="np-hint" role="status" aria-live="polite"></div>
        </div>

        <script>
        (function() {{
          const btn = document.getElementById('nayapani-pwa-install-btn');
          const msg = document.getElementById('nayapani-pwa-msg');
          const pWin = window.parent;
          const ua = pWin.navigator.userAgent || '';

          const isIOS = /iPad|iPhone|iPod/.test(ua) || (pWin.navigator.platform === 'MacIntel' && pWin.navigator.maxTouchPoints > 1);
          const isAndroid = /Android/i.test(ua);
          const isFirefox = /Firefox/i.test(ua);
          const isSafariDesktop = /^((?!chrome|android).)*safari/i.test(ua) && !isIOS;

          function checkIsStandalone() {{
            return Boolean(
              pWin.__nayaPaniInstalled ||
              pWin.matchMedia('(display-mode: standalone)').matches ||
              pWin.matchMedia('(display-mode: window-controls-overlay)').matches ||
              pWin.navigator.standalone === true
            );
          }}

          function syncUI() {{
            if (checkIsStandalone()) {{
              btn.textContent = '✓ Naya Pani Installed';
              btn.classList.add('installed');
              btn.disabled = true;
              btn.setAttribute('aria-disabled', 'true');
              msg.style.display = 'none';
              return;
            }}

            btn.classList.remove('installed');
            btn.disabled = false;
            btn.removeAttribute('aria-disabled');
            btn.textContent = '📲 Install Naya Pani';

            if (isIOS) {{
              msg.style.display = 'block';
              msg.textContent = 'To install: Tap Share → Add to Home Screen.';
            }}
          }}

          async function triggerInstall() {{
            if (checkIsStandalone()) {{
              syncUI();
              return;
            }}

            const deferredPrompt = pWin.__nayaPaniDeferredPrompt;
            if (deferredPrompt) {{
              try {{
                btn.disabled = true;
                await deferredPrompt.prompt();
                const choiceResult = await deferredPrompt.userChoice;
                if (choiceResult && choiceResult.outcome === 'accepted') {{
                  pWin.__nayaPaniDeferredPrompt = null;
                  msg.style.display = 'block';
                  msg.textContent = 'Completing installation…';
                }} else {{
                  btn.disabled = false;
                  msg.style.display = 'block';
                  msg.textContent = 'Installation cancelled. Click "📲 Install Naya Pani" whenever you are ready.';
                }}
              }} catch (err) {{
                btn.disabled = false;
                msg.style.display = 'block';
                msg.textContent = 'Installation error: ' + (err.message || 'Could not trigger prompt.');
              }}
              return;
            }}

            // Platform-appropriate message when beforeinstallprompt is not supported or not yet fired
            msg.style.display = 'block';
            if (isIOS) {{
              msg.textContent = 'To install: Tap Share → Add to Home Screen.';
            }} else if (isAndroid) {{
              msg.textContent = 'To install on Android: Tap browser menu (⋮) → Install app (or Add to Home screen).';
            }} else if (isFirefox) {{
              msg.textContent = 'Firefox Desktop does not support direct PWA installation. Open Naya Pani in Chrome or Edge to install.';
            }} else if (isSafariDesktop) {{
              msg.textContent = 'To install on macOS Safari: Choose File → Add to Dock.';
            }} else {{
              msg.textContent = 'Reload the page once so the Service Worker activates, then click "📲 Install Naya Pani" to open the install dialog.';
            }}
          }}

          btn.addEventListener('click', triggerInstall);
          pWin.__nayaPaniTriggerInstall = triggerInstall;

          pWin.addEventListener('nayapani:pwa-state-change', syncUI);
          try {{
            pWin.matchMedia('(display-mode: standalone)').addEventListener('change', syncUI);
          }} catch (e) {{}}

          syncUI();
        }})();
        </script>
        """,
        height=158,
    )
