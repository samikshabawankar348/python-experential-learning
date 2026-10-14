"""
LIBRARY MANAGEMENT SYSTEM
Improved version using Python, JSON files, and CSV export.

Files created automatically in the same folder:
    books.json
    members.json
    transactions.json
    library_backup/ (when backup is selected)

Demo login:
    Username: admin
    Password: admin123

For a real deployment, replace the demo login with proper password hashing
and individual user accounts. This is an educational local application.
"""

import csv
import json
import os
import re
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BOOK_FILE = BASE_DIR / "books.json"
MEMBER_FILE = BASE_DIR / "members.json"
TRANSACTION_FILE = BASE_DIR / "transactions.json"
RESERVATION_FILE = BASE_DIR / "reservations.json"
BACKUP_DIR = BASE_DIR / "library_backup"

FINE_PER_DAY = 5
LOAN_DAYS = 14
MAX_BOOKS_PER_MEMBER = 3

# Demo credentials only; do not use hard-coded credentials in production.
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# --------------------------- JSON STORAGE ---------------------------

def load_data(filename):
    """Load a JSON list. Create a missing file as an empty list."""
    filename = Path(filename)
    if not filename.exists():
        save_data(filename, [])
        return []

    try:
        with filename.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            print(f"Warning: {filename.name} should contain a JSON list.")
            return []
        return data
    except (json.JSONDecodeError, OSError) as error:
        print(f"Warning: Could not read {filename.name}: {error}")
        return []


def save_data(filename, data):
    """Write JSON safely using a temporary file and atomic replacement."""
    filename = Path(filename)
    temp_file = filename.with_suffix(filename.suffix + ".tmp")
    try:
        with temp_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        temp_file.replace(filename)
        return True
    except OSError as error:
        print(f"Error saving {filename.name}: {error}")
        try:
            if temp_file.exists():
                temp_file.unlink()
        except OSError:
            pass
        return False


books = load_data(BOOK_FILE)
members = load_data(MEMBER_FILE)
transactions = load_data(TRANSACTION_FILE)
reservations = load_data(RESERVATION_FILE)


def save_all():
    """Save all data files and report whether all saves succeeded."""
    results = [
        save_data(BOOK_FILE, books),
        save_data(MEMBER_FILE, members),
        save_data(TRANSACTION_FILE, transactions),
        save_data(RESERVATION_FILE, reservations),
    ]
    return all(results)


# --------------------------- COMMON HELPERS ---------------------------

def today():
    return date.today()


def pause():
    input("\nPress Enter to continue...")


def heading(title):
    print("\n" + "=" * 68)
    print(title.center(68))
    print("=" * 68)


def ask_nonempty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")


def ask_integer(prompt, minimum=0):
    while True:
        try:
            value = int(input(prompt).strip())
            if value < minimum:
                print(f"Enter a number greater than or equal to {minimum}.")
                continue
            return value
        except ValueError:
            print("Please enter a whole number.")


def valid_phone(phone):
    return bool(re.fullmatch(r"[6-9]\d{9}", phone))


def valid_email(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.fullmatch(pattern, email))


def generate_id(prefix, data, key):
    numbers = []
    for item in data:
        value = str(item.get(key, ""))
        if value.startswith(prefix):
            suffix = value[len(prefix):]
            if suffix.isdigit():
                numbers.append(int(suffix))
    return f"{prefix}{max(numbers, default=0) + 1:03d}"


def find_by_id(data, key, value):
    value = value.strip().lower()
    for item in data:
        if str(item.get(key, "")).lower() == value:
            return item
    return None


def find_book(book_id):
    return find_by_id(books, "book_id", book_id)


def find_member(member_id):
    return find_by_id(members, "member_id", member_id)


def find_transaction(transaction_id):
    return find_by_id(transactions, "transaction_id", transaction_id)


def confirm(prompt):
    return input(prompt + " (y/n): ").strip().lower() == "y"


def money(amount):
    return f"₹{amount:.2f}"


# --------------------------- LOGIN ---------------------------

def login():
    heading("LIBRARY ADMIN LOGIN")
    print("Demo credentials: admin / admin123")
    for attempt in range(3):
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            print("\nLogin successful.")
            return True
        remaining = 2 - attempt
        print(f"Invalid username or password. Attempts remaining: {remaining}")
    print("Too many failed attempts. Program terminated.")
    return False


