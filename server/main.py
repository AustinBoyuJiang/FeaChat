import sys

try:
    from . import database
    from .server import SocketServer
except ImportError:
    import database
    from server import SocketServer


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python -m server [--init|--clear]")
        return

    srv = SocketServer()

    # Pass --init to reset the database, --clear to wipe data only
    if "--init" in sys.argv:
        database.init_db(srv.db)
        print("Database initialized.")
    elif "--clear" in sys.argv:
        database.clear_db(srv.db)
        print("Database cleared.")

    srv.build()
    srv.listen()


if __name__ == "__main__":
    main()
