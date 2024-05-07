// static/image_cache.js

let db;

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('imageCache', 1);

    request.onerror = () => {
      reject(new Error('Failed to open database'));
    };

    request.onsuccess = (event) => {
      db = event.target.result;
      resolve();
    };

    request.onupgradeneeded = (event) => {
      db = event.target.result;
      db.createObjectStore('images', { keyPath: 'url' });
    };
  });
}

async function isImageCached(imageUrl) {
  await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['images'], 'readonly');
    const store = transaction.objectStore('images');
    const request = store.get(imageUrl);

    request.onerror = () => {
      reject(new Error('Failed to check image cache'));
    };

    request.onsuccess = () => {
      resolve(request.result !== undefined);
    };
  });
}

async function saveImageToCache(imageUrl, imageData) {
  await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['images'], 'readwrite');
    const store = transaction.objectStore('images');
    const request = store.put({ url: imageUrl, data: imageData });

    request.onerror = () => {
      reject(new Error('Failed to save image to cache'));
    };

    request.onsuccess = () => {
      resolve();
    };
  });
}

async function loadImageFromCache(imageUrl) {
  await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['images'], 'readonly');
    const store = transaction.objectStore('images');
    const request = store.get(imageUrl);

    request.onerror = () => {
      reject(new Error('Failed to load image from cache'));
    };

    request.onsuccess = () => {
      resolve(request.result ? request.result.data : null);
    };
  });
}