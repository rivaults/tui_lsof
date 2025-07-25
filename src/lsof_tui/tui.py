from .app import LsofApp

def main():
    """Entry point for the TUI application."""
    app = LsofApp()
    app.run()

if __name__ == "__main__":
    main()
