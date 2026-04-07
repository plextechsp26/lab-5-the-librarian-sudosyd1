[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/tgyAYXKu)
# The Librarian

A full-stack library management system. Browse books, view member records, and track who has borrowed what.

**Stack:** React · TypeScript · Vite · Flask · Python · MongoDB · Redis · Docker · Vercel · Render

---

## Table of Contents

**Part 1**
1. [Project Overview](#1-project-overview)
2. [Setup](#2-setup)
3. [MongoDB and Relationships](#3-mongodb-and-relationships)
4. [Seed Data](#4-seed-data)
5. [Flask GET Routes](#5-flask-get-routes)
6. [Wiring GET Fetch Calls](#6-wiring-get-fetch-calls)
7. [Flask POST Routes](#7-flask-post-routes)
8. [Wiring POST Fetch Calls](#8-wiring-post-fetch-calls)
9. [Detail Pages and Cross-Collection Lookups](#9-detail-pages-and-cross-collection-lookups)

**Part 2**
10. [Moving to Part 2](#moving-to-part-2)
11. [Extension 1 — Docker](#extension-1--docker)
12. [Extension 2 — Deployment](#extension-2--deployment)
13. [Extension 3 — Search Endpoint](#extension-3--search-endpoint)
14. [Extension 4 — Redis Caching](#extension-4--redis-caching)

**Resume**
15. [Resume Points](#resume-points)

---

# Part 1

## 1. Project Overview

You are building a The Librarian Project: a web application that lets you browse books, view member records, and track who has borrowed what. It is a small but complete full stack application, which means it has all three layers that real web applications use:

1. A **frontend** built with React and TypeScript: the part users see and interact with in the browser
2. A **backend** built with Python and Flask: a small server that receives requests and returns data
3. A **database** built with MongoDB: where the data actually lives between requests. The relationships between the data are real examples of patterns you will use in almost every application you build after this one.

### How Data Flows

```
+-----------+         HTTP Request          +----------+         Query          +----------+
|           |  GET /books  ------------>    |          |  db.books.find()  -->  |          |
|   React   |                               |  Flask   |                        | MongoDB  |
| (Browser) |  <-----------  JSON Response  |          |  <--  documents        |          |
+-----------+                               +----------+                        +----------+
```

Each layer has one job. React does not talk to MongoDB directly. Flask does not render HTML. MongoDB does not know anything about HTTP.

### The Three MongoDB Relationship Types in This Project

**One-to-One: Member → Library Card.** Each card stores the `_id` of its member. Kept separate because a card has its own lifecycle — it can expire or be suspended without touching the member record.

**One-to-Many: Author → Books.** Each book stores an `author_id`. The reference lives on the "many" side so adding a new book is a single insert, the author document never changes.

**Many-to-Many: Members ↔ Books via Borrows.** A separate `borrows` collection links one member to one book per loan. It also carries loan-specific data (`borrow_date`, `return_date`) that has nowhere else to live.

### Collections in This Project

```
  authors              books
  -------              ------
  _id  <-- author_id   _id
  name                 title
  bio                  genre
                       copies_available

  members              library_cards
  -------              -------------
  _id  <-- member_id   _id
  name                 card_number
  email                expires
  joined               status

                borrows
                -------
  members._id <-- member_id
  books._id   <-- book_id
                  borrow_date
                  return_date
```

### What Is Pre-Built vs. What You Write

Everything in `frontend/src/components/` is pre-built. Read those files to understand the data flow, but there is no need to modify them! The Books page already includes a search UI, but the matching Flask route exists only from **Part 2, Extension 3** — see [§6](#6-wiring-get-fetch-calls).

**You are responsible for writing:**

- All Flask routes in `backend/app.py` (Sections 5 and 7)
- All fetch functions in `frontend/src/api/library.ts` (Sections 6 and 8)

---

## 2. Setup

### Prerequisites

Before starting, make sure you have the following installed:

- **Python 3.9 or later** — check with `python3 --version`
- **Node.js 18 or later** — check with `node --version`
- **npm** — included with Node.js, check with `npm --version`
- **MongoDB** — either a free Atlas cluster or MongoDB running on your machine (see Step 3)

### Step 1 — Install Python Dependencies

Open a terminal and navigate to the `backend/` folder:

```bash
cd part1/backend
```

Create and activate a virtual environment:

```bash
python3 -m venv venv

# macOS / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

| Package | Purpose |
|---|---|
| `flask` | The web framework that handles HTTP requests |
| `pymongo` | The Python driver for MongoDB |
| `python-dotenv` | Reads `.env` files into environment variables |
| `flask-cors` | Allows the React frontend to call the Flask API |

### Step 2 — Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env`. It contains:

```
MONGO_URI=mongodb://localhost:27017/library
```

That default string is for **MongoDB running on your own computer** (`localhost`). If you use **Atlas** instead, replace `MONGO_URI` with your Atlas connection string (see Step 3).

### Step 3 — MongoDB: what it is doing, and where it runs

MongoDB holds every collection in this project (`authors`, `books`, `members`, `library_cards`, `borrows`). Flask uses **PyMongo** and your `MONGO_URI` to read and write those collections. The React app never talks to Mongo directly — only Flask does.

You only need **one** running MongoDB for Part 1. Pick **Atlas** or **local**; they are independent options, not two things you must install at once.

**Option A — MongoDB Atlas (cloud)**  
1. Create a free account at [mongodb.com/atlas](https://www.mongodb.com/atlas)  
2. Create a free **M0** cluster  
3. Under **Security > Database Access**, create a database user with read/write access  
4. Under **Security > Network Access**, add `0.0.0.0/0` to allow connections from any IP  
5. Under **Deployment > Connect**, choose **Drivers > Python** and copy the connection string  

It will look like:

```
mongodb+srv://youruser:yourpassword@cluster0.abc12.mongodb.net/library
```

Put that value in `.env` as `MONGO_URI`. Flask and `seed.py` send data over the internet to Atlas — no `mongod` process is required on your laptop.

**Option B — MongoDB on your machine (local)**  
Install and start the MongoDB server (for example [MongoDB Community Server](https://www.mongodb.com/try/download/community), or on macOS with Homebrew: `brew tap mongodb/brew` and `brew install mongodb-community`, then `brew services start mongodb-community`). Keep `MONGO_URI=mongodb://localhost:27017/library` in `.env`. All data lives in files Mongo manages on your computer.

**Part 2 + Docker (Extension 1)**  
`docker compose` starts a **separate** MongoDB inside a **container** (`mongo:7`). The backend container connects with `mongodb://mongodb:27017/library` — hostname `mongodb` is the Compose service name, not Atlas and not your host’s `localhost`. You do **not** need Atlas for that stack unless you deliberately override `MONGO_URI` to point at Atlas.

### Step 4 — Start the Flask Server

From the `backend/` folder with the virtual environment active:

```bash
python app.py
```

If it errors, remove the `?appName=` text!

Expected output:

```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Step 5 — Install Node Dependencies and Start React

```bash
cd part1/frontend
npm install
npm start
```

The dev server (**Vite**) opens the app at `http://localhost:3000` and reloads automatically on file saves. You can also run `npm run dev` (same as `npm start`).

### Checkpoint

Verify all three of the following before moving on:

- `http://localhost:5000/ping` returns `{ "status": "ok" }`
- `http://localhost:3000` shows the navigation bar with Books and Members links
- No errors appear in either terminal

---

## 3. MongoDB and Relationships

### MongoDB vs. SQL

| SQL | MongoDB |
|---|---|
| Table | Collection |
| Row | Document |
| Primary key | `_id` |
| Foreign key | A field storing another document's `_id` |

Unlike SQL, MongoDB does not enforce relationships automatically. If you store an `author_id` on a book, MongoDB does not know what that means — you write the lookup query yourself.

### What a Document Looks Like

Every document has an `_id` field. If you do not provide one, MongoDB generates it as a BSON ObjectId — a 12-byte value that looks like a hexadecimal string: `6622f4a1b3c0e1d2f9a84c17`.

```json
{
  "_id": "6622f4a1b3c0e1d2f9a84c17",
  "title": "The Glass Meridian",
  "genre": "Literary Fiction",
  "published_year": 2004,
  "copies_available": 3,
  "author_id": "6622f4a0b3c0e1d2f9a84c12"
}
```

The `author_id` field is just a regular field that holds the `_id` of a document in the `authors` collection. When your Flask code needs the author's name, it has to make a second query using that ID.

### One-to-One: Member and Library Card

**A member document:**
```json
{
  "_id": "6622f4a2b3c0e1d2f9a84c20",
  "name": "Justin Shen",
  "email": "justinshen@berkeley.edu",
  "joined": "2019-04-08T00:00:00"
}
```

**The corresponding library card document:**
```json
{
  "_id": "6622f4a3b3c0e1d2f9a84c21",
  "member_id": "6622f4a2b3c0e1d2f9a84c20",
  "card_number": "LIB-00041",
  "issued": "2021-03-14T00:00:00",
  "expires": "2026-03-14T00:00:00",
  "status": "active"
}
```

The card stores `member_id` — the reference lives on the card, not inside the member document.

### One-to-Many: Author and Books

**An author document:**
```json
{
  "_id": "6622f4a0b3c0e1d2f9a84c12",
  "name": "Marguerite Solenne",
  "birth_year": 1971,
  "nationality": "French-Canadian",
  "bio": "Known for intricate psychological fiction..."
}
```

**Two books by that author:**
```json
{ "_id": "6622f4a1b3c0e1d2f9a84c17", "title": "The Glass Meridian",  "author_id": "6622f4a0b3c0e1d2f9a84c12" }
{ "_id": "6622f4a1b3c0e1d2f9a84c18", "title": "Winter Cartography",  "author_id": "6622f4a0b3c0e1d2f9a84c12" }
```

### Many-to-Many: Members, Books, and Borrows

Two members:
```json
{ "_id": "aaa111", "name": "Justin Shen"  }
{ "_id": "bbb222", "name": "Sydney Dinh"  }
```

Two books:
```json
{ "_id": "ccc333", "title": "The Glass Meridian"    }
{ "_id": "ddd444", "title": "Fault Lines of Memory" }
```

Three borrow records linking them:
```json
{ "_id": "e1", "member_id": "aaa111", "book_id": "ccc333", "borrow_date": "2024-11-03", "return_date": "2024-11-24" }
{ "_id": "e2", "member_id": "bbb222", "book_id": "ccc333", "borrow_date": "2025-01-10", "return_date": null        }
{ "_id": "e3", "member_id": "bbb222", "book_id": "ddd444", "borrow_date": "2024-08-05", "return_date": "2024-08-26" }
```

From these three records you can answer: which books has each member borrowed, who has borrowed a given book, and what are the dates for each loan. Record `e2` has `return_date: null` — Sydney still has The Glass Meridian. The `borrows` collection also carries data that has nowhere else to live: `borrow_date` and `return_date` belong to the loan event, not to the member and not to the book.

### Full Collections Diagram

```
  authors                    books
  --------                   ------
  _id  <------- author_id    _id
  name                       title
  bio                        genre
  birth_year                 published_year
  nationality                isbn
                             copies_available


  members                    library_cards
  -------                    -------------
  _id  <------- member_id    _id
  name                       card_number
  email                      issued
  joined                     expires
                             status


                 borrows
                 -------
  members._id <-- member_id
  books._id   <-- book_id
                  borrow_date
                  return_date
```

---

## 4. Seed Data


### What Is Seed Data?

A seed script populates a database with a known set of initial data. During development, you need real-looking data to work with, otherwise you would be testing your UI against empty tables. The seed script drops all five collections and recreates them from scratch, so you can run it as many times as you need to reset to a clean state.

### How to Run

```bash
cd part1/backend
python seed.py
```

Expected output:

```
Dropping existing collections...
  Inserted 7 authors.
  Inserted 16 books.
  Inserted 10 members.
  Inserted 10 library cards.
  Inserted 26 borrow records.

Seed complete. All five collections are ready.
```

### Checkpoint

- If you use **Atlas**, open your cluster in the Atlas UI and confirm the collections appear after seeding.  
- If you use **local MongoDB**, connect with `mongosh mongodb://localhost:27017/library` (or Compass) and inspect the same collections.

**Seeding local Mongo** — The command is the same as above. From `part1/backend`, with your venv active and `mongod` running, `python seed.py` reads `MONGO_URI` from `.env`. If that URI is `mongodb://localhost:27017/library`, the script wipes and repopulates your **local** database. For Docker, use `docker compose exec backend python seed.py` from `part2/` (Extension 1).

---

## 5. Flask GET Routes

### How `@app.route` Works 

```python
@app.route("/books")
def get_all_books():
    return jsonify([])
```

For routes that accept a variable in the URL:

```python
@app.route("/books/<book_id>")
def get_book(book_id):
    # book_id is the string from the URL, e.g. "6622f4a1b3c0e1d2f9a84c17"
    pass
```

### How PyMongo's `find()` and `find_one()` Work

- `db.books.find({})`: returns all documents as a cursor
- `db.books.find({ "genre": "Thriller" })`: returns only matching documents
- `db.books.find_one({ "_id": some_id }): returns one document, or `None`

A cursor is not a list. Wrap it with `list()` or iterate over it in a loop.

### Why `_id` Must Be Converted to a String

Every MongoDB document has an `_id` field of type `ObjectId`. This is a Python object that the standard JSON encoder cannot handle so it raises a `TypeError`. The fix is to convert it to a string before returning:

```python
doc["_id"] = str(doc["_id"])
```

The `serialize()` helper in `app.py` does this for you. For a list of documents:

```python
books = [serialize(book) for book in db.books.find({})]
```

### Routes to Add

Open `part1/backend/app.py`. The four route stubs are already there; replace the starter code in each one with the full implementation.

### Checkpoint

- `GET /books`: array with `author_name` on each book
- `GET /members`: array with `card_number` on each member
- `GET /books/<id>`: single book with `author` and `borrow_history`
- `GET /members/<id>`: single member with `card` and `borrowed_books`

If any route returns a 500 error, check the Flask terminal, the full Python traceback appears there.

---

## 6. Wiring GET Fetch Calls

### The Dev-Server Proxy

In `frontend/vite.config.ts`, `server.proxy` forwards API paths to Flask during local development:

```ts
proxy: {
  '/books': { target: 'http://127.0.0.1:5000', changeOrigin: true },
  '/members': { target: 'http://127.0.0.1:5000', changeOrigin: true },
  // …borrow, return, ping
},
```

So a `fetch('/books')` from the browser hits Vite on port 3000, and Vite relays the request to `http://127.0.0.1:5000/books`. You keep short paths in `library.ts`; production uses `VITE_API_URL` instead (see Part 2 deployment).

### Search on the Books page (Part 1)

`BookList.tsx` includes a search box and genre filter that call `searchBooks()` → `GET /books/search`. **Part 1’s Flask app does not implement that route** — it is added in **Part 2, Extension 3**. In Part 1, expect search requests to **fail** (404) until you complete the backend there or move on to Part 2. For Part 1 checkpoints, use the full catalog from `GET /books` and ignore search.

### Your Task: Complete `library.ts`

Open `part1/frontend/src/api/library.ts`. The file has typed function signatures and JSDoc for each function. `fetchAllBooks` is already completed as the reference example:

```ts
export async function fetchAllBooks(): Promise<Book[]> {
  const response = await fetch(`${API_BASE}/books`);
  const books: Book[] = await response.json();
  return books;
}
```

Complete the remaining three GET functions following the same pattern. Each function's JSDoc tells you the endpoint and the return type.

### Checkpoint

After completing the four GET functions:

1. `/books` — table with all 16 books and their author names
2. Click a title — book detail page with author info and borrow history
3. `/members` — table with all 10 members and their card numbers
4. Click a name — member detail page with library card and borrowed books

If a page shows "Could not load" instead of data, open the browser developer tools (F12), go to the Network tab, and inspect the failing request to see what Flask returned.

---

## 7. Flask POST Routes


### Key PyMongo operations

```python
data = request.get_json()                                          # parse request body
result = db.borrows.insert_one(doc)                               # insert; result.inserted_id is the new _id
db.books.update_one({"_id": oid}, {"$set":  {"field": value}})   # set a field
db.books.update_one({"_id": oid}, {"$inc":  {"copies_available": -1}})  # decrement
```

### Routes to Add

Open `part1/backend/app.py`. The two route stubs are already there — replace the `pass` in each one with the following implementations.

---

**POST /borrow**: Creates a new borrow record and decrements `copies_available`.

**POST /return**: Sets `return_date` on the borrow record and increments `copies_available`.

### Checkpoint

```bash
# Test POST /borrow:
curl -X POST http://localhost:5000/borrow \
  -H "Content-Type: application/json" \
  -d '{"member_id": "<a member _id>", "book_id": "<a book _id>"}'

# Test POST /return:
curl -X POST http://localhost:5000/return \
  -H "Content-Type: application/json" \
  -d '{"borrow_id": "<the borrow_id from above>"}'
```

---

## 8. Wiring POST Fetch Calls

Unlike GET, a POST needs `method`, `headers: { 'Content-Type': 'application/json' }`, and `body: JSON.stringify(data)`. Without the Content-Type header, `request.get_json()` returns `None`.

### Completed Example: `borrowBook`

```ts
export async function borrowBook(memberId: string, bookId: string): Promise<NewBorrow> {
  const response = await fetch('/borrow', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ member_id: memberId, book_id: bookId }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Request failed.');
  }

  const newBorrow: NewBorrow = await response.json();
  return newBorrow;
}
```

`response.ok` is `true` for status codes 200–299. For a 400 or 409, it is `false`, and the function reads the error message from the body and throws it so the calling component can display it to the user.

### Your Task: Complete `returnBook`

Open `part1/frontend/src/api/library.ts` and complete `returnBook`. It should:

- Call `POST /return`
- Send `{ borrow_id: borrowId }` in the request body
- Throw an error if the response is not ok
- Return the response data on success

Use `borrowBook` as your template.

### Checkpoint

1. Open a book detail page
2. Copy a member `_id` from the Members page
3. Paste it into the Member ID field and click Borrow Book
4. You should see "Book borrowed successfully." and the borrow history should update
5. Copies Available should decrease by 1

---

## 9. Detail Pages and Cross-Collection Lookups

### The N+1 Query Problem

`GET /members/<member_id>` touches four collections: members → library_cards → borrows → books (one query per borrow record to get the title). This is the N+1 problem: 1 query returns N records, then N more queries fetch related data. At scale it kills performance. You won't notice it here, but recognize the pattern.

---

You have completed all phases. The Mini Library System is fully working: the database is seeded, the Flask API handles reads and writes, the React TypeScript frontend displays and updates data, and the full request-response cycle from browser to database and back is wired together.

---

# Part 2

## Moving to Part 2

Part 2 is a separate folder with the **same Phase 4 / Phase 6 scaffolding as Part 1** (identical route stubs and TODOs), plus **Part 2-only** pieces already wired in `part2/backend/app.py`: the Redis `Cache` object, commented hints for Extension 4, and the `GET /books/search` handler (Extension 3 — you still implement `mongo_filter`). The Part 2 frontend matches Part 1 (same Vite app and `library.ts` stubs).

If you fully completed Part 1, copy your **implemented** code from `part1/backend/app.py` into `part2/backend/app.py` **without removing** the `Cache` import/config, the Extension 4 comment blocks, or the `search_books` function at the bottom. Copy `part1/frontend/src/api/library.ts` → `part2/frontend/src/api/library.ts` if you finished those fetch helpers. Otherwise you can do all work directly in Part 2 and skip copying.

---

## Extension 1: Docker

Docker packages each service into a container so it runs identically everywhere: your laptop, a teammate's machine, or a cloud server.

### Files Already Created

The following files are already in `part2/`:

```
docker-compose.yml          <- orchestrates all four services
backend/Dockerfile          <- builds the Flask image
backend/.dockerignore       <- excludes venv, .env, __pycache__ from the image
frontend/Dockerfile         <- builds the React image (two-stage: Node build → nginx serve)
frontend/.dockerignore      <- excludes node_modules and build from the image
frontend/nginx.conf         <- configures nginx to serve React and proxy API calls to Flask
```

### How It Works

**`docker-compose.yml`** defines four services:

| Service | Image | Port |
|---|---|---|
| `mongodb` | `mongo:7` | 27017 |
| `redis` | `redis:7-alpine` | 6379 |
| `backend` | Built from `backend/Dockerfile` | 5000 |
| `frontend` | Built from `frontend/Dockerfile` | 3000 → 80 |

Service names act as hostnames within Docker's internal network. The backend container can reach MongoDB at `mongodb:27017`, not `localhost:27017`. The `environment` block in the backend service sets `MONGO_URI` and `REDIS_URL` accordingly.

**Mongo in Compose** — The `mongodb` service runs the official `mongo:7` image. It is **not** MongoDB Atlas and **not** the same as `mongod` on your Mac unless you point `MONGO_URI` elsewhere. Data for that container is stored in the `mongo_data` volume until you run `docker compose down -v`.

**Redis in Compose** — The `redis` service runs **Redis**, an in-memory key-value store. Part 2’s backend can use it for **HTTP response caching** (Extension 4): repeated `GET /books` and `GET /members` can be answered from Redis instead of hitting Mongo every time. Until you add the `@cache.cached` decorators, the app still runs; Redis is simply available on the network.

**`backend/Dockerfile`** installs dependencies from `requirements.txt` and starts the app with `gunicorn`. Gunicorn is a production WSGI server: it can handle concurrent requests. Flask's built-in `python app.py` dev server cannot, and should never be exposed publicly.

**`frontend/Dockerfile`** uses a two-stage build:
1. Stage 1 uses Node to run `npm run build`, which compiles the React app to static files
2. Stage 2 uses nginx to serve those static files

The final image contains only nginx and the compiled output — no Node runtime, no source code. This keeps the image small and means nothing sensitive ships to the server.

**`frontend/nginx.conf`** does two things:
- Proxies API traffic whose path starts with `/books`, `/members`, `/borrow`, `/return`, or `/ping` to the backend (this includes `/books/search` because it begins with `/books`)
- Routes everything else to `index.html` so React Router can handle client-side navigation

### Running with Docker

First, make sure Docker Desktop is installed and running. Then from `part2/`:

```bash
docker compose up --build
```

The first build takes a few minutes as Docker downloads base images and installs packages. Subsequent starts are faster because layers are cached.

Once running:
- `http://localhost:3000`: the React frontend
- `http://localhost:5000/`: the Flask backend

To seed the database while Docker is running:

```bash
docker compose exec backend python seed.py
```

To stop everything:

```bash
docker compose down
```

To stop and delete the database volume (full reset):

```bash
docker compose down -v
```

### Checkpoint

After `docker compose up --build`:

- `http://localhost:3000` shows the navigation bar
- `http://localhost:5000/` running the backend

---

## Extension 2: Deployment

### Architecture

In production there are three hosted services:

```
  Browser
     |
     v
  Vercel (React)  ---->  Render (Flask)  ---->  MongoDB Atlas
```

Each is free at the scale of a portfolio project.

### Step 1 — Deploy Flask to Render

1. Push your project to a GitHub repository
2. Create a free account at [render.com](https://render.com)
3. Click **New > Web Service** and connect your GitHub repo
4. Render detects `render.yaml` automatically and fills in the build and start commands
5. Under **Environment**, add two variables:
   - `MONGO_URI` — your Atlas connection string
   - `REDIS_URL` — leave blank for now (add a Redis instance if you complete Extension 4)
6. Click **Deploy**

Render gives you a public URL like `https://library-backend-xxxx.onrender.com`. Test it:

```
https://library-backend-xxxx.onrender.com/ping
```

You should see `{ "status": "ok" }`.

Seed the database by running the seed script locally with the Atlas URI:

```bash
MONGO_URI="mongodb+srv://..." python seed.py
```

### Step 2 — Set `VITE_API_URL` in the frontend

The `library.ts` file reads:

```ts
const API_BASE = import.meta.env.VITE_API_URL ?? '';
```

In development this is empty and the Vite dev-server proxy handles API calls. In production you need to tell the frontend where Flask lives.

Open `part2/frontend/.env.production` (create it if it does not exist):

```
VITE_API_URL=https://library-backend-xxxx.onrender.com
```

Replace the URL with your actual Render URL. Vite embeds this value at build time — every `fetch(\`${API_BASE}/books\`)` call in the compiled bundle will use the full Render URL.

Do not commit `.env.production` if it contains sensitive values. For Vercel, set it as an environment variable in the project settings instead (see Step 3).

### Step 3: Deploy React to Vercel

1. Create a free account at [vercel.com](https://vercel.com)
2. Click **Add New > Project** and import your GitHub repository
3. Set the **Root Directory** to `part2/frontend`
4. Under **Environment Variables**, add:
   - `VITE_API_URL` = `https://library-backend-xxxx.onrender.com`
5. Click **Deploy**

`vercel.json` is already present in the `part2/frontend/` folder. It contains a single catch-all rewrite that sends all paths to `index.html`, which is required for React Router to work on a static host.

Vercel gives you a URL like `https://library-system-abc.vercel.app`.

### Checkpoint

- `https://your-render-url/ping` returns `{ "status": "ok" }`
- `https://your-vercel-url/books` shows the book catalog
- Borrowing a book on the live site updates the database on Atlas

---

## Extension 3: Search Endpoint

### What You Implement

**Backend** — In `part2/backend/app.py`, complete `search_books()`. The route, reading query parameters, running `db.books.find(mongo_filter)`, resolving `author_name` for each book, and serializing the response are already written. **Your job is to build `mongo_filter`** so the query respects `q` and `genre`.

`request.args` is a dictionary of query parameters from the URL. For a request to `/books/search?q=ishiguro&genre=Literary+Fiction`, `request.args.get("q")` returns `"ishiguro"` and `request.args.get("genre")` returns `"Literary Fiction"`. Those values are already assigned to `q` and `genre` for you.

**Text search (`q`)** — Books do not embed the author’s name; they store `author_id`. To match either a title substring or an author name substring:

1. Query `db.authors` for documents whose `name` contains `q` (case-insensitive).
2. Collect their `_id` values into a list.
3. Set `mongo_filter["$or"]` to two conditions: the book’s `title` matches `q`, **or** the book’s `author_id` is in that list.

Example shape (you still need to obtain `matching_author_ids` from the database):

```python
mongo_filter["$or"] = [
    {"title":     {"$regex": q, "$options": "i"}},
    {"author_id": {"$in": matching_author_ids}},
]
```

**Genre (`genre`)** — Add a case-insensitive substring condition on the book’s `genre` field. When both `q` and `genre` are present, both must be satisfied (combine them in the same `mongo_filter`).

`"$options": "i"` makes regex matches case-insensitive. Without it, searching for `"Murakami"` would not match `"murakami"`.

A complete reference implementation lives in `.solutions` under **part2/backend/app.py — Extension 3: Search**.

### What Is Already Wired

**Frontend** — `part2/frontend/src/api/library.ts` already defines `searchBooks(query, genre)`. It uses `URLSearchParams` to safely encode the query string:

```ts
const params = new URLSearchParams();
if (query) params.append('q', query);
if (genre) params.append('genre', genre);
fetch(`${API_BASE}/books/search?${params.toString()}`);
```

`URLSearchParams` handles special characters automatically. If a user searches for `"García Márquez"`, the encoded URL becomes `/books/search?q=Garc%C3%ADa+M%C3%A1rquez`, which Flask decodes correctly on the other end.

**Frontend** — `BookList.tsx` already contains a search bar and genre dropdown. After your backend filter works, try it:

1. Start the app
2. Open the Books page
3. Type "Ishiguro" in the search box and click Search
4. Filter by genre "Thriller" using the dropdown

### Checkpoint

- `http://localhost:5000/books/search?q=ishiguro` returns only Ishiguro's books
- `http://localhost:5000/books/search?genre=Thriller` returns only thrillers
- `http://localhost:5000/books/search?q=le+carre&genre=Thriller` returns only le Carré thrillers
- `http://localhost:5000/books/search` with no params returns all books
- The search bar and genre dropdown in the UI produce the same results

---

## Extension 4: Redis Caching

**What Redis is** — Redis keeps key-value data **in memory** (RAM), so reads and writes are extremely fast compared to disk or a remote database. It is a general-purpose tool; in this project you use it only as the **backing store for Flask-Caching**.

**What you use it for here**: Listing all books or all members runs several MongoDB queries. When many clients hit `GET /books` or `GET /members` with the same parameters, caching stores the **JSON response** in Redis and can return it without re-querying Mongo — same idea as memoizing an expensive function, but shared across requests. You must **invalidate** those entries when data changes (`POST /borrow`, `POST /return`) so the UI never shows stale copy counts. `flask-caching` wires this up with a decorator on the view function.

### Setup

Redis is already in `requirements.txt` and `docker-compose.yml`. The cache is configured in `part2/backend/app.py`:

```python
app.config["CACHE_TYPE"]      = "RedisCache"
app.config["CACHE_REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379")

cache = Cache(app)
```

If Redis is not running, Flask falls back gracefully: requests are served normally, just without caching. Nothing breaks.

### Step 1 — Cache the GET Routes

After you have completed the GET routes, add the `@cache.cached` decorator to `GET /books` and `GET /members`:

```python
@app.route("/books")
@cache.cached(timeout=60, key_prefix="all_books")
def get_all_books():
    ...

@app.route("/members")
@cache.cached(timeout=60, key_prefix="all_members")
def get_all_members():
    ...
```

`timeout=60` means the cached response expires after 60 seconds even if nothing has changed — a safety net. `key_prefix` is the key Redis stores the response under.

### Step 2 — Invalidate the Cache on Writes

Caching a list makes sense only if you also clear the cache when the list changes. Add these two lines inside both `POST /borrow` and `POST /return`, just before the `return` statement:

```python
cache.delete("all_books")
cache.delete("all_members")
```

This ensures that the next request to `/books` or `/members` fetches fresh data from MongoDB instead of returning a stale cached response. Without this step the cache would show the old copy count on the Books page even after a book is borrowed.

This is called **cache invalidation**: deciding when stored data is no longer valid and must be discarded. It is widely considered one of the genuinely hard problems in software engineering, because getting it wrong produces bugs that are difficult to reproduce (data looks correct most of the time, but not always).

### Step 3 — Start Redis Locally

If you are running the project outside Docker:

```bash
# macOS (Homebrew):
brew services start redis

# Linux:
sudo systemctl start redis
```

If you are using Docker, Redis starts automatically with `docker compose up`.

### Checkpoint

- Visit `http://localhost:5000/books` once, then again — the second response is served from Redis (you can verify this by adding `print("querying MongoDB")` inside `get_all_books` and confirming it only prints on the first request)
- Borrow a book, then visit `/books` — `copies_available` shows the updated count (confirming the cache was invalidated)
- Stop Redis and visit `/books` — the route still works, just without caching

---

# Resume Points

Copy the block below into the Projects section of your resume. Pick 3–4 bullets that best match the roles you are applying for.

---

**The Librarian** | React · TypeScript · Vite · Flask · Python · MongoDB · Redis · Docker · Vercel · Render

- Built a full-stack library management system with a React/TypeScript frontend, Flask REST API, and MongoDB database, delivering end-to-end CRUD functionality across books, members, and borrow records
- Designed a normalized MongoDB schema modeling one-to-one, one-to-many, and many-to-many document relationships, enabling accurate real-time tracking of book availability across concurrent borrowers
- Containerized a four-service application (Flask, React, MongoDB, Redis) with Docker Compose, reducing environment setup from a multi-step manual process to a single `docker compose up` command
- Deployed to production on Render and Vercel with environment-based configuration, enabling zero-code-change promotion from local development to a publicly accessible live URL
- Reduced redundant database load by implementing Redis response caching with targeted cache invalidation on write operations, ensuring stale data is never served after a borrow or return
