import json
import os
import re
from datetime import datetime, timedelta


# ============================================================
# CONFIGURATION
# ============================================================

BOOK_FILE = "books.json"
MEMBER_FILE = "members.json"
TRANSACTION_FILE = "transactions.json"

FINE_PER_DAY = 5
LOAN_DAYS = 14
MAX_BOOKS_PER_MEMBER = 3

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ============================================================
# FILE HANDLING
# ============================================================

def load_data(filename):
    """Load data from JSON file."""

    if not os.path.exists(filename):
        return []

    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

            if isinstance(data, list):
                return data

            return []

    except (json.JSONDecodeError, FileNotFoundError):
        print(f"Warning: Could not load {filename}. Starting with empty data.")
        return []


def save_data(filename, data):
    """Save data to JSON file."""

    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    except OSError as error:
        print("Error saving data:", error)


# ============================================================
# LOAD DATA
# ============================================================

books = load_data(BOOK_FILE)
members = load_data(MEMBER_FILE)
transactions = load_data(TRANSACTION_FILE)


# ============================================================
# GENERAL FUNCTIONS
# ============================================================

def pause():
    input("\nPress Enter to continue...")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def today():
    return datetime.now().date()


def generate_id(prefix, data, key):
    """Generate unique ID."""

    numbers = []

    for item in data:
        value = str(item.get(key, ""))

        if value.startswith(prefix):
            try:
                numbers.append(int(value[len(prefix):]))
            except ValueError:
                pass

    new_number = max(numbers, default=0) + 1

    return f"{prefix}{new_number:03d}"


def find_book(book_id):
    for book in books:
        if book.get("book_id", "").lower() == book_id.lower():
            return book

    return None


def find_member(member_id):
    for member in members:
        if member.get("member_id", "").lower() == member_id.lower():
            return member

    return None


def find_transaction(transaction_id):
    for transaction in transactions:
        if transaction.get("transaction_id", "").lower() == transaction_id.lower():
            return transaction

    return None


# ============================================================
# VALIDATION FUNCTIONS
# ============================================================

def valid_phone(phone):
    """Validate Indian-style 10 digit phone number."""

    return bool(re.fullmatch(r"[6-9]\d{9}", phone))


def valid_email(email):
    """Validate email."""

    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    return bool(re.fullmatch(pattern, email))


def get_positive_integer(prompt):
    """Get positive integer from user."""

    while True:

        try:
            value = int(input(prompt))

            if value <= 0:
                print("Please enter a number greater than 0.")
                continue

            return value

        except ValueError:
            print("Please enter a valid number.")


def get_non_negative_integer(prompt):
    """Get zero or positive integer."""

    while True:

        try:
            value = int(input(prompt))

            if value < 0:
                print("Number cannot be negative.")

                continue

            return value

        except ValueError:
            print("Please enter a valid number.")


# ============================================================
# LOGIN
# ============================================================

def login():
    """Admin login."""

    clear_screen()

    print("=" * 55)
    print("              LIBRARY ADMIN LOGIN")
    print("=" * 55)

    attempts = 3

    while attempts > 0:

        username = input("\nUsername: ").strip()
        password = input("Password: ").strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            print("\nLogin successful!")
            pause()

            return True

        attempts -= 1

        print("\nInvalid username or password.")
        print("Attempts remaining:", attempts)

    print("\nToo many failed attempts.")
    print("Program terminated.")

    return False


# ============================================================
# BOOK MANAGEMENT
# ============================================================

def add_book():

    print("\n========== ADD BOOK ==========")

    title = input("Enter book title: ").strip()
    author = input("Enter author name: ").strip()
    category = input("Enter category: ").strip()
    isbn = input("Enter ISBN: ").strip()

    if not title or not author or not category or not isbn:
        print("\nAll fields are required.")
        return

    # Check duplicate ISBN
    for book in books:

        if book.get("isbn", "").lower() == isbn.lower():

            quantity = get_positive_integer(
                "Book already exists. Enter quantity to add: "
            )

            book["quantity"] += quantity
            book["available"] += quantity

            save_data(BOOK_FILE, books)

            print("\nExisting book quantity updated.")
            return

    quantity = get_positive_integer("Enter quantity: ")

    book_id = generate_id("B", books, "book_id")

    new_book = {
        "book_id": book_id,
        "title": title,
        "author": author,
        "category": category,
        "isbn": isbn,
        "quantity": quantity,
        "available": quantity
    }

    books.append(new_book)

    save_data(BOOK_FILE, books)

    print("\nBook added successfully!")
    print("Book ID:", book_id)


