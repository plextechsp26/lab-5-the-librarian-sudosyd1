import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_caching import Cache
from bson import ObjectId
from datetime import datetime, timezone
from db import db

app = Flask(__name__)

# CORS lets the React dev server (port 3000) call this API (port 5000).
CORS(app)

# Cache: backed by Redis, falls back to localhost if REDIS_URL is not set.
app.config["CACHE_TYPE"]      = "RedisCache"
app.config["CACHE_REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379")

cache = Cache(app)


def serialize(doc):
    """Convert BSON ObjectId fields to strings so jsonify() can serialize the document."""
    for key, value in list(doc.items()):
        if isinstance(value, ObjectId):
            doc[key] = str(value)
    return doc



# ---------------------------------------------------------------------------
# Health check — confirm the server is running
# ---------------------------------------------------------------------------

@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# PHASE 4 — GET routes go here
# ---------------------------------------------------------------------------

# Extension 4: once your GET routes are written, add caching by inserting
# @cache.cached between @app.route and your function definition, like this:

# @app.route("/books")
# @cache.cached(timeout=60, key_prefix="all_books")
# def get_all_books():
#     ...

# @app.route("/members")
# @cache.cached(timeout=60, key_prefix="all_members")
# def get_all_members():
#     ...


# ---------------------------------------------------------------------------
# PHASE 4 — GET routes go here
# ---------------------------------------------------------------------------

@app.route("/books")
@cache.cached(timeout=60, key_prefix="all_books")
def get_all_books():
    books = list(db.books.find({}))

    for book in books:
        author = db.authors.find_one({"_id": book["author_id"]})
        book["author_name"] = author["name"] if author else "Unknown"

    return jsonify([serialize(book) for book in books])


@app.route("/members")
@cache.cached(timeout=60, key_prefix="all_members")
def get_all_members():
    members = list(db.members.find({}))

    for member in members:
        # TODO: use db.library_cards.find_one() to look up the card for this member
        # Hint: search by {"member_id": member["_id"]}
        # If found, set member["card_number"] and member["card_issued"]
        # If not found, set both to None
        if db.library_cards.find_one({"member_id": member["_id"]}):
            card = db.library_cards.find_one({"member_id": member["_id"]})
            member["card_number"] = card["card_number"]
            member["card_issued"] = card["issued"].isoformat()
        else:
            member["card_number"] = None
            member["card_issued"] = None

    return jsonify([serialize(member) for member in members])


@app.route("/books/<book_id>")
@cache.cached(timeout=60, key_prefix="all_books")
def get_book(book_id):
    try:
        oid = ObjectId(book_id)
    except Exception:
        return jsonify({"error": "Invalid book ID."}), 404

    book = db.books.find_one({"_id": oid})
    if not book:
        return jsonify({"error": "Book not found."}), 404

    # TODO: look up the author with db.authors.find_one() and set book["author"]
    # Hint: serialize the author before attaching it
    book["author"] = db.authors.find_one({"_id": book["author_id"]})

    if book["author"]:
        book["author"] = serialize(book["author"])
    borrow_records = list(db.borrows.find({"book_id": oid}))

    borrow_history = []
    for record in borrow_records:
        # TODO: look up the member for this record with db.members.find_one()
        # Then append a dict to borrow_history with these keys:
        #   borrow_id, member_id, member_name, borrow_date, return_date
        # Use .isoformat() to convert datetime fields to strings
        member = db.members.find_one({"_id": record["member_id"]})
        borrow_history.append({
            "borrow_id": str(record["_id"]),
            "member_id": str(record["member_id"]),
            "member_name": member["name"] if member else "Unknown",
            "borrow_date": record["borrow_date"].isoformat() if record["borrow_date"] else None,
            "return_date": record["return_date"].isoformat() if record["return_date"] else None
        })
        pass

    book["borrow_history"] = borrow_history
    return jsonify(serialize(book))


@app.route("/members/<member_id>")
@cache.cached(timeout=60, key_prefix="all_members")
def get_member(member_id):
    try:
        oid = ObjectId(member_id)
    except Exception:
        return jsonify({"error": "Invalid member ID."}), 404

    member = db.members.find_one({"_id": oid})
    if not member:
        return jsonify({"error": "Member not found."}), 404

    # TODO: look up the card with db.library_cards.find_one({"member_id": oid})
    # If found, set member["card"] to a dict with: card_number, issued, expires, status
    # If not found, set member["card"] = None
    if db.library_cards.find_one({"member_id": oid}):
        card = db.library_cards.find_one({"member_id": oid})
        member["card"] = {
            "card_number": card["card_number"],
            "issued": card["issued"].isoformat(),
            "expires": card["expires"].isoformat(),
            "status": card["status"]
        }
    else: 
        member["card"] = None

    borrow_records = list(db.borrows.find({"member_id": oid}))

    borrowed_books = []
    for record in borrow_records:
        # TODO: look up the book for this record with db.books.find_one()
        # Then append a dict to borrowed_books with these keys:
        #   borrow_id, book_id, title, borrow_date, return_date
        book = db.books.find_one({"_id": record["book_id"]})
        borrowed_books.append({
            "borrow_id": str(record["_id"]),
            "book_id": str(record["book_id"]),
            "title": book["title"] if book else "Unknown",
            "borrow_date": record["borrow_date"].isoformat() if record["borrow_date"] else None,
            "return_date": record["return_date"].isoformat() if record["return_date"] else None
        })
        pass

    member["borrowed_books"] = borrowed_books

    if member.get("joined"):
        member["joined"] = member["joined"].isoformat()

    return jsonify(serialize(member))


