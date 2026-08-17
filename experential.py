import json
import os
from datetime import datetime, timedelta


# ============================================================
# FILE NAMES
# ============================================================

BOOK_FILE = "books.json"
MEMBER_FILE = "members.json"
TRANSACTION_FILE = "transactions.json"

FINE_PER_DAY = 5
LOAN_DAYS = 14


# ============================================================
# FILE HANDLING FUNCTIONS
# ============================================================

def load_data(filename):
    """Load data from JSON file."""
    if not os.path.exists(filename):
        return []

    try:
        with open(filename, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_data(filename, data):
    """Save data to JSON file."""
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)


# ============================================================
# LOAD DATA
# ============================================================

books = load_data(BOOK_FILE)
members = load_data(MEMBER_FILE)
transactions = load_data(TRANSACTION_FILE)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def pause():
    input("\nPress Enter to continue...")


def generate_id(prefix, data, key):
    """Generate a new ID."""
    numbers = []

    for item in data:
        value = item.get(key, "")

        if value.startswith(prefix):
            try:
                numbers.append(int(value[len(prefix):]))
            except ValueError:
                pass

    if numbers:
        new_number = max(numbers) + 1
    else:
        new_number = 1

    return f"{prefix}{new_number:03d}"


def find_book(book_id):
    for book in books:
        if book["book_id"].lower() == book_id.lower():
            return book
    return None


def find_member(member_id):
    for member in members:
        if member["member_id"].lower() == member_id.lower():
            return member
    return None


# ============================================================
# BOOK MANAGEMENT
# ============================================================

def add_book():
    print("\n========== ADD BOOK ==========")

    title = input("Enter book title: ").strip()
    author = input("Enter author name: ").strip()

    if not title or not author:
        print("Title and author cannot be empty.")
        return

    while True:
        try:
            quantity = int(input("Enter quantity: "))

            if quantity <= 0:
                print("Quantity must be greater than 0.")
                continue

            break

        except ValueError:
            print("Please enter a valid number.")

    # Check whether book already exists
    for book in books:
        if (book["title"].lower() == title.lower()
                and book["author"].lower() == author.lower()):

            book["quantity"] += quantity
            book["available"] += quantity

            save_data(BOOK_FILE, books)

            print("\nExisting book found.")
            print("Quantity updated successfully.")
            return

    book_id = generate_id("B", books, "book_id")

    new_book = {
        "book_id": book_id,
        "title": title,
        "author": author,
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
        f"{'Title':<30}"
        f"{'Author':<25}"
        f"{'Total':<10}"
        f"{'Available':<10}"
    )

    print("-" * 83)

    for book in books:
        print(
            f"{book['book_id']:<8}"
            f"{book['title'][:28]:<30}"
            f"{book['author'][:23]:<25}"
            f"{book['quantity']:<10}"
            f"{book['available']:<10}"
        )


def search_book():
    print("\n========== SEARCH BOOK ==========")

    keyword = input("Enter book ID, title or author: ").strip().lower()

    if not keyword:
        print("Search value cannot be empty.")
        return

    results = []

    for book in books:
        if (
            keyword in book["book_id"].lower()
            or keyword in book["title"].lower()
            or keyword in book["author"].lower()
        ):
            results.append(book)

    if not results:
        print("\nNo matching book found.")
        return

    print("\nSearch Results:")
    print("-" * 80)

    for book in results:
        print("Book ID     :", book["book_id"])
        print("Title       :", book["title"])
        print("Author      :", book["author"])
        print("Total       :", book["quantity"])
        print("Available   :", book["available"])
        print("-" * 80)