def display_books():

    print("\n================ ALL BOOKS ================")

    if not books:
        print("No books available.")
        return

    print(
        f"{'ID':<8}"
        f"{'Title':<25}"
        f"{'Author':<20}"
        f"{'Category':<15}"
        f"{'Total':<8}"
        f"{'Available':<10}"
    )

    print("-" * 86)

    for book in books:

        print(
            f"{book.get('book_id', ''):<8}"
            f"{book.get('title', '')[:23]:<25}"
            f"{book.get('author', '')[:18]:<20}"
            f"{book.get('category', '')[:13]:<15}"
            f"{book.get('quantity', 0):<8}"
            f"{book.get('available', 0):<10}"
        )


def display_book_details(book):

    print("\n----------------------------------------")
    print("Book ID    :", book["book_id"])
    print("Title      :", book["title"])
    print("Author     :", book["author"])
    print("Category   :", book.get("category", "N/A"))
    print("ISBN       :", book.get("isbn", "N/A"))
    print("Total      :", book["quantity"])
    print("Available  :", book["available"])
    print("Issued     :", book["quantity"] - book["available"])
    print("----------------------------------------")


def search_book():

    print("\n========== SEARCH BOOK ==========")

    keyword = input(
        "Enter ID, title, author, category or ISBN: "
    ).strip().lower()

    if not keyword:
        print("Search value cannot be empty.")
        return

    results = []

    for book in books:

        if (
            keyword in book.get("book_id", "").lower()
            or keyword in book.get("title", "").lower()
            or keyword in book.get("author", "").lower()
            or keyword in book.get("category", "").lower()
            or keyword in book.get("isbn", "").lower()
        ):
            results.append(book)

    if not results:
        print("\nNo matching book found.")
        return

    print("\nSearch Results:")

    for book in results:
        display_book_details(book)


def update_book():

    print("\n========== UPDATE BOOK ==========")

    book_id = input("Enter book ID: ").strip()

    book = find_book(book_id)

    if not book:
        print("Book not found.")
        return

    display_book_details(book)

    title = input(
        "New title (Enter to keep old): "
    ).strip()

    author = input(
        "New author (Enter to keep old): "
    ).strip()

    category = input(
        "New category (Enter to keep old): "
    ).strip()

    isbn = input(
        "New ISBN (Enter to keep old): "
    ).strip()

    if title:
        book["title"] = title

    if author:
        book["author"] = author

    if category:
        book["category"] = category

    if isbn:

        # Check duplicate ISBN
        for other in books:

            if (
                other != book
                and other.get("isbn", "").lower() == isbn.lower()
            ):
                print("This ISBN already belongs to another book.")
                return

        book["isbn"] = isbn

    while True:

        quantity_input = input(
            "New total quantity (Enter to keep old): "
        ).strip()

        if quantity_input == "":
            break

        try:

            new_quantity = int(quantity_input)

            if new_quantity < 0:
                print("Quantity cannot be negative.")
                continue

            issued = book["quantity"] - book["available"]

            if new_quantity < issued:
                print(
                    f"Cannot set quantity below {issued}. "
                    "Some copies are currently issued."
                )
                continue

            book["quantity"] = new_quantity
            book["available"] = new_quantity - issued

            break

        except ValueError:
            print("Please enter a valid number.")

    save_data(BOOK_FILE, books)

    print("\nBook updated successfully!")


