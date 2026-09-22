# Lightweight prototype database abstraction.
# CSV data is used for the demo so the application remains easy to reproduce.
# Production can replace this layer with PostgreSQL without changing the UI logic.

def database_status():
    return {
        "engine": "CSV prototype datastore",
        "production_target": "PostgreSQL",
        "status": "Demo"
    }