# --------------------------- BOOK MANAGEMENT ---------------------------

def display_book_details(book):
    issued = book.get("quantity", 0) - book.get("available", 0)
    print("-" * 54)
    print(f"Book ID       : {book.get('book_id', 'N/A')}")
    print(f"Title         : {book.get('title', 'N/A')}")
    print(f"Author        : {book.get('author', 'N/A')}")
    print(f"Category      : {book.get('category', 'N/A')}")
    print(f"ISBN          : {book.get('isbn', 'N/A')}")
    print(f"Total copies  : {book.get('quantity', 0)}")
    print(f"Available     : {book.get('available', 0)}")
    print(f"Issued        : {issued}")
    print("-" * 54)


def display_books():
    heading("BOOK CATALOG")
    if not books:
        print("No books found.")
        return
    print(f"{'ID':<8}{'Title':<26}{'Author':<20}{'Total':>7}{'Avail.':>7}")
    print("-" * 68)
    for book in books:
        print(
            f"{book.get('book_id',''):<8}"
            f"{book.get('title','')[:24]:<26}"
            f"{book.get('author','')[:18]:<20}"
            f"{book.get('quantity',0):>7}"
            f"{book.get('available',0):>7}"
        )


def add_book():
    heading("ADD BOOK")
    title = ask_nonempty("Book title: ")
    author = ask_nonempty("Author: ")
    category = ask_nonempty("Category: ")
    isbn = ask_nonempty("ISBN: ")

    existing = next(
        (b for b in books if str(b.get("isbn", "")).lower() == isbn.lower()),
        None,
    )
    quantity = ask_integer("Quantity to add: ", 1)

    if existing:
        existing["quantity"] = int(existing.get("quantity", 0)) + quantity
        existing["available"] = int(existing.get("available", 0)) + quantity
        if save_data(BOOK_FILE, books):
            print("Existing book quantity updated.")
        return

    book = {
        "book_id": generate_id("B", books, "book_id"),
        "title": title,
        "author": author,
        "category": category,
        "isbn": isbn,
        "quantity": quantity,
        "available": quantity,
    }
    books.append(book)
    if save_data(BOOK_FILE, books):
        print(f"Book added successfully. Book ID: {book['book_id']}")


def search_book():
    heading("SEARCH BOOK")
    keyword = ask_nonempty("Search by ID, title, author, category, or ISBN: ").lower()
    results = [
        b for b in books
        if any(keyword in str(b.get(field, "")).lower()
               for field in ("book_id", "title", "author", "category", "isbn"))
    ]
    if not results:
        print("No matching books found.")
    else:
        for book in results:
            display_book_details(book)


def update_book():
    heading("UPDATE BOOK")
    book = find_book(input("Enter book ID: "))
    if not book:
        print("Book not found.")
        return

    display_book_details(book)
    new_values = {}
    for field, label in (
        ("title", "Title"), ("author", "Author"), ("category", "Category")
    ):
        value = input(f"New {label} (Enter to keep current): ").strip()
        if value:
            new_values[field] = value

    isbn = input("New ISBN (Enter to keep current): ").strip()
    if isbn and any(
        b is not book and str(b.get("isbn", "")).lower() == isbn.lower()
        for b in books
    ):
        print("That ISBN already belongs to another book.")
        return
    if isbn:
        new_values["isbn"] = isbn

    issued = int(book.get("quantity", 0)) - int(book.get("available", 0))
    raw_quantity = input("New total quantity (Enter to keep current): ").strip()
    if raw_quantity:
        try:
            quantity = int(raw_quantity)
            if quantity < issued:
                print(f"Quantity cannot be below {issued}; copies are currently issued.")
                return
            if quantity < 0:
                print("Quantity cannot be negative.")
                return
            new_values["quantity"] = quantity
            new_values["available"] = quantity - issued
        except ValueError:
            print("Quantity must be a whole number.")
            return

    book.update(new_values)
    if save_data(BOOK_FILE, books):
        print("Book updated successfully.")