def remove_book():

    print("\n========== REMOVE BOOK ==========")

    book_id = input("Enter book ID: ").strip()

    book = find_book(book_id)

    if not book:
        print("Book not found.")
        return

    if book["available"] != book["quantity"]:

        print("\nCannot remove this book.")
        print("Some copies are currently issued.")

        return

    # Check transaction history
    has_history = any(
        t["book_id"].lower() == book_id.lower()
        for t in transactions
    )

    if has_history:

        print(
            "\nThis book has transaction history."
        )

        print(
            "Removing it may cause old transactions to show as Unknown."
        )

    confirmation = input(
        f"Remove '{book['title']}'? (y/n): "
    ).strip().lower()

    if confirmation == "y":

        books.remove(book)

        save_data(BOOK_FILE, books)

        print("\nBook removed successfully.")

    else:

        print("Operation cancelled.")


# ============================================================
# MEMBER MANAGEMENT
# ============================================================

def register_member():

    print("\n========== REGISTER MEMBER ==========")

    name = input("Enter member name: ").strip()

    if not name:
        print("Name cannot be empty.")
        return

    while True:

        phone = input("Enter phone number: ").strip()

        if valid_phone(phone):
            break

        print(
            "Invalid phone number."
            "\nEnter a valid 10-digit Indian mobile number."
        )

    # Duplicate phone
    for member in members:

        if member.get("phone", "") == phone:

            print("A member with this phone number already exists.")
            return

    while True:

        email = input("Enter email: ").strip()

        if valid_email(email):
            break

        print("Invalid email format.")

    # Duplicate email
    for member in members:

        if member.get("email", "").lower() == email.lower():

            print("A member with this email already exists.")
            return

    member_id = generate_id("M", members, "member_id")

    new_member = {
        "member_id": member_id,
        "name": name,
        "phone": phone,
        "email": email,
        "active": True
    }

    members.append(new_member)

    save_data(MEMBER_FILE, members)

    print("\nMember registered successfully!")
    print("Member ID:", member_id)


def display_members():

    print("\n================ ALL MEMBERS ================")

    if not members:

        print("No members registered.")

        return

    print(
        f"{'ID':<10}"
        f"{'Name':<25}"
        f"{'Phone':<15}"
        f"{'Email':<30}"
        f"{'Status':<10}"
    )

    print("-" * 90)

    for member in members:

        status = (
            "Active"
            if member.get("active", True)
            else "Inactive"
        )

        print(
            f"{member['member_id']:<10}"
            f"{member['name'][:23]:<25}"
            f"{member['phone'][:13]:<15}"
            f"{member['email'][:28]:<30}"
            f"{status:<10}"
        )


def search_member():

    print("\n========== SEARCH MEMBER ==========")

    keyword = input(
        "Enter ID, name, phone or email: "
    ).strip().lower()

    if not keyword:
        print("Search value cannot be empty.")
        return

    results = []

    for member in members:

        if (
            keyword in member.get("member_id", "").lower()
            or keyword in member.get("name", "").lower()
            or keyword in member.get("phone", "").lower()
            or keyword in member.get("email", "").lower()
        ):
            results.append(member)

    if not results:

        print("No matching member found.")

        return

    for member in results:

        print("\n----------------------------")
        print("Member ID :", member["member_id"])
        print("Name      :", member["name"])
        print("Phone     :", member["phone"])
        print("Email     :", member["email"])
        print(
            "Status    :",
            "Active" if member.get("active", True)
            else "Inactive"
        )


def update_member():

    print("\n========== UPDATE MEMBER ==========")

    member_id = input("Enter member ID: ").strip()

    member = find_member(member_id)

    if not member:

        print("Member not found.")

        return

    print("\nCurrent Name :", member["name"])
    print("Current Phone:", member["phone"])
    print("Current Email:", member["email"])

    name = input(
        "\nNew name (Enter to keep old): "
    ).strip()

    if name:
        member["name"] = name

    while True:

        phone = input(
            "New phone (Enter to keep old): "
        ).strip()

        if phone == "":
            break

        if not valid_phone(phone):

            print("Invalid phone number.")

            continue

        duplicate = False

        for other in members:

            if (
                other != member
                and other.get("phone") == phone
            ):
                duplicate = True
                break

        if duplicate:

            print("Phone number already belongs to another member.")

            continue

        member["phone"] = phone

        break

    while True:

        email = input(
            "New email (Enter to keep old): "
        ).strip()

        if email == "":
            break

        if not valid_email(email):

            print("Invalid email.")

            continue

        duplicate = False

        for other in members:

            if (
                other != member
                and other.get("email", "").lower()
                == email.lower()
            ):
                duplicate = True
                break

        if duplicate:

            print("Email already belongs to another member.")

            continue

        member["email"] = email

        break

    save_data(MEMBER_FILE, members)

    print("\nMember updated successfully!")


