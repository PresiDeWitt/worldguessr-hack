import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class WorldGuessrGod:
    def __init__(self):
        print("\n" + "=" * 50)
        print(" SABUESO ACTIVADO")
        print("=" * 50 + "\n")

        options = Options()
        options.add_argument("--start-maximized")

        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), options=options
            )
        except Exception as e:
            print(f"Error fatal iniciando Chrome: {e}")
            exit()

        self.last_coords = None

    def inject_interceptors(self):
        """
        Intercepta fetch buscando llamadas a api.worldguessr.com/api/country
        que contienen lat= y lon= directamente en la URL.
        """
        js = r"""
        (function() {
            if (window.__hack_injected) return;
            window.__hack_injected = true;
            window.__hack_coords   = null;  // {lat, lng} mas reciente

            var _fetch = window.fetch;
            window.fetch = async function() {
                var url = '';
                try {
                    url = (arguments[0] && arguments[0].url) ? arguments[0].url : String(arguments[0]);
                } catch(_) {}

                // Intercept response to check for JSON coordinates
                var call = _fetch.apply(this, arguments);

                call.then(function(response) {
                    try {
                        var clone = response.clone();
                        clone.json().then(function(data) {
                            // Recursively search for "lat" and "lng"/"lon" in the object
                            var findCoords = function(obj) {
                                if (!obj || typeof obj !== 'object') return;
                                if (obj.lat && (obj.lng || obj.lon)) {
                                    var lat = parseFloat(obj.lat);
                                    var lng = parseFloat(obj.lng || obj.lon);
                                    if (!isNaN(lat) && !isNaN(lng)) {
                                        window.__hack_coords = { lat: lat, lng: lng };
                                        console.log("[HACK] Coords found in API response:", window.__hack_coords);
                                    }
                                }
                                for (var k in obj) findCoords(obj[k]);
                            };
                            findCoords(data);
                        }).catch(function(){});
                    } catch(e) {}
                });

                return call;
            };

            // HACK: WebSocket Interceptor (for Multiplayer/Community)
            // Hooks WebSocket creation and listens for 'message' events
            var _WebSocket = window.WebSocket;
            window.WebSocket = function(url, protocols) {
                var ws = new _WebSocket(url, protocols);

                ws.addEventListener('message', function(event) {
                    try {
                        var data = JSON.parse(event.data);
                        // Recursive scan
                        var findCoords = function(obj) {
                            if (!obj || typeof obj !== 'object') return;
                            if (obj.lat && (obj.lng || obj.lon)) {
                                var lat = parseFloat(obj.lat);
                                var lng = parseFloat(obj.lng || obj.lon);
                                if (!isNaN(lat) && !isNaN(lng)) {
                                    window.__hack_coords = { lat: lat, lng: lng };
                                    console.log("[HACK] WebSocket Coords:", window.__hack_coords);
                                }
                            }
                            for (var k in obj) findCoords(obj[k]);
                        };
                        findCoords(data);
                    } catch(e) {}
                });

                return ws;
            };

            // HACK: Leaflet Map Instance Hook (God Mode)
            // Continuously checks for Leaflet 'L' global and hooks initialize
            function hookLeaflet() {
                var attempt = 0;
                var interval = setInterval(function() {
                    attempt++;
                    if (window.L && window.L.Map && window.L.Map.prototype && window.L.Map.prototype.initialize) {
                        clearInterval(interval);
                        console.log("[HACK] Leaflet found on attempt " + attempt + "! Hooking Map.initialize...");

                        var originalInit = window.L.Map.prototype.initialize;
                        window.L.Map.prototype.initialize = function() {
                            window.__hack_map_instance = this; // CAPTURE THE INSTANCE
                            console.log("[HACK] Map instance CAPTURED via hook!");
                            return originalInit.apply(this, arguments);
                        };

                        // Also try to hook existing maps if we were late
                        if (!window.__hack_map_instance) {
                             var container = document.querySelector('.leaflet-container');
                             if (container && container._leaflet_map) window.__hack_map_instance = container._leaflet_map;
                        }
                    }
                    if (attempt > 1000) clearInterval(interval); // Stop after 10s
                }, 10);
            }
            hookLeaflet();
        })();
        """
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument", {"source": js}
        )

    def inject_visuals(self):
        js_code = """
        window.hack_get_leaflet_map = function() {
            // Priority 0: Captured via hook
            if (window.__hack_map_instance) return window.__hack_map_instance;

            var isMap = function(o) {
                try {
                    return o && typeof o.addLayer === 'function' && typeof o.setView === 'function' && typeof o.latLngToContainerPoint === 'function';
                } catch(e) { return false; }
            };

            // 1. Direct container check
            var container = document.querySelector('.leaflet-container');
            if (container && container._leaflet_map) return container._leaflet_map;

            // 2. Global search
            var all = document.getElementsByTagName('*');
            for (var i = 0; i < all.length; i++) {
                var el = all[i];
                if (el._leaflet_map) return el._leaflet_map;

                // Nuclear scan of all properties on the element
                var keys = Object.keys(el);
                for (var j = 0; j < keys.length; j++) {
                    var key = keys[j];
                    try {
                        var val = el[key];
                        if (!val) continue;

                        // Check the value itself
                        if (isMap(val)) return val;

                        // If it's a React fiber or internal prop, check its contents (1 level deep)
                        if (typeof val === 'object' && (key.startsWith('__react') || key.startsWith('_leaflet') || key === 'leaflet')) {
                            if (val.stateNode && isMap(val.stateNode)) return val.stateNode;
                            if (val.memoizedProps && isMap(val.memoizedProps.map)) return val.memoizedProps.map;

                            // Check its keys
                            for (var subkey in val) {
                                if (isMap(val[subkey])) return val[subkey];
                            }
                        }
                    } catch(e) {}
                }
            }

            // 3. Last resort: check window globals
            for (var k in window) {
                try { if (isMap(window[k])) return window[k]; } catch(e){}
            }

            return null;
        };

        window.hack_draw_target = function(lat, lng) {
            if (typeof L === 'undefined') return "FALLO - Leaflet no cargado";
            var map = window.hack_get_leaflet_map();
            if (!map) return "FALLO - mapa no encontrado";

            if (window._hack_layers) {
                window._hack_layers.forEach(function(layer) {
                    try { map.removeLayer(layer); } catch(e) {}
                });
            }
            window._hack_layers = [];

            var circle = L.circle([lat, lng], {
                color: '#FF0000', weight: 4, opacity: 1.0,
                fillColor: '#FF0000', fillOpacity: 0.25, radius: 50000
            }).addTo(map);

            var dot = L.circleMarker([lat, lng], {
                radius: 8, color: '#FFFFFF', weight: 2,
                fillColor: '#FF0000', fillOpacity: 1.0
            }).addTo(map);

            window._hack_layers.push(circle, dot);
            map.panTo([lat, lng], { animate: true, duration: 0.5 });
            return "OK";
        };

        // HUD REMOVED PER USER REQUEST
        console.log("HUD disabled.");
        """
        self.driver.execute_script(js_code)

    def found_location(self, lat, lng):
        if self.last_coords == (lat, lng):
            return
        self.last_coords = (lat, lng)
        print(f"\n>>> COORDENADAS: {lat}, {lng}")

        # Removed HUD update logic, keeping only the retry loop for the map circle
        js_update = f"""
        // Retry logic for drawing (invisible mode)
        window.hack_draw_retries = 0;
        function tryDraw() {{
            var res = window.hack_draw_target({lat}, {lng});

            if (res === 'OK') {{
                console.log("[HACK] Draw success");
            }} else {{
                console.log("[HACK] Draw attempt " + window.hack_draw_retries + " failed: " + res);
                window.hack_draw_retries++;
                if (window.hack_draw_retries < 10) {{
                     setTimeout(tryDraw, 1000);
                }}
            }}
            return res;
        }}
        return tryDraw();
        """
        res = self.driver.execute_script(js_update)
        print(f"Estado de dibujo inicial: {res}")

    def process_queue(self):
        try:
            # 1. Check window.__hack_coords (from API interceptor)
            coords = self.driver.execute_script(
                """
                var c = window.__hack_coords;
                window.__hack_coords = null;
                return c;
                """
            )
            if coords and coords.get("lat") is not None:
                self.found_location(coords["lat"], coords["lng"])
                return

            # 2. Check IFRAMEs (Enhanced Regex Method)
            iframe_coords = self.driver.execute_script(
                """
                try {
                    // Method A: ID 'streetview' (Most common)
                    var el = document.getElementById('streetview');
                    var srcs = [el ? el.src : ''];

                    // Method B: All iframes
                    var iframes = document.getElementsByTagName('iframe');
                    for (var i = 0; i < iframes.length; i++) {
                        srcs.push(iframes[i].src);
                    }

                    for (var i = 0; i < srcs.length; i++) {
                        var src = srcs[i];
                        if (!src) continue;

                        // Regex match for location=lat,lng or ll=lat,lng or cbll=lat,lng
                        // Handles decimal coordinates with optional negative sign
                        var matches = [
                            src.match(/location=(-?\d+\.\d+),(-?\d+\.\d+)/),
                            src.match(/ll=(-?\d+\.\d+),(-?\d+\.\d+)/),
                            src.match(/cbll=(-?\d+\.\d+),(-?\d+\.\d+)/)
                        ];

                        for (var j = 0; j < matches.length; j++) {
                            if (matches[j] && matches[j].length >= 3) {
                                var lat = parseFloat(matches[j][1]);
                                var lng = parseFloat(matches[j][2]);
                                if (!isNaN(lat) && !isNaN(lng)) {
                                    return { lat: lat, lng: lng };
                                }
                            }
                        }
                    }
                } catch(e) {}
                return null;
                """
            )
            if iframe_coords and iframe_coords.get("lat") is not None:
                self.found_location(iframe_coords["lat"], iframe_coords["lng"])
        except:
            pass

    def run(self):
        self.inject_interceptors()
        print("Interceptor registrado.")

        self.driver.get("https://www.worldguessr.com/es")
        print("Esperando carga de pagina...")
        time.sleep(5)

        self.inject_visuals()
        print("Sistema inyectado. JUEGA AHORA.\n")

        while True:
            self.process_queue()
            time.sleep(0.3)


if __name__ == "__main__":
    bot = WorldGuessrGod()
    bot.run()
