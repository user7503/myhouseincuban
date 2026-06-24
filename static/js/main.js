document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        document.querySelectorAll('.alert').forEach(function(alert) {
            new bootstrap.Alert(alert).close();
        });
    }, 5000);
});