def toggle_member_status():

    print("\n========== MEMBER STATUS ==========")

    member_id = input("Enter member ID: ").strip()

    member = find_member(member_id)

    if not member:

        print("Member not found.")

        return

    current_status = member.get("active", True)

    member["active"] = not current_status

    save_data(MEMBER_FILE, members)

    print(
        "\nMember is now:",
        "Active" if member["active"] else "Inactive"
    )


def remove_member():

    print("\n========== REMOVE MEMBER ==========")

    member_id = input("Enter member ID: ").strip()

    member = find_member(member_id)

    if not member:

        print("Member not found.")

        return

    # Check active loans
    for transaction in transactions:

        if (
            transaction.get("member_id", "").lower()
            == member_id.lower()
            and transaction.get("status") == "Issued"
        ):

            print("\nCannot remove member.")

            print(
                "Member currently has an issued book."
            )

            return

    confirmation = input(
        f"Remove member '{member['name']}'? (y/n): "
    ).strip().lower()

    if confirmation == "y":

        members.remove(member)

        save_data(MEMBER_FILE, members)

        print("\nMember removed successfully.")

    else:

        print("Operation cancelled.")


# ============================================================
# ISSUE BOOK
# ============================================================

def issue_book():

    print("\n========== ISSUE BOOK ==========")

    book_id = input("Enter book ID: ").strip()
    member_id = input("Enter member ID: ").strip()

    book = find_book(book_id)
    member = find_member(member_id)

    if not book:

        print("Book not found.")

        return

    if not member:

        print("Member not found.")

        return

    if not member.get("active", True):

        print("This member is inactive.")

        return

    if book["available"] <= 0:

        print("No copies currently available.")

        return

    # Count active loans
    active_loans = 0

    for transaction in transactions:

        if (
            transaction.get("member_id", "").lower()
            == member_id.lower()
            and transaction.get("status") == "Issued"
        ):
            active_loans += 1

    if active_loans >= MAX_BOOKS_PER_MEMBER:

        print(
            f"\nMember has reached the maximum limit "
            f"of {MAX_BOOKS_PER_MEMBER} books."
        )

        return

    # Check duplicate current book
    for transaction in transactions:

        if (
            transaction.get("book_id", "").lower()
            == book_id.lower()
            and transaction.get("member_id", "").lower()
            == member_id.lower()
            and transaction.get("status") == "Issued"
        ):

            print(
                "This member already has this book."
            )

            return

    transaction_id = generate_id(
        "T",
        transactions,
        "transaction_id"
    )

    issue_date = today()

    due_date = issue_date + timedelta(
        days=LOAN_DAYS
    )

    transaction = {
        "transaction_id": transaction_id,
        "book_id": book["book_id"],
        "member_id": member["member_id"],
        "issue_date": str(issue_date),
        "due_date": str(due_date),
        "return_date": "",
        "fine": 0,
        "status": "Issued"
    }

    transactions.append(transaction)

    book["available"] -= 1

    save_data(BOOK_FILE, books)
    save_data(TRANSACTION_FILE, transactions)

    print("\nBook issued successfully!")

    print("Transaction ID:", transaction_id)
    print("Book         :", book["title"])
    print("Member       :", member["name"])
    print("Issue Date   :", issue_date)
    print("Due Date     :", due_date)


# ============================================================
# RETURN BOOK
# ============================================================

