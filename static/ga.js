
// Updated content of static/ga.js
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());

// Assuming secrets.GTAG is replaced with the actual Google Analytics ID before this file is served
gtag('config', '{{ secrets.GTAG }}');