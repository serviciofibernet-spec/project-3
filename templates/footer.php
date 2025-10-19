    </main>
    
    <script>
        // Auto-refresh dashboard every 30 seconds
        if (window.location.pathname.endsWith('index.php') || window.location.pathname === '/') {
            setTimeout(() => {
                window.location.reload();
            }, 30000);
        }
        
        // Simple confirmation for dangerous actions
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('confirm-action')) {
                if (!confirm('¿Estás seguro de que quieres realizar esta acción?')) {
                    e.preventDefault();
                }
            }
        });
    </script>
</body>
</html>