def remove_book():
    heading("REMOVE BOOK")
    book = find_book(input("Enter book ID: "))
    if not book:
        print("Book not found.")
        return
    if book.get("available", 0) != book.get("quantity", 0):
        print("Cannot remove a book while copies are issued.")
        return
    if any(t.get("book_id") == book["book_id"] for t in transactions):
        print("This book has transaction history and cannot be deleted safely.")
        print("Tip: keep it in the catalog, or implement an archive feature.")
        return
    if confirm(f"Remove '{book['title']}'?"):
        books.remove(book)
        if save_data(BOOK_FILE, books):
            print("Book removed.")


def book_menu():
    while True:
        heading("BOOK MANAGEMENT")
        print("1. Add book\n2. Display all books\n3. Search book")
        print("4. Update book\n5. Remove book\n6. Back")
        choice = input("Choose: ").strip()
        actions = {
            "1": add_book, "2": display_books, "3": search_book,
            "4": update_book, "5": remove_book,
        }
        if choice == "6":
            break
        action = actions.get(choice)
        if action:
            action()
            pause()
        else:
            print("Invalid choice.")


# --------------------------- MEMBER MANAGEMENT ---------------------------

def register_member():
    heading("REGISTER MEMBER")
    name = ask_nonempty("Full name: ")

    while True:
        phone = ask_nonempty("10-digit Indian mobile number: ")
        if not valid_phone(phone):
            print("Invalid phone number.")
        elif any(m.get("phone") == phone for m in members):
            print("That phone number is already registered.")
        else:
            break

    while True:
        email = ask_nonempty("Email: ")
        if not valid_email(email):
            print("Invalid email format.")
        elif any(m.get("email", "").lower() == email.lower() for m in members):
            print("That email is already registered.")
        else:
            break

    member = {
        "member_id": generate_id("M", members, "member_id"),
        "name": name,
        "phone": phone,
        "email": email,
        "active": True,
    }
    members.append(member)
    if save_data(MEMBER_FILE, members):
        print(f"Member registered. Member ID: {member['member_id']}")


def display_members():
    heading("MEMBER LIST")
    if not members:
        print("No members registered.")
        return
    print(f"{'ID':<9}{'Name':<25}{'Phone':<13}{'Email':<30}{'Status'}")
    print("-" * 86)
    for member in members:
        status = "Active" if member.get("active", True) else "Inactive"
        print(
            f"{member.get('member_id',''):<9}"
            f"{member.get('name','')[:23]:<25}"
            f"{member.get('phone',''):<13}"
            f"{member.get('email','')[:28]:<30}{status}"
        )


def search_member():
    heading("SEARCH MEMBER")
    keyword = ask_nonempty("Search by ID, name, phone, or email: ").lower()
    results = [
        m for m in members
        if any(keyword in str(m.get(field, "")).lower()
               for field in ("member_id", "name", "phone", "email"))
    ]
    if not results:
        print("No matching members.")
        return
    for member in results:
        print("-" * 40)
        print(f"ID: {member.get('member_id')}")
        print(f"Name: {member.get('name')}")
        print(f"Phone: {member.get('phone')}")
        print(f"Email: {member.get('email')}")
        print(f"Status: {'Active' if member.get('active', True) else 'Inactive'}")


def update_member():
    heading("UPDATE MEMBER")
    member = find_member(input("Enter member ID: "))
    if not member:
        print("Member not found.")
        return

    name = input(f"New name [{member['name']}]: ").strip()
    if name:
        member["name"] = name

    phone = input(f"New phone [{member['phone']}]: ").strip()
    if phone:
        if not valid_phone(phone):
            print("Invalid phone number; phone unchanged.")
        elif any(m is not member and m.get("phone") == phone for m in members):
            print("Phone belongs to another member; phone unchanged.")
        else:
            member["phone"] = phone

    email = input(f"New email [{member['email']}]: ").strip()
    if email:
        if not valid_email(email):
            print("Invalid email; email unchanged.")
        elif any(
            m is not member and m.get("email", "").lower() == email.lower()
            for m in members
        ):
            print("Email belongs to another member; email unchanged.")
        else:
            member["email"] = email

    if save_data(MEMBER_FILE, members):
        print("Member updated.")