def return_book():

    print("\n========== RETURN BOOK ==========")

    transaction_id = input(
        "Enter transaction ID: "
    ).strip()

    transaction = find_transaction(transaction_id)

    if not transaction:

        print("Transaction not found.")

        return

    if transaction.get("status") == "Returned":

        print("This book has already been returned.")

        return

    book = find_book(transaction["book_id"])

    return_date = today()

    due_date = datetime.strptime(
        transaction["due_date"],
        "%Y-%m-%d"
    ).date()

    overdue_days = (
        return_date - due_date
    ).days

    if overdue_days > 0:

        fine = overdue_days * FINE_PER_DAY

    else:

        overdue_days = 0
        fine = 0

    transaction["return_date"] = str(return_date)
    transaction["fine"] = fine
    transaction["status"] = "Returned"

    if book:

        book["available"] += 1

        if book["available"] > book["quantity"]:
            book["available"] = book["quantity"]

    save_data(BOOK_FILE, books)
    save_data(TRANSACTION_FILE, transactions)

    print("\nBook returned successfully!")

    print("Return Date  :", return_date)
    print("Overdue Days :", overdue_days)
    print("Fine         : ₹", fine)


# ============================================================
# TRANSACTION HISTORY
# ============================================================

def display_transactions():

    print(
        "\n================ TRANSACTION HISTORY ================"
    )

    if not transactions:

        print("No transactions found.")

        return

    for transaction in transactions:

        book = find_book(transaction["book_id"])
        member = find_member(transaction["member_id"])

        book_title = (
            book["title"]
            if book
            else "Book Removed"
        )

        member_name = (
            member["name"]
            if member
            else "Member Removed"
        )

        print("\n---------------------------------------------")

        print(
            "Transaction ID :",
            transaction["transaction_id"]
        )

        print("Book           :", book_title)
        print("Member         :", member_name)
        print("Issue Date     :", transaction["issue_date"])
        print("Due Date       :", transaction["due_date"])

        print(
            "Return Date    :",
            transaction["return_date"]
            if transaction["return_date"]
            else "Not Returned"
        )

        print("Fine           : ₹", transaction["fine"])
        print("Status         :", transaction["status"])


def search_transaction():

    print("\n========== SEARCH TRANSACTION ==========")

    keyword = input(
        "Enter transaction ID, member ID or book ID: "
    ).strip().lower()

    if not keyword:

        print("Search value cannot be empty.")

        return

    results = []

    for transaction in transactions:

        if (
            keyword in transaction.get(
                "transaction_id", ""
            ).lower()
            or keyword in transaction.get(
                "member_id", ""
            ).lower()
            or keyword in transaction.get(
                "book_id", ""
            ).lower()
        ):

            results.append(transaction)

    if not results:

        print("No transaction found.")

        return

    for transaction in results:

        book = find_book(transaction["book_id"])
        member = find_member(transaction["member_id"])

        print("\n--------------------------------")

        print(
            "Transaction:",
            transaction["transaction_id"]
        )

        print(
            "Book:",
            book["title"] if book else "Removed"
        )

        print(
            "Member:",
            member["name"] if member else "Removed"
        )

        print("Issue:", transaction["issue_date"])
        print("Due:", transaction["due_date"])

        print(
            "Return:",
            transaction["return_date"]
            or "Not Returned"
        )

        print("Fine: ₹", transaction["fine"])
        print("Status:", transaction["status"])


# ============================================================
# CURRENTLY ISSUED BOOKS
# ============================================================

def issued_books():

    print("\n========== CURRENTLY ISSUED BOOKS ==========")

    issued = [
        transaction
        for transaction in transactions
        if transaction.get("status") == "Issued"
    ]

    if not issued:

        print("No books are currently issued.")

        return

    for transaction in issued:

        book = find_book(transaction["book_id"])
        member = find_member(transaction["member_id"])

        print("\n-------------------------------------")

        print(
            "Transaction ID :",
            transaction["transaction_id"]
        )

        print(
            "Book           :",
            book["title"] if book else "Unknown"
        )

        print(
            "Member         :",
            member["name"] if member else "Unknown"
        )

        print("Issue Date     :", transaction["issue_date"])
        print("Due Date       :", transaction["due_date"])

        due = datetime.strptime(
            transaction["due_date"],
            "%Y-%m-%d"
        ).date()

        overdue = (today() - due).days

        if overdue > 0:

            print("Status         : OVERDUE")

            print(
                "Current Fine   : ₹",
                overdue * FINE_PER_DAY
            )

        else:

            remaining = (due - today()).days

            print("Status         : On Time")

            print(
                "Days Remaining :",
                remaining
            )


