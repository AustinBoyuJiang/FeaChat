import sys
import database
from server import SocketServer

if __name__ == "__main__":
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
