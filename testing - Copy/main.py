import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import requests  # make sure to install this package (pip install requests)

class MediaTracker:
    JSON_FILENAME = "media_data.json"

    def __init__(self, root):
        self.root = root
        self.root.title("Media Tracker")
        self.root.iconbitmap("icon.ico")  # Set the window icon
        self.entries = []
        self.current_filter = "All"
        self.local_search_query = ""

        # Load existing data
        self.load_data()

        # Create input section for adding new entries
        input_frame = ttk.LabelFrame(root, text="Add New Entry")
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(input_frame, text="Title:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.title_entry = ttk.Entry(input_frame, width=40)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Type:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.type_var = tk.StringVar()
        # Changed "TV Show" to "Series"
        self.type_combo = ttk.Combobox(input_frame, textvariable=self.type_var,
                                       values=["Movie", "Series", "Book", "Game"], state="readonly")
        self.type_combo.current(0)
        self.type_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(input_frame, text="Status:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(input_frame, textvariable=self.status_var,
                                         values=["Want to Watch/Read/Play", "Watched/Read/Played"], state="readonly")
        self.status_combo.current(0)
        self.status_combo.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.status_combo.bind("<<ComboboxSelected>>", self.toggle_rating)

        ttk.Label(input_frame, text="Rating:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.rating_var = tk.StringVar()
        self.rating_combo = ttk.Combobox(input_frame, textvariable=self.rating_var,
                                         values=["★☆☆☆☆", "★★☆☆☆", "★★★☆☆", "★★★★☆", "★★★★★"], state="disabled")
        self.rating_combo.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

        add_btn = ttk.Button(input_frame, text="Add to List", command=self.add_entry)
        add_btn.grid(row=4, column=1, padx=5, pady=5, sticky=tk.E)

        # Search section (IMDb Search)
        search_frame = ttk.LabelFrame(root, text="Search IMDb")
        search_frame.pack(padx=10, pady=10, fill=tk.X)
        ttk.Label(search_frame, text="Search Title:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        search_btn = ttk.Button(search_frame, text="Search IMDb", command=self.search_imdb)
        search_btn.grid(row=0, column=2, padx=5, pady=5)

        # Filter and local search controls
        filter_frame = ttk.Frame(root)
        filter_frame.pack(padx=10, pady=5, fill=tk.X)

        ttk.Label(filter_frame, text="Filter by Status:").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar(value="All")
        ttk.Radiobutton(filter_frame, text="All", variable=self.filter_var,
                        value="All", command=self.update_list).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="To Watch", variable=self.filter_var,
                        value="Want to Watch/Read/Play", command=self.update_list).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Completed", variable=self.filter_var,
                        value="Watched/Read/Played", command=self.update_list).pack(side=tk.LEFT, padx=5)

        ttk.Label(filter_frame, text="   Filter by Type:").pack(side=tk.LEFT, padx=5)
        self.type_filter_var = tk.StringVar(value="All Types")
        # Changed "TV Show" to "Series" in filter options as well
        self.type_filter = ttk.Combobox(filter_frame, textvariable=self.type_filter_var,
                                        values=["All Types", "Movie", "Series", "Book", "Game"],
                                        state="readonly", width=12)
        self.type_filter.current(0)
        self.type_filter.pack(side=tk.LEFT, padx=5)
        self.type_filter.bind("<<ComboboxSelected>>", self.update_list)

        # Local list search controls
        local_search_frame = ttk.Frame(root)
        local_search_frame.pack(padx=10, pady=5, fill=tk.X)
        ttk.Label(local_search_frame, text="Search List:").pack(side=tk.LEFT, padx=5)
        self.local_search_var = tk.StringVar()
        self.local_search_entry = ttk.Entry(local_search_frame, textvariable=self.local_search_var, width=30)
        self.local_search_entry.pack(side=tk.LEFT, padx=5)
        search_list_btn = ttk.Button(local_search_frame, text="Search", command=self.search_local)
        search_list_btn.pack(side=tk.LEFT, padx=5)
        clear_search_btn = ttk.Button(local_search_frame, text="Clear", command=self.clear_local_search)
        clear_search_btn.pack(side=tk.LEFT, padx=5)

        # Media list (Treeview)
        self.tree = ttk.Treeview(root, columns=("Title", "Type", "Status", "Rating"), show="headings")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Type", text="Type", command=lambda: self.sort_column("Type", False))
        self.tree.heading("Status", text="Status")
        self.tree.heading("Rating", text="Rating")
        self.tree.column("Title", width=250)
        self.tree.column("Type", width=100)
        self.tree.column("Status", width=150)
        self.tree.column("Rating", width=100)
        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.edit_entry_event)  # Bind double-click to edit

        # Control buttons for delete (edit is now via double-click)
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=5)
        del_btn = ttk.Button(btn_frame, text="Delete Selected", command=self.delete_entry)
        del_btn.pack(side=tk.LEFT, padx=5)

        self.update_list()

    def load_data(self):
        if os.path.exists(self.JSON_FILENAME):
            try:
                with open(self.JSON_FILENAME, "r") as f:
                    self.entries = json.load(f)
            except Exception as e:
                messagebox.showwarning("Load Error", f"Failed to load data: {str(e)}")

    def save_data(self):
        try:
            with open(self.JSON_FILENAME, "w") as f:
                json.dump(self.entries, f, indent=2)
        except Exception as e:
            messagebox.showwarning("Save Error", f"Failed to save data: {str(e)}")

    def toggle_rating(self, event=None):
        if self.status_var.get() == "Watched/Read/Played":
            self.rating_combo.config(state="readonly")
            self.rating_combo.current(0)
        else:
            self.rating_combo.config(state="disabled")
            self.rating_var.set("")

    def add_entry(self):
        title = self.title_entry.get().strip()
        media_type = self.type_var.get()
        status = self.status_var.get()
        rating = self.rating_var.get() if status == "Watched/Read/Played" else "N/A"

        if not title:
            messagebox.showwarning("Input Error", "Please enter a title")
            return

        if status == "Watched/Read/Played" and not rating:
            messagebox.showwarning("Input Error", "Please select a rating for completed items")
            return

        self.entries.append({
            "title": title,
            "type": media_type,
            "status": status,
            "rating": rating
        })

        self.title_entry.delete(0, tk.END)
        self.update_list()
        self.save_data()

    def delete_entry(self):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        # Delete in reverse order to avoid index issues.
        indices = sorted((int(item) for item in selected_items), reverse=True)
        for index in indices:
            del self.entries[index]

        self.update_list()
        self.save_data()

    def edit_entry_event(self, event):
        # Identify the clicked row using the y coordinate of the event.
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.open_edit_window(int(item_id))

    def edit_entry(self):
        # Fallback method if using a button (if needed)
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select an entry to edit")
            return
        self.open_edit_window(int(selected_items[0]))

    def open_edit_window(self, index):
        entry = self.entries[index]
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit Entry")

        ttk.Label(edit_win, text="Title:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        title_entry = ttk.Entry(edit_win, width=40)
        title_entry.grid(row=0, column=1, padx=5, pady=5)
        title_entry.insert(0, entry["title"])

        ttk.Label(edit_win, text="Type:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        type_var = tk.StringVar(value=entry["type"])
        # Changed "TV Show" to "Series" in the edit window options as well
        type_combo = ttk.Combobox(edit_win, textvariable=type_var,
                                  values=["Movie", "Series", "Book", "Game"], state="readonly")
        type_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(edit_win, text="Status:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        status_var = tk.StringVar(value=entry["status"])
        status_combo = ttk.Combobox(edit_win, textvariable=status_var,
                                    values=["Want to Watch/Read/Play", "Watched/Read/Played"], state="readonly")
        status_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(edit_win, text="Rating:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        rating_var = tk.StringVar(value=entry["rating"])
        rating_combo = ttk.Combobox(edit_win, textvariable=rating_var,
                                    values=["★☆☆☆☆", "★★☆☆☆", "★★★☆☆", "★★★★☆", "★★★★★"], state="readonly")
        rating_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        def toggle_edit_rating(*args):
            if status_var.get() == "Watched/Read/Played":
                rating_combo.config(state="readonly")
            else:
                rating_combo.config(state="disabled")
                rating_var.set("N/A")
        status_combo.bind("<<ComboboxSelected>>", toggle_edit_rating)
        toggle_edit_rating()

        def save_changes():
            new_title = title_entry.get().strip()
            if not new_title:
                messagebox.showwarning("Input Error", "Title cannot be empty")
                return
            new_status = status_var.get()
            new_rating = rating_var.get() if new_status == "Watched/Read/Played" else "N/A"
            self.entries[index] = {
                "title": new_title,
                "type": type_var.get(),
                "status": new_status,
                "rating": new_rating
            }
            self.update_list()
            self.save_data()
            edit_win.destroy()

        save_btn = ttk.Button(edit_win, text="Save Changes", command=save_changes)
        save_btn.grid(row=4, column=1, padx=5, pady=10, sticky="e")

    def sort_column(self, column, reverse):
        items = [(self.tree.set(child, column), child) for child in self.tree.get_children("")]
        items.sort(reverse=reverse)
        for index, (val, child) in enumerate(items):
            self.tree.move(child, "", index)
        self.tree.heading(column, command=lambda: self.sort_column(column, not reverse))

    def update_list(self, event=None):
        self.tree.delete(*self.tree.get_children())
        status_filter = self.filter_var.get()
        type_filter = self.type_filter_var.get()
        query = self.local_search_query.lower()

        for i, entry in enumerate(self.entries):
            status_ok = (status_filter == "All") or (entry["status"] == status_filter)
            type_ok = (type_filter == "All Types") or (entry["type"] == type_filter)
            search_ok = (not query) or (query in entry["title"].lower())
            if status_ok and type_ok and search_ok:
                self.tree.insert("", tk.END, iid=str(i), values=(
                    entry["title"],
                    entry["type"],
                    entry["status"],
                    entry["rating"]
                ))

    def search_imdb(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Input Error", "Please enter a search term")
            return

        api_key = "1e4e6243"  # Replace with your actual OMDb API key
        url = f"http://www.omdbapi.com/?apikey={api_key}&s={query}"

        try:
            response = requests.get(url)
            data = response.json()
            if data.get("Response") == "True":
                results = data.get("Search", [])
                self.show_search_results(results)
            else:
                messagebox.showinfo("No Results", data.get("Error", "No results found"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to search IMDb: {str(e)}")

    def show_search_results(self, results):
        result_win = tk.Toplevel(self.root)
        result_win.title("IMDb Search Results")
        result_win.geometry("600x400")
        listbox = tk.Listbox(result_win, width=80)
        listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        listbox.results = results
        for result in results:
            title = result.get("Title", "N/A")
            year = result.get("Year", "N/A")
            media_type = result.get("Type", "N/A")
            listbox.insert(tk.END, f"{title} ({year}) - {media_type.title()}")
        listbox.bind("<Double-Button-1>", lambda event: self.add_search_result(event, listbox))

    def add_search_result(self, event, listbox):
        selection = listbox.curselection()
        if not selection:
            return
        index = selection[0]
        result = listbox.results[index]
        title = result.get("Title", "N/A")
        media_type = result.get("Type", "N/A").title()
        status = "Want to Watch/Read/Play"
        rating = "N/A"
        self.entries.append({
            "title": title,
            "type": media_type,
            "status": status,
            "rating": rating
        })
        self.update_list()
        self.save_data()
        messagebox.showinfo("Added", f"'{title}' has been added to your media list.")

    def search_local(self):
        self.local_search_query = self.local_search_var.get().strip()
        self.update_list()

    def clear_local_search(self):
        self.local_search_query = ""
        self.local_search_var.set("")
        self.update_list()

if __name__ == "__main__":
    root = tk.Tk()
    app = MediaTracker(root)
    root.mainloop()