# ============================================================
# OVERDUE BOOKS
# ============================================================

def overdue_books():

    print("\n========== OVERDUE BOOKS ==========")

    found = False

    for transaction in transactions:

        if transaction.get("status") != "Issued":
            continue

        due_date = datetime.strptime(
            transaction["due_date"],
            "%Y-%m-%d"
        ).date()

        overdue_days = (
            today() - due_date
        ).days

        if overdue_days <= 0:
            continue

        found = True

        book = find_book(transaction["book_id"])
        member = find_member(transaction["member_id"])

        current_fine = (
            overdue_days * FINE_PER_DAY
        )

        print("\n-------------------------------------")

        print(
            "Transaction :",
            transaction["transaction_id"]
        )

        print(
            "Book        :",
            book["title"] if book else "Unknown"
        )

        print(
            "Member      :",
            member["name"] if member else "Unknown"
        )

        print("Due Date    :", due_date)
        print("Overdue     :", overdue_days, "days")
        print("Current Fine: ₹", current_fine)

    if not found:

        print("No overdue books.")


# ============================================================
# MEMBER CURRENT BOOKS
# ============================================================

def member_books():

    print("\n========== MEMBER BORROWED BOOKS ==========")

    member_id = input(
        "Enter member ID: "
    ).strip()

    member = find_member(member_id)

    if not member:

        print("Member not found.")

        return

    found = False

    for transaction in transactions:

        if (
            transaction.get("member_id", "").lower()
            == member_id.lower()
            and transaction.get("status") == "Issued"
        ):

            found = True

            book = find_book(transaction["book_id"])

            print("\n--------------------------------")

            print(
                "Book:",
                book["title"] if book else "Unknown"
            )

            print(
                "Transaction:",
                transaction["transaction_id"]
            )

            print(
                "Issue Date:",
                transaction["issue_date"]
            )

            print(
                "Due Date:",
                transaction["due_date"]
            )

    if not found:

        print("This member has no currently issued books.")


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    print("\n")
    print("=" * 60)
    print("                 LIBRARY DASHBOARD")
    print("=" * 60)

    total_titles = len(books)

    total_copies = sum(
        book.get("quantity", 0)
        for book in books
    )

    available_copies = sum(
        book.get("available", 0)
        for book in books
    )

    issued_copies = (
        total_copies - available_copies
    )

    total_members = len(members)

    active_members = sum(
        1
        for member in members
        if member.get("active", True)
    )

    total_transactions = len(transactions)

    returned_books = sum(
        1
        for transaction in transactions
        if transaction.get("status") == "Returned"
    )

    current_issued = sum(
        1
        for transaction in transactions
        if transaction.get("status") == "Issued"
    )

    overdue_count = 0
    current_fine = 0

    for transaction in transactions:

        if transaction.get("status") != "Issued":
            continue

        due_date = datetime.strptime(
            transaction["due_date"],
            "%Y-%m-%d"
        ).date()

        overdue = (today() - due_date).days

        if overdue > 0:

            overdue_count += 1

            current_fine += (
                overdue * FINE_PER_DAY
            )

    collected_fine = sum(
        transaction.get("fine", 0)
        for transaction in transactions
        if transaction.get("status") == "Returned"
    )

    print("\nBooks")
    print("-------------------------")
    print("Total Titles      :", total_titles)
    print("Total Copies      :", total_copies)
    print("Available Copies  :", available_copies)
    print("Issued Copies     :", issued_copies)

    print("\nMembers")
    print("-------------------------")
    print("Total Members     :", total_members)
    print("Active Members    :", active_members)

    print("\nTransactions")
    print("-------------------------")
    print("Total Transactions:", total_transactions)
    print("Returned Books    :", returned_books)
    print("Currently Issued  :", current_issued)
    print("Overdue Books     :", overdue_count)

    print("\nFine")
    print("-------------------------")
    print("Current Fine      : ₹", current_fine)
    print("Collected Fine    : ₹", collected_fine)

    print("=" * 60)