def update_book():
    print("\n========== UPDATE BOOK ==========")

    book_id = input("Enter book ID to update: ").strip()

    book = find_book(book_id)

    if not book:
        print("Book not found.")
        return

    print("\nCurrent Details:")
    print("Title:", book["title"])
    print("Author:", book["author"])
    print("Quantity:", book["quantity"])

    new_title = input("\nEnter new title (press Enter to keep old): ").strip()
    new_author = input("Enter new author (press Enter to keep old): ").strip()

    if new_title:
        book["title"] = new_title

    if new_author:
        book["author"] = new_author

    while True:
        new_quantity = input(
            "Enter new total quantity (press Enter to keep old): "
        ).strip()

        if new_quantity == "":
            break

        try:
            new_quantity = int(new_quantity)

            if new_quantity < 0:
                print("Quantity cannot be negative.")
                continue

            issued = book["quantity"] - book["available"]

            if new_quantity < issued:
                print(
                    f"Cannot set quantity below {issued}. "
                    "Some books are currently issued."
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

    book_id = input("Enter book ID to remove: ").strip()

    book = find_book(book_id)

    if not book:
        print("Book not found.")
        return

    if book["available"] != book["quantity"]:
        print("Cannot remove this book.")
        print("Some copies are currently issued.")
        return

    confirmation = input(
        f"Are you sure you want to remove '{book['title']}'? (y/n): "
    ).lower()

    if confirmation == "y":
        books.remove(book)
        save_data(BOOK_FILE, books)
        print("Book removed successfully.")
    else:
        print("Operation cancelled.")


# ============================================================
# MEMBER MANAGEMENT
# ============================================================

def register_member():
    print("\n========== REGISTER MEMBER ==========")

    name = input("Enter member name: ").strip()
    phone = input("Enter phone number: ").strip()
    email = input("Enter email: ").strip()

    if not name:
        print("Member name cannot be empty.")
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
        f"{'Phone':<18}"
        f"{'Email':<30}"
        f"{'Status':<10}"
    )

    print("-" * 93)

    for member in members:
        status = "Active" if member["active"] else "Inactive"

        print(
            f"{member['member_id']:<10}"
            f"{member['name'][:23]:<25}"
            f"{member['phone'][:16]:<18}"
            f"{member['email'][:28]:<30}"
            f"{status:<10}"
        )


