// heartbeat.js
document.addEventListener('DOMContentLoaded', function() {
    function checkSession() {
        fetch('/heartbeat')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Session timeout');
                }
                return response.json();
            })
            .then(data => console.log('Session active:', data))
            .catch(error => {
                alert('Your session has timed out, please refresh.');
                // Optional: Redirect to login or refresh
                // window.location.href = '/login';
            });
    }

    // Check session status every 5 minutes as an example; adjust the interval as needed
    setInterval(checkSession, 60 * 60 * 1000);
});
