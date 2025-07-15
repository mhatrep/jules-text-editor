import tkinter as tk
from tkinter import ttk, messagebox
from faker import Faker
import json
import xml.etree.ElementTree as ET
import random
from decimal import Decimal
from datetime import date

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (Decimal, date)):
            return str(obj)
        return super().default(obj)

class FakeDataGeneratorDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master.root)
        self.title("Fake Data Generator")
        self.geometry("600x400")
        self.master_app = master
        self.fake = Faker()

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Options ---
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=5)

        ttk.Label(options_frame, text="File Type:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_type_var = tk.StringVar()
        self.file_type_combo = ttk.Combobox(options_frame, textvariable=self.file_type_var,
                                              values=[".txt", ".csv", ".json", ".xml", ".ini", ".yaml", ".log", ".sql", ".html", ".md"],
                                              state="readonly")
        self.file_type_combo.pack(side=tk.LEFT, padx=5)
        self.file_type_combo.current(0)
        self.file_type_combo.bind("<<ComboboxSelected>>", self.update_subtypes)

        ttk.Label(options_frame, text="Subtype:").pack(side=tk.LEFT, padx=(10, 5))
        self.subtype_var = tk.StringVar()
        self.subtype_combo = ttk.Combobox(options_frame, textvariable=self.subtype_var, state="readonly")
        self.subtype_combo.pack(side=tk.LEFT, padx=5)
        self.update_subtypes()

        ttk.Label(options_frame, text="Records:").pack(side=tk.LEFT, padx=(10, 5))
        self.records_var = tk.StringVar(value="10")
        self.records_entry = ttk.Entry(options_frame, textvariable=self.records_var, width=10)
        self.records_entry.pack(side=tk.LEFT, padx=5)

        self.generate_button = ttk.Button(options_frame, text="Generate", command=self.generate_data)
        self.generate_button.pack(side=tk.LEFT, padx=10)

        # --- Output ---
        output_frame = ttk.LabelFrame(main_frame, text="Generated Data", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.output_text = tk.Text(output_frame, wrap=tk.WORD, height=10)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)

        output_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=5)

        self.copy_button = ttk.Button(action_frame, text="Copy to Clipboard", command=self._copy_to_clipboard)
        self.copy_button.pack(side=tk.RIGHT, padx=(0, 5))

        self.save_button = ttk.Button(action_frame, text="Save to File...", command=self._save_to_file)
        self.save_button.pack(side=tk.RIGHT)
        self.output_text.config(yscrollcommand=output_scrollbar.set)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", self.on_close)

    def generate_data(self):
        file_type = self.file_type_var.get()
        try:
            num_records = int(self.records_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for records.", parent=self)
            return

        generated_text = ""
        subtype = self.subtype_var.get()
        if file_type == ".txt":
            generated_text = self._generate_txt(num_records, subtype)
        elif file_type == ".csv":
            generated_text = self._generate_csv(num_records, subtype)
        elif file_type == ".json":
            generated_text = self._generate_json(num_records, subtype)
        elif file_type == ".xml":
            generated_text = self._generate_xml(num_records)
        elif file_type == ".ini":
            generated_text = self._generate_ini(num_records)
        elif file_type == ".yaml":
            generated_text = self._generate_yaml(num_records)
        elif file_type == ".log":
            generated_text = self._generate_log(num_records)
        elif file_type == ".sql":
            generated_text = self._generate_sql(num_records, subtype)
        elif file_type == ".html":
            generated_text = self._generate_html(num_records)
        elif file_type == ".md":
            generated_text = self._generate_md(num_records)

        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, generated_text)
        self.output_text.config(state=tk.DISABLED)

    def _generate_txt(self, num_records, subtype):
        if subtype == "User Profiles":
            return "\n\n".join([self.fake.profile_str() for _ in range(num_records)])
        elif subtype == "Log Entries":
            return self._generate_log(num_records)
        else: # Paragraphs
            return "\n\n".join([self.fake.paragraph(nb_sentences=5) for _ in range(num_records)])

    def _generate_csv(self, num_records, subtype):
        if subtype == "Product List":
            header = "product_name,price,company\n"
            rows = [f"{self.fake.catch_phrase()},{self.fake.random_number(digits=2)}.{self.fake.random_number(digits=2)},{self.fake.company()}" for _ in range(num_records)]
            return header + "\n".join(rows)
        elif subtype == "Order History":
            header = "order_id,product_id,customer_id,order_date\n"
            rows = [f"{self.fake.uuid4()},{self.fake.random_int(min=100, max=999)},{self.fake.random_int(min=1000, max=9999)},{self.fake.date_this_year()}" for _ in range(num_records)]
            return header + "\n".join(rows)
        else: # User Data
            header = "name,email,job,date_of_birth\n"
            rows = [f"{self.fake.name()},{self.fake.email()},{self.fake.job()},{self.fake.date_of_birth()}" for _ in range(num_records)]
            return header + "\n".join(rows)

    def _generate_json(self, num_records, subtype):
        if subtype == "Product Catalog":
            data = [{"id": self.fake.uuid4(), "name": self.fake.catch_phrase(), "price": str(self.fake.random_number(digits=2)), "company": self.fake.company(), "description": self.fake.text(), "reviews": [{"user": self.fake.user_name(), "rating": random.randint(1, 5), "comment": self.fake.sentence()} for _ in range(random.randint(1, 5))]} for _ in range(num_records)]
        elif subtype == "Event Logs":
            data = [{"timestamp": str(self.fake.date_time_this_year()), "level": random.choice(["INFO", "WARNING", "ERROR"]), "ip": self.fake.ipv4(), "event": {"id": self.fake.uuid4(), "name": self.fake.word(), "details": self.fake.sentence()}} for _ in range(num_records)]
        else: # User Profiles
            data = []
            for _ in range(num_records):
                profile = self.fake.profile()
                profile['address'] = self.fake.address().split('\n')
                profile['friends'] = [self.fake.profile(fields=['username']) for _ in range(random.randint(1, 5))]
                data.append(profile)
        return json.dumps(data, indent=4, cls=CustomJSONEncoder)

    def _generate_xml(self, num_records):
        root = ET.Element("catalog")
        for _ in range(num_records):
            product = ET.SubElement(root, "product", id=self.fake.uuid4())
            ET.SubElement(product, "name").text = self.fake.catch_phrase()
            ET.SubElement(product, "price").text = str(self.fake.random_number(digits=2))
            ET.SubElement(product, "company").text = self.fake.company()
            ET.SubElement(product, "description").text = self.fake.text()
            reviews = ET.SubElement(product, "reviews")
            for _ in range(random.randint(1, 5)):
                review = ET.SubElement(reviews, "review", user=self.fake.user_name())
                ET.SubElement(review, "rating").text = str(random.randint(1, 5))
                ET.SubElement(review, "comment").text = self.fake.sentence()

        # Pretty print the XML
        from xml.dom import minidom
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def _generate_ini(self, num_records):
        text = ""
        for i in range(num_records):
            text += f"[user_{i}]\n"
            text += f"username = {self.fake.user_name()}\n"
            text += f"email = {self.fake.email()}\n\n"
        return text

    def _generate_yaml(self, num_records):
        import yaml
        data = [self.fake.profile() for _ in range(num_records)]
        return yaml.dump(data, default_flow_style=False)

    def _generate_log(self, num_records):
        lines = []
        for _ in range(num_records):
            dt = self.fake.date_time().strftime("%Y-%m-%d %H:%M:%S")
            ip = self.fake.ipv4()
            path = self.fake.uri_path()
            lines.append(f"{dt} - {ip} - GET {path} - 200")
        return "\n".join(lines)

    def _generate_sql(self, num_records, subtype):
        lines = []
        if subtype == "INSERT":
            for _ in range(num_records):
                name = self.fake.name().replace("'", "''")
                email = self.fake.email()
                lines.append(f"INSERT INTO users (name, email, created_at) VALUES ('{name}', '{email}', '{self.fake.date_time_this_decade()}');")
        elif subtype == "UPDATE":
            for i in range(num_records):
                name = self.fake.name().replace("'", "''")
                lines.append(f"UPDATE users SET name = '{name}', updated_at = '{self.fake.date_time_this_year()}' WHERE id = {i + 1};")
        elif subtype == "DELETE":
            for i in range(num_records):
                lines.append(f"DELETE FROM users WHERE created_at < '{self.fake.date_time_this_decade()}';")
        elif subtype == "SELECT":
            templates = [
                "SELECT u.id, u.name, p.product_name FROM users u JOIN purchases p ON u.id = p.user_id WHERE u.created_at > '2023-01-01';",
                "SELECT u.name, COUNT(p.id) as total_purchases FROM users u LEFT JOIN purchases p ON u.id = p.user_id GROUP BY u.name ORDER BY total_purchases DESC;",
                "SELECT * FROM users WHERE id IN (SELECT user_id FROM purchases WHERE product_name = '{product}');",
                "WITH recent_users AS (SELECT * FROM users WHERE created_at > '2023-01-01') SELECT * FROM recent_users;",
                "SELECT u.name, o.order_date, SUM(p.price) as total_price FROM users u JOIN orders o ON u.id = o.user_id JOIN products p ON o.product_id = p.id GROUP BY u.name, o.order_date;",
                "SELECT * FROM users WHERE email LIKE '%@gmail.com';",
                "SELECT * FROM users WHERE name LIKE 'J%';",
                "SELECT AVG(price) as avg_price, category FROM products GROUP BY category;",
                "SELECT * FROM users ORDER BY created_at DESC LIMIT 10;",
                "SELECT u.name, p.product_name FROM users u, purchases p WHERE u.id = p.user_id;"
            ]
            for _ in range(num_records):
                lines.append(random.choice(templates).format(product=self.fake.catch_phrase()))
        elif subtype == "ALTER TABLE":
            lines.append("ALTER TABLE users ADD COLUMN last_login TIMESTAMP;")
        return "\n".join(lines)

    def _generate_html(self, num_records):
        templates = [
            "<h1>{name}</h1><p>{text}</p>",
            "<h2>{name}</h2><p>{text}</p><ul><li>{item1}</li><li>{item2}</li></ul>",
            "<h3>{name}</h3><p>{text}</p><a href='{url}'>Link</a>",
            "<h4>{name}</h4><p>{text}</p><img src='{image_url}'>",
            "<h5>{name}</h5><p>{text}</p><blockquote>{quote}</blockquote>",
            "<h6>{name}</h6><p>{text}</p><pre><code>{code}</code></pre>",
            "<table><tr><th>{header1}</th><th>{header2}</th></tr><tr><td>{cell1}</td><td>{cell2}</td></tr></table>",
            "<div><h2>{name}</h2><p>{text}</p></div>",
            "<section><h3>{name}</h3><p>{text}</p></section>",
            "<article><h1>{name}</h1><p>{text}</p></article>"
        ]
        lines = ["<html><body>"]
        for _ in range(num_records):
            template = random.choice(templates)
            lines.append(template.format(
                name=self.fake.name(),
                text=self.fake.paragraph(),
                item1=self.fake.word(),
                item2=self.fake.word(),
                url=self.fake.url(),
                image_url=self.fake.image_url(),
                quote=self.fake.sentence(),
                code=self.fake.text(max_nb_chars=100),
                header1=self.fake.word(),
                header2=self.fake.word(),
                cell1=self.fake.word(),
                cell2=self.fake.word()
            ))
        lines.append("</body></html>")
        return "\n".join(lines)

    def _generate_md(self, num_records):
        templates = [
            "# {title}\n\n{text}",
            "## {title}\n\n{text}\n\n* {item1}\n* {item2}",
            "### {title}\n\n{text}\n\n[Link]({url})",
            "#### {title}\n\n{text}\n\n![Image]({image_url})",
            "##### {title}\n\n> {quote}",
            "###### {title}\n\n```\n{code}\n```",
            "| {header1} | {header2} |\n|---|---|\n| {cell1} | {cell2} |",
            "## {title}\n\n{text}",
            "### {title}\n\n{text}",
            "# {title}\n\n{text}"
        ]
        lines = []
        for _ in range(num_records):
            template = random.choice(templates)
            lines.append(template.format(
                title=self.fake.sentence(nb_words=4),
                text=self.fake.paragraph(),
                item1=self.fake.word(),
                item2=self.fake.word(),
                url=self.fake.url(),
                image_url=self.fake.image_url(),
                quote=self.fake.sentence(),
                code=self.fake.text(max_nb_chars=100),
                header1=self.fake.word(),
                header2=self.fake.word(),
                cell1=self.fake.word(),
                cell2=self.fake.word()
            ))
        return "\n\n".join(lines)

    def update_subtypes(self, event=None):
        file_type = self.file_type_var.get()
        subtypes = []
        if file_type == ".sql":
            subtypes = ["INSERT", "UPDATE", "DELETE", "SELECT", "ALTER TABLE"]
        elif file_type == ".txt":
            subtypes = ["Paragraphs", "User Profiles", "Log Entries"]
        elif file_type == ".json":
            subtypes = ["User Profiles", "Product Catalog", "Event Logs"]
        elif file_type == ".csv":
            subtypes = ["User Data", "Product List", "Order History"]

        self.subtype_combo['values'] = subtypes
        if subtypes:
            self.subtype_var.set(subtypes[0])
            self.subtype_combo.config(state="readonly")
        else:
            self.subtype_var.set("")
            self.subtype_combo.config(state="disabled")

    def _copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.output_text.get("1.0", tk.END))

    def _save_to_file(self):
        file_type = self.file_type_var.get()
        file_extension = file_type
        file_name = f"fake_data{file_extension}"
        filepath = filedialog.asksaveasfilename(
            initialfile=file_name,
            defaultextension=file_extension,
            filetypes=[(f"{file_extension.upper()} files", f"*{file_extension}"), ("All files", "*.*")]
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.output_text.get("1.0", tk.END))

    def on_close(self, event=None):
        self.destroy()