def toggle_member_status():
    heading("ACTIVATE / DEACTIVATE MEMBER")
    member = find_member(input("Enter member ID: "))
    if not member:
        print("Member not found.")
        return
    member["active"] = not member.get("active", True)
    if save_data(MEMBER_FILE, members):
        print("Member status:", "Active" if member["active"] else "Inactive")


def remove_member():
    heading("REMOVE MEMBER")
    member = find_member(input("Enter member ID: "))
    if not member:
        print("Member not found.")
        return
    if any(
        t.get("member_id") == member["member_id"] and t.get("status") == "Issued"
        for t in transactions
    ):
        print("Cannot remove a member who currently has an issued book.")
        return
    if any(t.get("member_id") == member["member_id"] for t in transactions):
        print("This member has transaction history and cannot be deleted safely.")
        print("Deactivate the member instead to preserve records.")
        return
    if confirm(f"Remove member '{member['name']}'?"):
        members.remove(member)
        if save_data(MEMBER_FILE, members):
            print("Member removed.")


def member_books():
    heading("MEMBER BORROWED BOOKS")
    member = find_member(input("Enter member ID: "))
    if not member:
        print("Member not found.")
        return
    found = False
    for transaction in transactions:
        if transaction.get("member_id") == member["member_id"] and transaction.get("status") == "Issued":
            book = find_book(transaction.get("book_id", ""))
            print(
                f"{book.get('title', 'Unknown') if book else 'Unknown'} | "
                f"Transaction: {transaction.get('transaction_id')} | "
                f"Due: {transaction.get('due_date')}"
            )
            found = True
    if not found:
        print("This member has no currently issued books.")


def member_menu():
    while True:
        heading("MEMBER MANAGEMENT")
        print("1. Register member\n2. Display all members\n3. Search member")
        print("4. Update member\n5. Activate/deactivate member")
        print("6. Remove member\n7. View member's issued books\n8. Back")
        choice = input("Choose: ").strip()
        actions = {
            "1": register_member, "2": display_members, "3": search_member,
            "4": update_member, "5": toggle_member_status,
            "6": remove_member, "7": member_books,
        }
        if choice == "8":
            break
        action = actions.get(choice)
        if action:
            action()
            pause()
        else:
            print("Invalid choice.")


# --------------------------- ISSUE / RETURN / FINES ---------------------------

def active_loan_count(member_id):
    return sum(
        1 for t in transactions
        if t.get("member_id") == member_id and t.get("status") == "Issued"
    )


def issue_book():
    heading("ISSUE BOOK")
    book = find_book(input("Book ID: "))
    member = find_member(input("Member ID: "))

    if not book:
        print("Book not found.")
        return
    if not member:
        print("Member not found.")
        return
    if not member.get("active", True):
        print("This member is inactive.")
        return
    if book.get("available", 0) <= 0:
        print("No copies are currently available.")
        return
    if active_loan_count(member["member_id"]) >= MAX_BOOKS_PER_MEMBER:
        print(f"Member has reached the limit of {MAX_BOOKS_PER_MEMBER} books.")
        return
    if any(
        t.get("book_id") == book["book_id"]
        and t.get("member_id") == member["member_id"]
        and t.get("status") == "Issued"
        for t in transactions
    ):
        print("This member already has this book issued.")
        return

    issue_date = today()
    transaction = {
        "transaction_id": generate_id("T", transactions, "transaction_id"),
        "book_id": book["book_id"],
        "member_id": member["member_id"],
        "issue_date": issue_date.isoformat(),
        "due_date": (issue_date + timedelta(days=LOAN_DAYS)).isoformat(),
        "return_date": "",
        "fine": 0,
        "fine_paid": False,
        "status": "Issued",
    }
    transactions.append(transaction)
    book["available"] -= 1

    if save_data(BOOK_FILE, books) and save_data(TRANSACTION_FILE, transactions):
        print("Book issued successfully.")
        print("Transaction ID:", transaction["transaction_id"])
        print("Book:", book["title"])
        print("Member:", member["name"])
        print("Due date:", transaction["due_date"])
    else:
        print("Warning: saving failed. Check the JSON files before continuing.")