# @app.route("/books")
# def get_all_books():
#     books = list(db.books.find({}))

#     for book in books:
#         author = db.authors.find_one({"_id": book["author_id"]})
#         book["author_name"] = author["name"] if author else "Unknown"

#     return jsonify([serialize(book) for book in books])


# @app.route("/members")
# def get_all_members():
#     members = list(db.members.find({}))

#     for member in members:
#         # TODO: use db.library_cards.find_one() to look up the card for this member
#         # Hint: search by {"member_id": member["_id"]}
#         # If found, set member["card_number"] and member["card_issued"]
#         # If not found, set both to None
#         member["card_number"] = None
#         member["card_issued"] = None

#     return jsonify([serialize(member) for member in members])


# @app.route("/books/<book_id>")
# def get_book(book_id):
#     try:
#         oid = ObjectId(book_id)
#     except Exception:
#         return jsonify({"error": "Invalid book ID."}), 404

#     book = db.books.find_one({"_id": oid})
#     if not book:
#         return jsonify({"error": "Book not found."}), 404

#     # TODO: look up the author with db.authors.find_one() and set book["author"]
#     # Hint: serialize the author before attaching it
#     book["author"] = None

#     borrow_records = list(db.borrows.find({"book_id": oid}))

#     borrow_history = []
#     for record in borrow_records:
#         # TODO: look up the member for this record with db.members.find_one()
#         # Then append a dict to borrow_history with these keys:
#         #   borrow_id, member_id, member_name, borrow_date, return_date
#         # Use .isoformat() to convert datetime fields to strings
#         pass

#     book["borrow_history"] = borrow_history
#     return jsonify(serialize(book))


# @app.route("/members/<member_id>")
# def get_member(member_id):
#     try:
#         oid = ObjectId(member_id)
#     except Exception:
#         return jsonify({"error": "Invalid member ID."}), 404

#     member = db.members.find_one({"_id": oid})
#     if not member:
#         return jsonify({"error": "Member not found."}), 404

#     # TODO: look up the card with db.library_cards.find_one({"member_id": oid})
#     # If found, set member["card"] to a dict with: card_number, issued, expires, status
#     # If not found, set member["card"] = None
#     member["card"] = None

#     borrow_records = list(db.borrows.find({"member_id": oid}))

#     borrowed_books = []
#     for record in borrow_records:
#         # TODO: look up the book for this record with db.books.find_one()
#         # Then append a dict to borrowed_books with these keys:
#         #   borrow_id, book_id, title, borrow_date, return_date
#         pass

#     member["borrowed_books"] = borrowed_books

#     if member.get("joined"):
#         member["joined"] = member["joined"].isoformat()

#     return jsonify(serialize(member))


# ---------------------------------------------------------------------------
# PHASE 6 — POST routes go here
# ---------------------------------------------------------------------------

# Extension 4: after each successful borrow or return, delete the stale
# list caches so the next GET reflects the updated copy counts:
#
# cache.delete("all_books")
# cache.delete("all_members")


# ---------------------------------------------------------------------------
# PHASE 6 — POST routes go here
# ---------------------------------------------------------------------------

@app.route("/borrow", methods=["POST"])
def borrow_book():
    data = request.get_json()

    if not data or "member_id" not in data or "book_id" not in data:
        return jsonify({"error": "member_id and book_id are required."}), 400
        

    try:
        member_oid = ObjectId(data["member_id"])
        book_oid   = ObjectId(data["book_id"])
    except Exception:
        return jsonify({"error": "Invalid member_id or book_id."}), 400

    book = db.books.find_one({"_id": book_oid})
    if not book:
        return jsonify({"error": "Book not found."}), 404
    if book["copies_available"] < 1:
        return jsonify({"error": "No copies available."}), 409
    
    new_borrow = {
        "member_id": member_oid,
        "book_id": book_oid,
        "borrow_date": datetime.now(timezone.utc),
        "return_date": None 
    }

    result = db.borrows.insert_one(new_borrow)

    db.books.update_one({"_id": book_oid}, {"$inc": {"copies_available": -1}})
 
    return jsonify({
        "borrow_id": str(result.inserted_id),
        "member_id": str(member_oid),
        "book_id": str(book_oid),
        "borrow_date": new_borrow["borrow_date"].isoformat(),
        "return_date": None 
    })

    # TODO: build a new_borrow dict with member_id, book_id, borrow_date, return_date=None
    # Hint: use datetime.now(timezone.utc) for borrow_date
    # Then insert it with db.borrows.insert_one()
    # Then decrement copies_available with db.books.update_one() and {"$inc": {"copies_available": -1}}
    # Finally return a JSON response with borrow_id, member_id, book_id, borrow_date, return_date
    

