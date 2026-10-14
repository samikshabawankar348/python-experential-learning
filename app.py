import json
import os
import re
from datetime import date, timedelta
from pathlib import Path
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Library Management System", page_icon="📚", layout="wide")
BASE_DIR = Path(__file__).resolve().parent
BOOK_FILE = BASE_DIR / "books.json"
MEMBER_FILE = BASE_DIR / "members.json"
TRANSACTION_FILE = BASE_DIR / "transactions.json"
RESERVATION_FILE = BASE_DIR / "reservations.json"
FINE_PER_DAY = 5
LOAN_DAYS = 14
MAX_BOOKS_PER_MEMBER = 3


def load_data(path):
    if not path.exists():
        save_data(path, [])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_data(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def next_id(prefix, rows, key):
    nums = [int(str(x.get(key, ""))[len(prefix):]) for x in rows
            if str(x.get(key, "")).startswith(prefix)
            and str(x.get(key, ""))[len(prefix):].isdigit()]
    return f"{prefix}{max(nums, default=0)+1:03d}"


def by_id(rows, key, value):
    return next((x for x in rows if str(x.get(key, "")).lower() == str(value).lower()), None)


def calculate_fine(tx, on_date=None):
    on_date = on_date or date.today()
    due = date.fromisoformat(tx["due_date"])
    end = date.fromisoformat(tx["return_date"]) if tx.get("return_date") else on_date
    days = max(0, (end - due).days)
    return days * FINE_PER_DAY, days


def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


# Set ADMIN_USERNAME and ADMIN_PASSWORD in Streamlit Cloud > App settings > Secrets.
ADMIN_USERNAME = get_secret("ADMIN_USERNAME")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD")

st.markdown("""
<style>
.main {background: #f7f9fc;}
.hero {padding: 1.2rem 1.5rem; border-radius: 16px; background: linear-gradient(120deg,#123b66,#2878a8); color: white; margin-bottom: 1rem;}
.hero h1 {color:white; margin:0;} .hero p {margin:.35rem 0 0 0; color:#eaf5ff;}
[data-testid="stMetric"] {background:white; padding:1rem; border:1px solid #e4eaf2; border-radius:12px;}
</style>
<div class="hero"><h1>📚 Library Management System</h1><p>Manage books, members, issue/return transactions and reservations.</p></div>
""", unsafe_allow_html=True)

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    st.warning("Admin login is not configured yet. On Streamlit Community Cloud, open your app's Settings → Secrets and add ADMIN_USERNAME and ADMIN_PASSWORD. For local testing, set these environment variables before starting the app.")
    st.code('ADMIN_USERNAME = "your_admin_name"\nADMIN_PASSWORD = "choose-a-strong-password"', language="toml")
    st.stop()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.subheader("Admin sign in")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
    if submitted:
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect username or password.")
    st.caption("For a class demo only. Do not enter real member information until secure authentication and persistent database storage are configured.")
    st.stop()

books = load_data(BOOK_FILE)
members = load_data(MEMBER_FILE)
transactions = load_data(TRANSACTION_FILE)
reservations = load_data(RESERVATION_FILE)

with st.sidebar:
    st.title("Navigation")
    page = st.radio("Choose a section", ["Dashboard", "Books", "Members", "Issue / Return", "Reservations", "Reports"])
    st.divider()
    st.caption("Demo system · Fine ₹5/day · Loan period 14 days")
    if st.button("Sign out"):
        st.session_state.authenticated = False
        st.rerun()

if page == "Dashboard":
    st.subheader("Dashboard overview")
    total_copies = sum(int(b.get("quantity", 0)) for b in books)
    available = sum(int(b.get("available", 0)) for b in books)
    issued = [t for t in transactions if t.get("status") == "Issued"]
    active_members = sum(1 for m in members if m.get("active", True))
    overdue = sum(1 for t in issued if calculate_fine(t)[1] > 0)
    pending_res = sum(1 for r in reservations if r.get("status") == "Pending")
    cols = st.columns(4)
    cols[0].metric("Book titles", len(books))
    cols[1].metric("Total copies", total_copies)
    cols[2].metric("Available copies", available)
    cols[3].metric("Currently issued", len(issued))
    cols = st.columns(4)
    cols[0].metric("Members", len(members))
    cols[1].metric("Active members", active_members)
    cols[2].metric("Overdue loans", overdue)
    cols[3].metric("Pending reservations", pending_res)
    if books:
        st.markdown("#### Book availability")
        st.dataframe(pd.DataFrame(books), use_container_width=True, hide_index=True)
    else:
        st.info("No books yet. Open Books → Add a book to get started.")

elif page == "Books":
    tab1, tab2 = st.tabs(["Book catalog", "Add / restock book"])
    with tab1:
        query = st.text_input("Search by ID, title, author, category or ISBN")
        found = [b for b in books if not query or any(query.lower() in str(b.get(k, "")).lower() for k in ("book_id","title","author","category","isbn"))]
        if found:
            st.dataframe(pd.DataFrame(found), use_container_width=True, hide_index=True)
        else:
            st.info("No matching books found.")
        with st.expander("Remove a book"):
            removable = [b for b in books if int(b.get("quantity",0)) == int(b.get("available",0))]
            if removable:
                selected = st.selectbox("Choose a book", removable, format_func=lambda b: f"{b.get('book_id')} — {b.get('title')}")
                if st.button("Remove selected book"):
                    books.remove(selected); save_data(BOOK_FILE, books); st.success("Book removed."); st.rerun()
            else:
                st.caption("Only books with no currently issued copies can be removed.")
    with tab2:
        with st.form("add_book_form"):
            title = st.text_input("Book title")
            author = st.text_input("Author")
            category = st.text_input("Category")
            isbn = st.text_input("ISBN")
            quantity = st.number_input("Copies to add", min_value=1, step=1)
            save_book = st.form_submit_button("Add book / restock", type="primary")
        if save_book:
            if not all(x.strip() for x in (title, author, category, isbn)):
                st.error("Please complete all fields.")
            else:
                existing = next((b for b in books if str(b.get("isbn","")).lower() == isbn.strip().lower()), None)
                if existing:
                    existing["quantity"] = int(existing.get("quantity",0)) + int(quantity)
                    existing["available"] = int(existing.get("available",0)) + int(quantity)
                    message = f"Restocked {existing['title']}."
                else:
                    book = {"book_id":next_id("B",books,"book_id"),"title":title.strip(),"author":author.strip(),"category":category.strip(),"isbn":isbn.strip(),"quantity":int(quantity),"available":int(quantity)}
                    books.append(book); message = f"Book added. ID: {book['book_id']}"
                save_data(BOOK_FILE, books); st.success(message); st.rerun()

elif page == "Members":
    tab1, tab2 = st.tabs(["Member directory", "Register member"])
    with tab1:
        query = st.text_input("Search by ID, name, phone or email")
        found = [m for m in members if not query or any(query.lower() in str(m.get(k,"")).lower() for k in ("member_id","name","phone","email"))]
        if found:
            display = [{**m, "status":"Active" if m.get("active",True) else "Inactive"} for m in found]
            st.dataframe(pd.DataFrame(display), use_container_width=True, hide_index=True)
        else:
            st.info("No members found.")
        with st.expander("Activate / deactivate a member"):
            if members:
                m = st.selectbox("Member", members, format_func=lambda x:f"{x.get('member_id')} — {x.get('name')}")
                if st.button("Toggle member status"):
                    m["active"] = not m.get("active", True); save_data(MEMBER_FILE,members); st.success("Member status updated."); st.rerun()
            else: st.caption("Register a member first.")
    with tab2:
        with st.form("member_form"):
            name = st.text_input("Full name")
            phone = st.text_input("10-digit Indian mobile number")
            email = st.text_input("Email address")
            save_member = st.form_submit_button("Register member", type="primary")
        if save_member:
            if not name.strip(): st.error("Name is required.")
            elif not re.fullmatch(r"[6-9]\d{9}", phone.strip()): st.error("Enter a valid 10-digit Indian mobile number.")
            elif not re.fullmatch(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email.strip()): st.error("Enter a valid email address.")
            elif any(m.get("phone")==phone.strip() or m.get("email","").lower()==email.strip().lower() for m in members): st.error("That phone number or email is already registered.")
            else:
                member={"member_id":next_id("M",members,"member_id"),"name":name.strip(),"phone":phone.strip(),"email":email.strip(),"active":True}
                members.append(member); save_data(MEMBER_FILE,members); st.success(f"Member registered. ID: {member['member_id']}"); st.rerun()

elif page == "Issue / Return":
    tab1, tab2, tab3 = st.tabs(["Issue a book", "Return a book", "Current loans / history"])
    with tab1:
        available_books = [b for b in books if int(b.get("available",0)) > 0]
        active_members_list = [m for m in members if m.get("active",True)]
        if not available_books or not active_members_list:
            st.info("You need at least one available book and one active member before issuing a book.")
        else:
            with st.form("issue_form"):
                book = st.selectbox("Book", available_books, format_func=lambda b:f"{b.get('book_id')} — {b.get('title')} ({b.get('available')} available)")
                member = st.selectbox("Member", active_members_list, format_func=lambda m:f"{m.get('member_id')} — {m.get('name')}")
                issue = st.form_submit_button("Issue book", type="primary")
            if issue:
                count = sum(1 for t in transactions if t.get("member_id")==member["member_id"] and t.get("status")=="Issued")
                duplicate = any(t.get("book_id")==book["book_id"] and t.get("member_id")==member["member_id"] and t.get("status")=="Issued" for t in transactions)
                if count >= MAX_BOOKS_PER_MEMBER: st.error(f"Member already has {MAX_BOOKS_PER_MEMBER} books issued.")
                elif duplicate: st.error("This member already has this book issued.")
                else:
                    now=date.today(); tx={"transaction_id":next_id("T",transactions,"transaction_id"),"book_id":book["book_id"],"member_id":member["member_id"],"issue_date":now.isoformat(),"due_date":(now+timedelta(days=LOAN_DAYS)).isoformat(),"return_date":"","fine":0,"fine_paid":False,"status":"Issued"}
                    transactions.append(tx); book["available"]-=1; save_data(BOOK_FILE,books); save_data(TRANSACTION_FILE,transactions); st.success(f"Issued successfully. Transaction ID: {tx['transaction_id']} · Due: {tx['due_date']}"); st.rerun()
    with tab2:
        outstanding = [t for t in transactions if t.get("status")=="Issued"]
        if outstanding:
            with st.form("return_form"):
                tx = st.selectbox("Issued transaction", outstanding, format_func=lambda t:f"{t.get('transaction_id')} — {by_id(books,'book_id',t.get('book_id'))['title'] if by_id(books,'book_id',t.get('book_id')) else t.get('book_id')} / {by_id(members,'member_id',t.get('member_id'))['name'] if by_id(members,'member_id',t.get('member_id')) else t.get('member_id')} (due {t.get('due_date')})")
                return_it = st.form_submit_button("Confirm return", type="primary")
            if return_it:
                fine, days = calculate_fine(tx); tx["return_date"]=date.today().isoformat(); tx["fine"]=fine; tx["fine_paid"]=(fine==0); tx["status"]="Returned"
                book=by_id(books,"book_id",tx.get("book_id"))
                if book: book["available"]=min(int(book.get("quantity",0)),int(book.get("available",0))+1)
                save_data(BOOK_FILE,books); save_data(TRANSACTION_FILE,transactions); st.success(f"Book returned. Overdue days: {days}. Fine: ₹{fine}." ); st.rerun()
        else: st.info("There are no currently issued books.")
    with tab3:
        if transactions:
            rows=[]
            for tx in transactions:
                b=by_id(books,"book_id",tx.get("book_id")) or {}; m=by_id(members,"member_id",tx.get("member_id")) or {}
                fine,days=calculate_fine(tx)
                rows.append({"Transaction ID":tx.get("transaction_id"),"Book":b.get("title",tx.get("book_id")),"Member":m.get("name",tx.get("member_id")),"Issue date":tx.get("issue_date"),"Due date":tx.get("due_date"),"Status":tx.get("status"),"Fine (₹)":tx.get("fine",fine if tx.get("status")=="Issued" else 0)})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else: st.info("No transactions yet.")

elif page == "Reservations":
    tab1, tab2 = st.tabs(["Create reservation", "Reservation list"])
    with tab1:
        active_members_list=[m for m in members if m.get("active",True)]
        if not books or not active_members_list: st.info("Add a book and register an active member first.")
        else:
            with st.form("reservation_form"):
                book=st.selectbox("Book",books,format_func=lambda b:f"{b.get('book_id')} — {b.get('title')}")
                member=st.selectbox("Member",active_members_list,format_func=lambda m:f"{m.get('member_id')} — {m.get('name')}")
                reserve=st.form_submit_button("Reserve book",type="primary")
            if reserve:
                duplicate=any(r.get("book_id")==book["book_id"] and r.get("member_id")==member["member_id"] and r.get("status")=="Pending" for r in reservations)
                if duplicate: st.error("This member already has a pending reservation for this book.")
                else:
                    r={"reservation_id":next_id("R",reservations,"reservation_id"),"book_id":book["book_id"],"member_id":member["member_id"],"reservation_date":date.today().isoformat(),"status":"Pending"}
                    reservations.append(r); save_data(RESERVATION_FILE,reservations); st.success(f"Reservation created: {r['reservation_id']}"); st.rerun()
    with tab2:
        if reservations:
            rows=[]
            for r in reservations:
                b=by_id(books,"book_id",r.get("book_id")) or {}; m=by_id(members,"member_id",r.get("member_id")) or {}
                rows.append({"Reservation ID":r.get("reservation_id"),"Book":b.get("title",r.get("book_id")),"Member":m.get("name",r.get("member_id")),"Date":r.get("reservation_date"),"Status":r.get("status")})
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            pending=[r for r in reservations if r.get("status")=="Pending"]
            if pending:
                selected=st.selectbox("Pending reservation",pending,format_func=lambda r:f"{r.get('reservation_id')} — {r.get('book_id')} / {r.get('member_id')}")
                if st.button("Cancel reservation"):
                    selected["status"]="Cancelled"; save_data(RESERVATION_FILE,reservations); st.success("Reservation cancelled."); st.rerun()
        else: st.info("No reservations yet.")

elif page == "Reports":
    st.subheader("Reports and data export")
    for label, data in [("Books",books),("Members",members),("Transactions",transactions),("Reservations",reservations)]:
        st.markdown(f"#### {label}")
        if data:
            df=pd.DataFrame(data)
            st.dataframe(df,use_container_width=True,hide_index=True)
            st.download_button(f"Download {label.lower()} CSV",df.to_csv(index=False).encode("utf-8-sig"),file_name=f"{label.lower()}.csv",mime="text/csv",key=f"download_{label}")
        else: st.caption(f"No {label.lower()} records yet.")

st.divider()
st.caption("Educational demo. For real deployment, use a persistent database and stronger authentication. Streamlit hosting may not preserve changes written to local JSON files after restarts or redeployments.")
