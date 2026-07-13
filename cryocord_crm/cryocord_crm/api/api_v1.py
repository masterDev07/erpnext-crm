# -*- coding: utf-8 -*-
import frappe
from frappe import _

@frappe.whitelist()
def get_document_history(docname):
    """
    REST API Endpoint Kustom untuk mengambil status terkini dan jejak audit dokumen.
    Akses: http://your-site/api/method/cryocord_crm.api.api_v1.get_document_history
    """
    # 1. Pastikan pengguna sudah login (Bukan Guest)
    if frappe.session.user == "Guest":
        frappe.local.response.http_status_code = 401
        return {"error": _("Akses ditolak: Anda harus login terlebih dahulu.")}

    # 2. Validasi parameter input
    if not docname:
        frappe.local.response.http_status_code = 400
        return {"error": _("Parameter 'docname' wajib diisi.")}

    # 3. Pemeriksaan Hak Akses Manual (Explicit Permission Check)
    # Memastikan user memiliki hak akses minimal 'Read' pada dokumen target
    if not frappe.has_permission("Storage Agreement Request", "read", docname):
        frappe.local.response.http_status_code = 403
        return {"error": _("Akses dilarang: Anda tidak memiliki izin untuk melihat dokumen ini.")}

    # 4. Ambil data dokumen utama jika lolos pemeriksaan keamanan
    if not frappe.db.exists("Storage Agreement Request", docname):
        frappe.local.response.http_status_code = 404
        return {"error": _("Dokumen {0} tidak ditemukan.").format(docname)}

    doc_data = frappe.db.get_value(
        "Storage Agreement Request",
        docname,
        ["name", "customer", "status", "total_amount"],
        as_dict=1
    )

    # 5. Ambil data jejak audit (Append-Only Audit Logs) yang terikat dengan dokumen ini
    audit_logs = frappe.get_all(
        "CryoCord Audit Log",
        filters={"document_link": docname},
        fields=["timestamp", "user", "from_state", "to_state", "reason"],
        order_by="timestamp desc"
    )

    # 6. Kembalikan respons data terstruktur aman (JSON)
    return {
        "document": doc_data,
        "audit_trail": audit_logs
    }