# ============================================================
# BOOK MENU
# ============================================================

def book_menu():

    while True:

        print("\n")
        print("======================================")
        print("           BOOK MANAGEMENT")
        print("======================================")
        print("1. Add Book")
        print("2. Display All Books")
        print("3. Search Book")
        print("4. Update Book")
        print("5. Remove Book")
        print("6. Back to Main Menu")
        print("======================================")

        choice = input("Enter your choice: ").strip()

        if choice == "1":

            add_book()
            pause()

        elif choice == "2":

            display_books()
            pause()

        elif choice == "3":

            search_book()
            pause()

        elif choice == "4":

            update_book()
            pause()

        elif choice == "5":

            remove_book()
            pause()

        elif choice == "6":

            break

        else:

            print("Invalid choice.")


# ============================================================
# MEMBER MENU
# ============================================================

def member_menu():

    while True:

        print("\n")
        print("======================================")
        print("          MEMBER MANAGEMENT")
        print("======================================")
        print("1. Register Member")
        print("2. Display All Members")
        print("3. Search Member")
        print("4. Update Member")
        print("5. Activate/Deactivate Member")
        print("6. Remove Member")
        print("7. View Member Books")
        print("8. Back to Main Menu")
        print("======================================")

        choice = input("Enter your choice: ").strip()

        if choice == "1":

            register_member()
            pause()

        elif choice == "2":

            display_members()
            pause()

        elif choice == "3":

            search_member()
            pause()

        elif choice == "4":

            update_member()
            pause()

        elif choice == "5":

            toggle_member_status()
            pause()

        elif choice == "6":

            remove_member()
            pause()

        elif choice == "7":

            member_books()
            pause()

        elif choice == "8":

            break

        else:

            print("Invalid choice.")


# ============================================================
# TRANSACTION MENU
# ============================================================

def transaction_menu():

    while True:

        print("\n")
        print("======================================")
        print("         TRANSACTION MANAGEMENT")
        print("======================================")
        print("1. Issue Book")
        print("2. Return Book")
        print("3. Transaction History")
        print("4. Search Transaction")
        print("5. Currently Issued Books")
        print("6. Overdue Books")
        print("7. Back to Main Menu")
        print("======================================")

        choice = input("Enter your choice: ").strip()

        if choice == "1":

            issue_book()
            pause()

        elif choice == "2":

            return_book()
            pause()

        elif choice == "3":

            display_transactions()
            pause()

        elif choice == "4":

            search_transaction()
            pause()

        elif choice == "5":

            issued_books()
            pause()

        elif choice == "6":

            overdue_books()
            pause()

        elif choice == "7":

            break

        else:

            print("Invalid choice.")


# ============================================================
# MAIN MENU
# ============================================================

def main():

    if not login():
        return

    while True:

        clear_screen()

        print("=" * 60)
        print("           LIBRARY MANAGEMENT SYSTEM")
        print("=" * 60)

        print("1.  Dashboard")
        print("2.  Book Management")
        print("3.  Member Management")
        print("4.  Transaction Management")
        print("5.  Display All Books")
        print("6.  Display All Members")
        print("7.  Overdue Books")
        print("8.  Logout / Exit")

        print("=" * 60)

        choice = input(
            "Enter your choice: "
        ).strip()

        if choice == "1":

            dashboard()
            pause()

        elif choice == "2":

            book_menu()

        elif choice == "3":

            member_menu()

        elif choice == "4":

            transaction_menu()

        elif choice == "5":

            display_books()
            pause()

        elif choice == "6":

            display_members()
            pause()

        elif choice == "7":

            overdue_books()
            pause()

        elif choice == "8":

            print("\nThank you for using")
            print("Library Management System!")
            print("Goodbye!")

            break

        else:

            print("\nInvalid choice.")

            pause()


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":
    main()