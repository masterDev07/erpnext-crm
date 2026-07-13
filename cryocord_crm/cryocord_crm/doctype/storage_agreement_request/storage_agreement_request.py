# -*- coding: utf-8 -*-
import frappe
from frappe.model.document import Document
from frappe import _

class StorageAgreementRequest(Document):
    def validate(self):
        """Fungsi validasi utama sebelum data disimpan (Form Validation)"""
        self.validate_child_items()
        self.calculate_totals()
        self.enforce_immutability()
        self.enforce_separation_of_duties()

    def validate_child_items(self):
        """Aturan Bisnis: Memastikan item paket tidak kosong dan harga tidak negatif"""
        if not self.packages:
            frappe.throw(_("Daftar paket pilihan tidak boleh kosong."))

        for item in self.packages:
            if item.quantity <= 0:
                frappe.throw(_("Jumlah (Quantity) untuk paket {0} harus lebih dari 0.").format(item.package_name))
            if item.unit_price < 0:
                frappe.throw(_("Harga satuan (Unit Price) untuk paket {0} tidak boleh negatif.").format(item.package_name))

    def calculate_totals(self):
        """Menghitung total harga otomatis di server-side"""
        total = 0
        for item in self.packages:
            item.amount = item.quantity * item.unit_price
            total += item.amount
        self.total_amount = total

    def enforce_immutability(self):
        """Aturan Bisnis: Dokumen yang sudah Approved atau Closed tidak boleh diubah nilainya"""
        if self.is_new():
            return

        # Ambil status dokumen asli yang tersimpan di database sebelum diubah pengguna
        db_status = frappe.db.get_value("Storage Agreement Request", self.name, "status")

        if db_status in ["Approved", "Closed"] and self.has_changed():
            # Mengizinkan perubahan status itu sendiri, tetapi memblokir perubahan data lainnya
            if not self.is_dirty("status") or len(self.get_dirty_fields()) > 1:
                frappe.throw(_("Dokumen ini sudah berstatus {0} dan datanya tidak dapat diubah lagi (Immutable).").format(db_status))

    def enforce_separation_of_duties(self):
        """Aturan Bisnis: Pembuat dokumen tidak boleh melakukan Approval sendiri"""
        if self.is_new():
            return

        db_status = frappe.db.get_value("Storage Agreement Request", self.name, "status")

        # Jika status mencoba diubah menjadi 'Approved'
        if self.status == "Approved" and db_status != "Approved":
            # Periksa pembuat asli dokumen (owner) dengan user yang sedang login saat ini (frappe.session.user)
            if self.owner == frappe.session.user:
                frappe.throw(_("Pelanggaran Aturan: Pembuat dokumen (Sales Officer) dilarang keras menyetujui (Approve) dokumennya sendiri!"))

    def before_save(self):
        """Memvalidasi Alur State Machine (Workflow Transitions Guard) di tingkat Server"""
        if self.is_new():
            self.status = "Draft"
            return

        db_status = frappe.db.get_value("Storage Agreement Request", self.name, "status")

        if db_status == self.status:
            return # Tidak ada perubahan status, lewati validasi transisi

        # Definisikan peta transisi status yang valid (State Machine)
        valid_transitions = {
            "Draft": ["Pending Approval"],
            "Pending Approval": ["Approved", "Rejected"],
            "Approved": ["Closed"],
            "Rejected": ["Draft"],
            "Closed": [] # State akhir, tidak bisa ke mana-mana lagi
        }

        if self.status not in valid_transitions.get(db_status, []):
            frappe.throw(_("Transisi status ilegal! Tidak diizinkan mengubah status dari '{0}' langsung ke '{1}'.").format(db_status, self.status))

        # Catat log audit setiap ada transisi status yang sah
        self.create_audit_log(db_status, self.status)

    def create_audit_log(self, from_state, to_state):
        """Fungsi pembantu untuk mencatat jejak audit (Append-Only Audit Trail) secara otomatis"""
        # Kita akan mendefinisikan DocType 'CryoCord Audit Log' pada tahap berikutnya
        audit_doc = frappe.get_doc({
            "doctype": "CryoCord Audit Log",
            "timestamp": frappe.utils.now_datetime(),
            "user": frappe.session.user,
            "from_state": from_state,
            "to_state": to_state,
            "document_link": self.name,
            "reason": f"Status changed from {from_state} to {to_state} via document update controller."
        })
        audit_doc.insert(ignore_permissions=True) # Paksa tulis ke DB lewat server, bypass user permission biasa
