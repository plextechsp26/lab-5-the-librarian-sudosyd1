/** All fetch calls to the Flask backend. Import from here instead of writing fetch() in components. */

/** Empty in dev (Vite proxy forwards to Flask). Set `VITE_API_URL` for production builds (e.g. Vercel). */
const API_BASE = import.meta.env.VITE_API_URL ?? '';


// Shared types

/** A document from the authors collection. */
export interface Author {
  _id: string;
  name: string;
  nationality: string;
  bio: string;
  birth_year: number;
}

/** A book as returned by GET /books — includes a resolved author_name. */
export interface Book {
  _id: string;
  title: string;
  author_id: string;
  author_name: string;
  genre: string;
  published_year: number;
  isbn: string;
  copies_available: number;
}

/** A single row in a book's borrow history table. */
export interface BorrowRecord {
  borrow_id: string;
  member_id: string;
  member_name: string;
  borrow_date: string;
  return_date: string | null;
}

/** A book as returned by GET /books/:id — extends Book with full author and history. */
export interface BookDetail extends Book {
  author: Author;
  borrow_history: BorrowRecord[];
}

/** A member as returned by GET /members — includes resolved card fields. */
export interface Member {
  _id: string;
  name: string;
  email: string;
  joined: string;
  card_number: string | null;
  card_issued: string | null;
}

/** The library card sub-object nested inside a MemberDetail response. */
export interface LibraryCard {
  card_number: string;
  issued: string;
  expires: string;
  status: string;
}

/** A single row in a member's borrow history table. */
export interface BorrowedBook {
  borrow_id: string;
  book_id: string;
  title: string;
  borrow_date: string;
  return_date: string | null;
}

/** A member as returned by GET /members/:id — extends Member with card and history. */
export interface MemberDetail extends Member {
  card: LibraryCard | null;
  borrowed_books: BorrowedBook[];
}

/** The document returned after a successful POST /borrow. */
export interface NewBorrow {
  borrow_id: string;
  member_id: string;
  book_id: string;
  borrow_date: string;
  return_date: null;
}


// GET functions

/** Fetches all books. Each book includes `author_name` resolved from the authors collection. */
export async function fetchAllBooks(): Promise<Book[]> {
  const response = await fetch(`${API_BASE}/books`);
  const books: Book[] = await response.json();
  return books;
}

/** Fetches all members. Each member includes `card_number` resolved from library_cards. */
export async function fetchAllMembers(): Promise<Member[]> {
  // TODO: replace this line with your fetch call to GET /members
  const response = await fetch(`${API_BASE}/members`)
  const members: Member[] = await response.json();
  return members;
}

/** Fetches a single book by ID. Response includes full `author` object and `borrow_history`. */
export async function fetchBookById(id: string): Promise<BookDetail> {
  // TODO: replace this line with your fetch call to GET /books/${id}
    const response = await fetch(`${API_BASE}/books/${id}`);
    const bookDetails: BookDetail = await response.json();
  return bookDetails;
}

/** Fetches a single member by ID. Response includes `card` and `borrowed_books`. */
export async function fetchMemberById(id: string): Promise<MemberDetail> {
  // TODO: replace this line with your fetch call to GET /members/${id}
  const response = await fetch(`${API_BASE}/members/${id}`);
  const memberDetails: MemberDetail = await response.json();
  return memberDetails;
}

// POST functions

/**
 * Creates a borrow record linking a member to a book.
 * @throws {Error} When the server returns an error (e.g. no copies available).
 */
export async function borrowBook(memberId: string, bookId: string): Promise<NewBorrow> {
  const response = await fetch(`${API_BASE}/borrow`, {
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

/**
 * Closes a borrow record by recording the return date.
 * @throws {Error} When the borrow record does not exist or was already returned.
 */
export async function returnBook(borrowId: string): Promise<{ message: string }> {
  // TODO: replace this line with your fetch call to POST /return
    const response = await fetch(`${API_BASE}/return`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ borrow_id: borrowId }),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Request failed.');
  }

  const result = await response.json();
  return result; 
}


// Extension functions

/** Searches books by title, author name, or genre using optional `q` and `genre` query params. */
export async function searchBooks(query: string, genre: string): Promise<Book[]> {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (genre) params.append('genre', genre);

  const response = await fetch(`${API_BASE}/books/search?${params.toString()}`);

  if (!response.ok) {
    throw new Error('Search request failed.');
  }

  const books: Book[] = await response.json();
  return books;
}
