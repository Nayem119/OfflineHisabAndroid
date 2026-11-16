import os
import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

Window.clearcolor = get_color_from_hex("#f1f5f9")


class AmarHisabDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.seed_defaults()

    def create_tables(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                balance REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_code TEXT UNIQUE,
                name TEXT NOT NULL,
                mobile TEXT,
                status TEXT DEFAULT 'Active'
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trx_code TEXT UNIQUE,
                type TEXT NOT NULL,
                customer_id INTEGER,
                account_id INTEGER,
                category TEXT,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                notes TEXT
            );
            """
        )
        self.conn.commit()

    def seed_defaults(self):
        cnt = self.conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        if cnt == 0:
            self.conn.executemany(
                "INSERT INTO accounts (name, balance) VALUES (?, ?)",
                [
                    ("Cash in Hand", 0.0),
                    ("bKash", 0.0),
                    ("Nagad", 0.0),
                    ("Bank Account", 0.0),
                ],
            )
            self.conn.commit()

    def get_summary(self):
        liquid = self.conn.execute("SELECT COALESCE(SUM(balance), 0) FROM accounts").fetchone()[0]
        lg = self.conn.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='LOAN_GIVEN'").fetchone()[0]
        lr = self.conn.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='LOAN_RETURN'").fetchone()[0]
        di = self.conn.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='DEPOSIT_IN'").fetchone()[0]
        do = self.conn.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='DEPOSIT_OUT'").fetchone()[0]
        inc = self.conn.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='INCOME'").fetchone()[0]
        exp = self.conn.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='EXPENSE'").fetchone()[0]

        receivable = lg - lr
        deposit_due = di - do
        net_worth = (liquid + receivable) - deposit_due
        return {
            "liquid": liquid,
            "receivable": receivable,
            "deposit_due": deposit_due,
            "net_worth": net_worth,
            "income": inc,
            "expense": exp,
        }


class AmarHisabKivyApp(App):
    def build(self):
        self.title = "Amar Hisab"
        # Android internal storage path (/data/user/0/org.amarhisab/files/amar_hisab.db)
        db_dir = self.user_data_dir
        os.makedirs(db_dir, exist_ok=True)
        self.db = AmarHisabDB(os.path.join(db_dir, "amar_hisab.db"))

        self.root_layout = BoxLayout(orientation="vertical")

        # Top Header
        header = BoxLayout(size_hint_y=None, height=56, padding=[15, 10])
        header.add_widget(
            Label(
                text="[b]Amar Hisab (Offline SQLite)[/b]",
                markup=True,
                font_size="18sp",
                color=get_color_from_hex("#065f46"),
                halign="left",
            )
        )
        self.root_layout.add_widget(header)

        # Dynamic Main Body
        self.body = BoxLayout(orientation="vertical", padding=10)
        self.root_layout.add_widget(self.body)

        # Bottom Navigation
        nav = GridLayout(cols=4, size_hint_y=None, height=56, spacing=2)
        for label, callback in [
            ("Home", self.show_home),
            ("Customers", self.show_customers),
            ("+ Entry", self.open_trx_popup),
            ("DB Info", self.show_db_info),
        ]:
            btn = Button(
                text=label,
                background_normal="",
                background_color=get_color_from_hex("#059669"),
                color=(1, 1, 1, 1),
                bold=True,
            )
            btn.bind(on_release=lambda inst, cb=callback: cb())
            nav.add_widget(btn)

        self.root_layout.add_widget(nav)
        self.show_home()
        return self.root_layout

    def show_home(self):
        self.body.clear_widgets()
        s = self.db.get_summary()

        scroll = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=10)
        box.bind(minimum_height=box.setter("height"))

        cards = [
            ("Total Cash & Accounts", f"BDT {s['liquid']:,.0f}", "#059669"),
            ("Own Net Worth", f"BDT {s['net_worth']:,.0f}", "#0284c7"),
            ("Loan Receivable (Pawna)", f"BDT {s['receivable']:,.0f}", "#e11d48"),
            ("Customer Deposits (Liability)", f"BDT {s['deposit_due']:,.0f}", "#d97706"),
            ("Total Income", f"BDT {s['income']:,.0f}", "#10b981"),
            ("Total Expense", f"BDT {s['expense']:,.0f}", "#be123c"),
        ]

        for title, val, hex_col in cards:
            card = Button(
                text=f"{title}\n[b]{val}[/b]",
                markup=True,
                size_hint_y=None,
                height=75,
                background_normal="",
                background_color=get_color_from_hex(hex_col),
                color=(1, 1, 1, 1),
                font_size="15sp",
            )
            box.add_widget(card)

        scroll.add_widget(box)
        self.body.add_widget(scroll)

    def show_customers(self):
        self.body.clear_widgets()
        add_btn = Button(
            text="+ Add New Customer",
            size_hint_y=None,
            height=48,
            background_normal="",
            background_color=get_color_from_hex("#059669"),
            bold=True,
        )
        add_btn.bind(on_release=lambda x: self.open_add_customer())
        self.body.add_widget(add_btn)

        scroll = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=8, padding=[0, 10])
        box.bind(minimum_height=box.setter("height"))

        rows = self.db.conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
        for c in rows:
            lbl = Button(
                text=f"{c['name']} ({c['customer_code']}) - {c['mobile'] or 'No Mobile'}",
                size_hint_y=None,
                height=52,
                background_normal="",
                background_color=(1, 1, 1, 1),
                color=(0.1, 0.1, 0.1, 1),
            )
            box.add_widget(lbl)

        scroll.add_widget(box)
        self.body.add_widget(scroll)

    def open_add_customer(self):
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        name_in = TextInput(hint_text="Customer Name", multiline=False, size_hint_y=None, height=44)
        mob_in = TextInput(hint_text="Mobile Number", multiline=False, size_hint_y=None, height=44)
        save_btn = Button(text="Save Customer", size_hint_y=None, height=48, background_color=get_color_from_hex("#059669"))

        content.add_widget(name_in)
        content.add_widget(mob_in)
        content.add_widget(save_btn)
        popup = Popup(title="New Customer", content=content, size_hint=(0.9, 0.45))

        def save(inst):
            if name_in.text.strip():
                cnt = self.db.conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
                code = f"CUS-{1001 + cnt}"
                self.db.conn.execute(
                    "INSERT INTO customers (customer_code, name, mobile) VALUES (?, ?, ?)",
                    (code, name_in.text.strip(), mob_in.text.strip()),
                )
                self.db.conn.commit()
                popup.dismiss()
                self.show_customers()

        save_btn.bind(on_release=save)
        popup.open()

    def open_trx_popup(self):
        content = BoxLayout(orientation="vertical", spacing=8, padding=10)
        type_sp = Spinner(
            text="LOAN_GIVEN",
            values=("LOAN_GIVEN", "LOAN_RETURN", "DEPOSIT_IN", "DEPOSIT_OUT", "INCOME", "EXPENSE"),
            size_hint_y=None,
            height=44,
        )

        customers = self.db.conn.execute("SELECT id, name FROM customers").fetchall()
        cust_map = {c["name"]: c["id"] for c in customers}
        cust_sp = Spinner(
            text=list(cust_map.keys())[0] if cust_map else "No Customer",
            values=list(cust_map.keys()) if cust_map else ["No Customer"],
            size_hint_y=None,
            height=44,
        )

        accounts = self.db.conn.execute("SELECT id, name FROM accounts").fetchall()
        acc_map = {a["name"]: a["id"] for a in accounts}
        acc_sp = Spinner(text="Cash in Hand", values=list(acc_map.keys()), size_hint_y=None, height=44)

        amt_in = TextInput(hint_text="Amount (BDT)", input_filter="float", multiline=False, size_hint_y=None, height=44)
        save_btn = Button(text="Save Transaction", size_hint_y=None, height=48, background_color=get_color_from_hex("#059669"))

        for w in [type_sp, cust_sp, acc_sp, amt_in, save_btn]:
            content.add_widget(w)

        popup = Popup(title="New Entry", content=content, size_hint=(0.92, 0.65))

        def save_trx(inst):
            try:
                amt = float(amt_in.text.strip())
                if amt <= 0:
                    return
            except ValueError:
                return

            t_type = type_sp.text
            cid = cust_map.get(cust_sp.text)
            aid = acc_map.get(acc_sp.text, 1)
            cnt = self.db.conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
            code = f"TRX-{1001 + cnt}"
            today = datetime.now().strftime("%Y-%m-%d")

            self.db.conn.execute(
                "INSERT INTO transactions (trx_code, type, customer_id, account_id, amount, date) VALUES (?, ?, ?, ?, ?, ?)",
                (code, t_type, cid, aid, amt, today),
            )
            is_out = t_type in ("LOAN_GIVEN", "DEPOSIT_OUT", "EXPENSE")
            self.db.conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (-amt if is_out else amt, aid))
            self.db.conn.commit()
            popup.dismiss()
            self.show_home()

        save_btn.bind(on_release=save_trx)
        popup.open()

    def show_db_info(self):
        self.body.clear_widgets()
        lbl = Label(
            text=f"[b]SQLite Database Location on Phone:[/b]\n\n{self.db.db_path}",
            markup=True,
            color=(0.1, 0.1, 0.1, 1),
            halign="center",
        )
        self.body.add_widget(lbl)


if __name__ == "__main__":
    AmarHisabKivyApp().run()