def search_member():
    print("\n========== SEARCH MEMBER ==========")

    keyword = input(
        "Enter member ID, name, phone or email: "
    ).strip().lower()

    results = []

    for member in members:
        if (
            keyword in member["member_id"].lower()
            or keyword in member["name"].lower()
            or keyword in member["phone"].lower()
            or keyword in member["email"].lower()
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
            "Active" if member["active"] else "Inactive"
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

    name = input("\nEnter new name (Enter to keep old): ").strip()
    phone = input("Enter new phone (Enter to keep old): ").strip()
    email = input("Enter new email (Enter to keep old): ").strip()

    if name:
        member["name"] = name

    if phone:
        member["phone"] = phone

    if email:
        member["email"] = email

    save_data(MEMBER_FILE, members)

    print("\nMember updated successfully!")


def remove_member():
    print("\n========== REMOVE MEMBER ==========")

    member_id = input("Enter member ID: ").strip()

    member = find_member(member_id)

    if not member:
        print("Member not found.")
        return

    # Check whether member has an active transaction
    for transaction in transactions:
        if (
            transaction["member_id"].lower() == member_id.lower()
            and transaction["status"] == "Issued"
        ):
            print("Cannot remove member.")
            print("Member currently has an issued book.")
            return

    confirmation = input(
        f"Remove member '{member['name']}'? (y/n): "
    ).lower()

    if confirmation == "y":
        members.remove(member)
        save_data(MEMBER_FILE, members)
        print("Member removed successfully.")
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

    if not member["active"]:
        print("This member is inactive.")
        return

    if book["available"] <= 0:
        print("No copies of this book are currently available.")
        return

    # Check if member already has this book
    for transaction in transactions:
        if (
            transaction["book_id"].lower() == book_id.lower()
            and transaction["member_id"].lower() == member_id.lower()
            and transaction["status"] == "Issued"
        ):
            print("This member already has this book.")
            return

    transaction_id = generate_id(
        "T",
        transactions,
        "transaction_id"
    )

    issue_date = datetime.now().date()
    due_date = issue_date + timedelta(days=LOAN_DAYS)

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
    print("Book:", book["title"])
    print("Member:", member["name"])
    print("Issue Date:", issue_date)
    print("Due Date:", due_date)


# ============================================================
# RETURN BOOK
# ============================================================

def return_book():
    print("\n========== RETURN BOOK ==========")

    transaction_id = input(
        "Enter transaction ID: "
    ).strip()

    transaction = None

    for item in transactions:
        if item["transaction_id"].lower() == transaction_id.lower():
            transaction = item
            break

    if not transaction:
        print("Transaction not found.")
        return

    if transaction["status"] == "Returned":
        print("This book has already been returned.")
        return

    book = find_book(transaction["book_id"])

    return_date = datetime.now().date()
    due_date = datetime.strptime(
        transaction["due_date"],
        "%Y-%m-%d"
    ).date()

    overdue_days = (return_date - due_date).days

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
    print("\n================ TRANSACTION HISTORY ================")

    if not transactions:
        print("No transactions found.")
        return

    for transaction in transactions:
        book = find_book(transaction["book_id"])
        member = find_member(transaction["member_id"])

        book_title = book["title"] if book else "Unknown"
        member_name = member["name"] if member else "Unknown"

        print("\n---------------------------------------------")
        print("Transaction ID :", transaction["transaction_id"])
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


# ============================================================
# CURRENTLY ISSUED BOOKS
# ============================================================

def issued_books():
    print("\n========== CURRENTLY ISSUED BOOKS ==========")

    issued = [
        transaction
        for transaction in transactions
        if transaction["status"] == "Issued"
    ]

    if not issued:
        print("No books are currently issued.")
        return

    for transaction in issued:
        book = find_book(transaction["book_id"])
        member = find_member(transaction["member_id"])

        print("\n-------------------------------------")
        print("Transaction ID :", transaction["transaction_id"])
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

        today = datetime.now().date()
        due = datetime.strptime(
            transaction["due_date"],
            "%Y-%m-%d"
        ).date()

        overdue = (today - due).days

        if overdue > 0:
            print("Status         : OVERDUE")
            print("Current Fine   : ₹", overdue * FINE_PER_DAY)
        else:
            print("Status         : On Time")


# ============================================================
# BOOK MENU
# ============================================================

def book_menu():

    while True:

        print("\n")
        print("======================================")
        print("          BOOK MANAGEMENT")
        print("======================================")
        print("1. Add Book")
        print("2. Display All Books")
        print("3. Search Book")
        print("4. Update Book")
        print("5. Remove Book")
        print("6. Back to Main Menu")
        print("======================================")

        choice = input("Enter your choice: ")

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
        print("         MEMBER MANAGEMENT")
        print("======================================")
        print("1. Register Member")
        print("2. Display All Members")
        print("3. Search Member")
        print("4. Update Member")
        print("5. Remove Member")
        print("6. Back to Main Menu")
        print("======================================")

        choice = input("Enter your choice: ")

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
            remove_member()
            pause()

        elif choice == "6":
            break

        else:
            print("Invalid choice.")


# ============================================================
# MAIN MENU
# ============================================================

def main():

    while True:

        print("\n")
        print("================================================")
        print("          LIBRARY MANAGEMENT SYSTEM")
        print("================================================")
        print("1.  Book Management")
        print("2.  Member Management")
        print("3.  Issue Book")
        print("4.  Return Book")
        print("5.  Transaction History")
        print("6.  Currently Issued Books")
        print("7.  Display All Books")
        print("8.  Display All Members")
        print("9.  Exit")
        print("================================================")

        choice = input("Enter your choice: ")

        if choice == "1":
            book_menu()

        elif choice == "2":
            member_menu()

        elif choice == "3":
            issue_book()
            pause()

        elif choice == "4":
            return_book()
            pause()

        elif choice == "5":
            display_transactions()
            pause()

        elif choice == "6":
            issued_books()
            pause()

        elif choice == "7":
            display_books()
            pause()

        elif choice == "8":
            display_members()
            pause()

        elif choice == "9":
            print("\nThank you for using Library Management System!")
            print("Goodbye!")
            break

        else:
            print("\nInvalid choice. Please try again.")


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":
    main()