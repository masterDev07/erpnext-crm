app_name = "cryocord_crm"
app_title = "CryoCord CRM"
app_publisher = "Endro Mei Asmoro"
app_description = "Technical assessment for CryoCord AI Projects Lab"
app_email = "emasmoro@gmail.com"
app_license = "MIT"

# Fixtures untuk mengunci hak akses agar tidak hilang saat migrasi/update
fixtures = [
    {"dt": "Custom DocPerm"},
    {"dt": "Property Setter"}
]