def calculate_fine(transaction, on_date=None):
    """Calculate current or final fine for a transaction."""
    on_date = on_date or today()
    due = date.fromisoformat(transaction["due_date"])
    effective_return = date.fromisoformat(transaction["return_date"]) if transaction.get("return_date") else on_date
    overdue_days = max(0, (effective_return - due).days)
    return overdue_days * FINE_PER_DAY, overdue_days


def return_book():
    heading("RETURN BOOK")
    transaction = find_transaction(input("Transaction ID: "))
    if not transaction:
        print("Transaction not found.")
        return
    if transaction.get("status") != "Issued":
        print("This transaction is not currently issued.")
        return

    fine, overdue_days = calculate_fine(transaction)
    book = find_book(transaction.get("book_id", ""))
    transaction["return_date"] = today().isoformat()
    transaction["fine"] = fine
    transaction["fine_paid"] = fine == 0
    transaction["status"] = "Returned"

    if book:
        book["available"] = min(
            int(book.get("quantity", 0)),
            int(book.get("available", 0)) + 1,
        )

    if save_data(BOOK_FILE, books) and save_data(TRANSACTION_FILE, transactions):
        print("Book returned successfully.")
        print("Overdue days:", overdue_days)
        print("Fine:", money(fine))
        print("Fine status:", "No fine due" if fine == 0 else "Pending payment")


def pay_fine():
    heading("RECORD FINE PAYMENT")
    transaction = find_transaction(input("Transaction ID: "))
    if not transaction:
        print("Transaction not found.")
        return
    if transaction.get("status") != "Returned":
        print("Return the book before recording its final fine payment.")
        return
    fine = int(transaction.get("fine", 0))
    if fine <= 0:
        print("No fine is due for this transaction.")
        return
    if transaction.get("fine_paid", False):
        print("Fine is already marked as paid.")
        return
    print("Fine due:", money(fine))
    if confirm("Confirm full fine payment"):
        transaction["fine_paid"] = True
        transaction["fine_paid_date"] = today().isoformat()
        if save_data(TRANSACTION_FILE, transactions):
            print("Fine payment recorded.")


def display_transactions():
    heading("TRANSACTION HISTORY")
    if not transactions:
        print("No transactions found.")
        return
    for t in transactions:
        book = find_book(t.get("book_id", ""))
        member = find_member(t.get("member_id", ""))
        print("-" * 54)
        print("Transaction:", t.get("transaction_id"))
        print("Book:", book.get("title", "Archived/removed") if book else "Archived/removed")
        print("Member:", member.get("name", "Archived/removed") if member else "Archived/removed")
        print("Issue date:", t.get("issue_date"))
        print("Due date:", t.get("due_date"))
        print("Return date:", t.get("return_date") or "Not returned")
        print("Fine:", money(float(t.get("fine", 0))))
        print("Fine status:", "Paid" if t.get("fine_paid", False) else ("Pending" if t.get("fine", 0) else "No fine"))
        print("Status:", t.get("status"))


def search_transaction():
    heading("SEARCH TRANSACTION")
    keyword = ask_nonempty("Transaction ID, book ID, or member ID: ").lower()
    results = [
        t for t in transactions
        if any(keyword in str(t.get(field, "")).lower()
               for field in ("transaction_id", "book_id", "member_id"))
    ]
    if not results:
        print("No matching transactions.")
        return
    for t in results:
        print(
            f"{t.get('transaction_id')} | Book {t.get('book_id')} | "
            f"Member {t.get('member_id')} | {t.get('status')} | "
            f"Due {t.get('due_date')} | Fine {money(float(t.get('fine', 0)))}"
        )


def issued_books(overdue_only=False):
    heading("OVERDUE BOOKS" if overdue_only else "CURRENTLY ISSUED BOOKS")
    found = False
    for t in transactions:
        if t.get("status") != "Issued":
            continue
        fine, overdue_days = calculate_fine(t)
        if overdue_only and overdue_days <= 0:
            continue
        found = True
        book = find_book(t.get("book_id", ""))
        member = find_member(t.get("member_id", ""))
        print("-" * 50)
        print("Transaction:", t.get("transaction_id"))
        print("Book:", book.get("title", "Unknown") if book else "Unknown")
        print("Member:", member.get("name", "Unknown") if member else "Unknown")
        print("Due date:", t.get("due_date"))
        if overdue_days > 0:
            print("Status: OVERDUE")
            print("Current fine:", money(fine))
        else:
            print("Days remaining:", (date.fromisoformat(t["due_date"]) - today()).days)
    if not found:
        print("No overdue books." if overdue_only else "No books are currently issued.")