@app.route("/return", methods=["POST"])
def return_book():

    data = request.get_json()

    if not data or "borrow_id" not in data:
        return jsonify({"error": "borrow_id is required."}), 400

    try:
        borrow_oid = ObjectId(data["borrow_id"])
    except Exception:
        return jsonify({"error": "Invalid borrow_id."}), 400

    borrow = db.borrows.find_one({"_id": borrow_oid})
    if not borrow:
        return jsonify({"error": "Borrow record not found."}), 404
    if borrow["return_date"] is not None:
        return jsonify({"error": "This book has already been returned."}), 409
    
    db.borrows.update_one({"_id": borrow_oid}, {"$set": {"return_date": datetime.now(timezone.utc)}})
    db.books.update_one({"_id": borrow["book_id"]}, {"$inc": {"copies_available": 1}})

    # TODO: set return_date on the borrow record using db.borrows.update_one() and {"$set": {...}}
    # Then increment copies_available with db.books.update_one() and {"$inc": {"copies_available": 1}}
    # Finally return jsonify({"message": "Book returned successfully."})
    return jsonify({"message": "Book returned successfully."}), 200 


# @app.route("/borrow", methods=["POST"])
# def borrow_book():
#     data = request.get_json()

#     if not data or "member_id" not in data or "book_id" not in data:
#         return jsonify({"error": "member_id and book_id are required."}), 400

#     try:
#         member_oid = ObjectId(data["member_id"])
#         book_oid   = ObjectId(data["book_id"])
#     except Exception:
#         return jsonify({"error": "Invalid member_id or book_id."}), 400

#     book = db.books.find_one({"_id": book_oid})
#     if not book:
#         return jsonify({"error": "Book not found."}), 404
#     if book["copies_available"] < 1:
#         return jsonify({"error": "No copies available."}), 409

#     # TODO: build a new_borrow dict with member_id, book_id, borrow_date, return_date=None
#     # Hint: use datetime.now(timezone.utc) for borrow_date
#     # Then insert it with db.borrows.insert_one()
#     # Then decrement copies_available with db.books.update_one() and {"$inc": {"copies_available": -1}}
#     # Finally return a JSON response with borrow_id, member_id, book_id, borrow_date, return_date
#     pass


# @app.route("/return", methods=["POST"])
# def return_book():
#     data = request.get_json()

#     if not data or "borrow_id" not in data:
#         return jsonify({"error": "borrow_id is required."}), 400

#     try:
#         borrow_oid = ObjectId(data["borrow_id"])
#     except Exception:
#         return jsonify({"error": "Invalid borrow_id."}), 400

#     borrow = db.borrows.find_one({"_id": borrow_oid})
#     if not borrow:
#         return jsonify({"error": "Borrow record not found."}), 404
#     if borrow["return_date"] is not None:
#         return jsonify({"error": "This book has already been returned."}), 409

#     # TODO: set return_date on the borrow record using db.borrows.update_one() and {"$set": {...}}
#     # Then increment copies_available with db.books.update_one() and {"$inc": {"copies_available": 1}}
#     # Finally return jsonify({"message": "Book returned successfully."})
#     pass


# # ---------------------------------------------------------------------------
# # EXTENSION — GET /books/search?q=<query>&genre=<genre>
# # Both params optional. Case-insensitive substring match on title, author, genre.
# # ---------------------------------------------------------------------------

@app.route("/books/search")
def search_books():
    """Search books by title, author name, or genre. Both params optional."""
    q     = request.args.get("q",     "").strip()
    genre = request.args.get("genre", "").strip()

    mongo_filter = {}

    # Extension 3 — You implement the filter. See README (Extension 3).
    #
    # When `q` is non-empty: books should match if the title contains `q` OR the
    # author’s name contains `q`. Authors live in `db.authors`; books reference them
    # via `author_id`. Hint: query authors by name first, collect their `_id` values,
    # then use `$or` with a title regex and `author_id` `$in` that list.
    #
    # When `genre` is non-empty: restrict to books whose `genre` field contains
    # that string. Combine with `q` when both are present (both conditions apply).
    #
    # Use `$regex` with `"$options": "i"` for case-insensitive substring matches.
    # An empty `mongo_filter` should return every book.

    books = list(db.books.find(mongo_filter))

    for book in books:
        author = db.authors.find_one({"_id": book["author_id"]})
        book["author_name"] = author["name"] if author else "Unknown"

    return jsonify([serialize(book) for book in books])


if __name__ == "__main__":
    app.run(port=5000, debug=True)
