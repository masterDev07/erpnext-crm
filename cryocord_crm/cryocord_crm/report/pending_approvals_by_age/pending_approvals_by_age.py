# -*- coding: utf-8 -*-
import frappe
from frappe import _

def execute(filters=None):
    """Fungsi utama penarik data laporan yang mengembalikan struktur kolom dan baris"""
    columns = get_columns()
    data = get_data()
    return columns, data

def get_columns():
    """Mendefinisikan kolom tabel laporan"""
    return [
        {"label": _("Document ID"), "fieldname": "name", "fieldtype": "Link", "options": "Storage Agreement Request", "width": 180},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 180},
        {"label": _("Current Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
        {"label": _("Created Date"), "fieldname": "creation", "fieldtype": "Date", "width": 110},
        {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 130}
    ]

def get_data():
    """Mengambil data real-time dari database khusus untuk dokumen yang belum di-approve"""
    return frappe.get_all(
        "Storage Agreement Request",
        filters={"status": ["in", ["Draft", "Pending Approval"]]},
        fields=["name", "customer", "status", "creation", "total_amount"],
        order_by="creation asc"
    )