def transaction_menu():
    while True:
        heading("TRANSACTION MANAGEMENT")
        print("1. Issue book\n2. Return book\n3. Transaction history")
        print("4. Search transaction\n5. Currently issued books")
        print("6. Overdue books\n7. Record fine payment\n8. Back")
        choice = input("Choose: ").strip()
        actions = {
            "1": issue_book, "2": return_book, "3": display_transactions,
            "4": search_transaction, "5": lambda: issued_books(False),
            "6": lambda: issued_books(True), "7": pay_fine,
        }
        if choice == "8":
            break
        action = actions.get(choice)
        if action:
            action()
            pause()
        else:
            print("Invalid choice.")


# --------------------------- BOOK RESERVATIONS ---------------------------

def reserve_book():
    """Add a member to a book's reservation queue."""
    heading("RESERVE A BOOK")
    book = find_book(input("Book ID to reserve: "))
    member = find_member(input("Member ID: "))

    if not book:
        print("Book not found.")
        return
    if not member:
        print("Member not found.")
        return
    if not member.get("active", True):
        print("Inactive members cannot reserve books.")
        return
    if any(
        r.get("book_id") == book["book_id"]
        and r.get("member_id") == member["member_id"]
        and r.get("status") == "Pending"
        for r in reservations
    ):
        print("This member already has a pending reservation for this book.")
        return
    if any(
        t.get("book_id") == book["book_id"]
        and t.get("member_id") == member["member_id"]
        and t.get("status") == "Issued"
        for t in transactions
    ):
        print("This member already has this book issued.")
        return

    reservation = {
        "reservation_id": generate_id("R", reservations, "reservation_id"),
        "book_id": book["book_id"],
        "member_id": member["member_id"],
        "reservation_date": today().isoformat(),
        "status": "Pending",
    }
    reservations.append(reservation)
    if save_data(RESERVATION_FILE, reservations):
        print("Reservation created successfully.")
        print("Reservation ID:", reservation["reservation_id"])
        if book.get("available", 0) > 0:
            print("A copy is currently available; the librarian can issue it.")
        else:
            print("No copies are available now. This reservation is recorded in the queue.")


def display_reservations():
    heading("BOOK RESERVATIONS")
    if not reservations:
        print("No reservations found.")
        return

    print(f"{'Reservation':<14}{'Book ID':<10}{'Member ID':<11}{'Date':<13}{'Status'}")
    print("-" * 65)
    for reservation in reservations:
        book = find_book(reservation.get("book_id", ""))
        member = find_member(reservation.get("member_id", ""))
        print(
            f"{reservation.get('reservation_id', ''):<14}"
            f"{reservation.get('book_id', ''):<10}"
            f"{reservation.get('member_id', ''):<11}"
            f"{reservation.get('reservation_date', ''):<13}"
            f"{reservation.get('status', 'Pending')}"
        )
        print(
            f"  Book: {book.get('title', 'Unknown') if book else 'Unknown'} | "
            f"Member: {member.get('name', 'Unknown') if member else 'Unknown'}"
        )


def cancel_reservation():
    heading("CANCEL RESERVATION")
    reservation_id = input("Reservation ID: ").strip()
    reservation = find_by_id(reservations, "reservation_id", reservation_id)
    if not reservation:
        print("Reservation not found.")
        return
    if reservation.get("status") != "Pending":
        print("Only pending reservations can be cancelled.")
        return
    if confirm(f"Cancel reservation {reservation_id}?"):
        reservation["status"] = "Cancelled"
        if save_data(RESERVATION_FILE, reservations):
            print("Reservation cancelled.")


def reservation_menu():
    while True:
        heading("BOOK RESERVATION MANAGEMENT")
        print("1. Reserve a book")
        print("2. View all reservations")
        print("3. Cancel a pending reservation")
        print("4. Back to main menu")
        choice = input("Choose: ").strip()
        actions = {
            "1": reserve_book,
            "2": display_reservations,
            "3": cancel_reservation,
        }
        if choice == "4":
            break
        action = actions.get(choice)
        if action:
            action()
            pause()
        else:
            print("Invalid choice.")


