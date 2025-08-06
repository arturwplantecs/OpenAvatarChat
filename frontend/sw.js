// Service Worker for OpenAvatarChat
// Basic caching and offline support

const CACHE_NAME = 'openavatar-chat-v1';
const urlsToCache = [
  '/',
  '/styles.css',
  '/js/config.js',
  '/js/api.js',
  '/js/audio.js',
  '/js/avatar.js',
  '/js/chat.js',
  '/js/app.js'
];

// Install event
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      }
    )
  );
});
