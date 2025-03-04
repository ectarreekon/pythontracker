const CACHE_NAME = 'location-tracker-v2';
const urlsToCache = [
    '/',
    '/static/styles.css',
    '/manifest.json'
];

// Install event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(urlsToCache))
    );
});

// Fetch event
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cached response if found
                if (response) {
                    return response;
                }
                
                // Try network, fallback to cache
                return fetch(event.request).catch(() => {
                    // If both network and cache fail, return a fallback
                    return new Response('Offline mode. Please check your connection.');
                });
            })
    );
});

// Background sync (if supported)
self.addEventListener('sync', (event) => {
    if (event.tag === 'location-sync') {
        event.waitUntil(syncLocations());
    }
});

// Function to sync locations (mock implementation)
async function syncLocations() {
    // In a real implementation, you'd:
    // 1. Check for stored locations in IndexedDB
    // 2. Attempt to send them to the server
    // 3. Remove successfully synced locations
    console.log('Background sync attempted');
}