# --------------------------- DASHBOARD / REPORTS / BACKUP ---------------------------

def dashboard():
    heading("LIBRARY DASHBOARD")
    total_titles = len(books)
    total_copies = sum(int(b.get("quantity", 0)) for b in books)
    available = sum(int(b.get("available", 0)) for b in books)
    issued_count = sum(1 for t in transactions if t.get("status") == "Issued")
    returned_count = sum(1 for t in transactions if t.get("status") == "Returned")
    active_members = sum(1 for m in members if m.get("active", True))
    overdue_count = 0
    pending_fines = 0
    collected_fines = 0

    for t in transactions:
        if t.get("status") == "Issued":
            fine, overdue_days = calculate_fine(t)
            if overdue_days > 0:
                overdue_count += 1
                pending_fines += fine
        elif t.get("status") == "Returned":
            if t.get("fine_paid", False):
                collected_fines += int(t.get("fine", 0))
            else:
                pending_fines += int(t.get("fine", 0))

    print("BOOKS")
    print(f"  Titles: {total_titles} | Total copies: {total_copies}")
    print(f"  Available copies: {available} | Issued transactions: {issued_count}")
    print("\nMEMBERS")
    print(f"  Total members: {len(members)} | Active members: {active_members}")
    print("\nTRANSACTIONS")
    print(f"  Total: {len(transactions)} | Returned: {returned_count} | Overdue: {overdue_count}")
    pending_reservations = sum(1 for r in reservations if r.get("status") == "Pending")
    print(f"  Pending book reservations: {pending_reservations}")
    print("\nFINES")
    print(f"  Pending fines: {money(pending_fines)}")
    print(f"  Collected fines: {money(collected_fines)}")


def export_csv():
    heading("EXPORT REPORTS TO CSV")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    exports = [
        ("books.csv", books),
        ("members.csv", members),
        ("transactions.csv", transactions),
        ("reservations.csv", reservations),
    ]
    for filename, rows in exports:
        path = BASE_DIR / filename
        keys = sorted({key for row in rows for key in row.keys()})
        try:
            with path.open("w", newline="", encoding="utf-8-sig") as file:
                if keys:
                    writer = csv.DictWriter(file, fieldnames=keys, extrasaction="ignore")
                    writer.writeheader()
                    writer.writerows(rows)
            print(f"Exported: {path.name}")
        except OSError as error:
            print(f"Could not export {filename}: {error}")


def backup_data():
    heading("BACKUP DATA")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    files = (BOOK_FILE, MEMBER_FILE, TRANSACTION_FILE, RESERVATION_FILE)
    try:
        for source in files:
            if source.exists():
                destination = BACKUP_DIR / f"{source.stem}_{timestamp}{source.suffix}"
                shutil.copy2(source, destination)
                print(f"Backed up: {destination.name}")
        print(f"Backup folder: {BACKUP_DIR}")
    except OSError as error:
        print("Backup failed:", error)


# --------------------------- MAIN PROGRAM ---------------------------

def main():
    if not login():
        return

    while True:
        heading("LIBRARY MANAGEMENT SYSTEM")
        print("1. Dashboard")
        print("2. Book management")
        print("3. Member management")
        print("4. Transaction management")
        print("5. Display all books")
        print("6. Display all members")
        print("7. Overdue books")
        print("8. Export CSV reports")
        print("9. Backup JSON data")
        print("10. Book reservations")
        print("11. Save and exit")

        choice = input("Enter your choice: ").strip()
        actions = {
            "1": dashboard,
            "2": book_menu,
            "3": member_menu,
            "4": transaction_menu,
            "5": display_books,
            "6": display_members,
            "7": lambda: issued_books(True),
            "8": export_csv,
            "9": backup_data,
            "10": reservation_menu,
        }

        if choice == "11":
            save_all()
            print("Thank you for using the Library Management System.")
            break

        action = actions.get(choice)
        if action:
            action()
            if choice not in ("2", "3", "4"):
                pause()
        else:
            print("Invalid choice. Select a number from the menu.")
            pause()


if __name__ == "__main__":
    main()
