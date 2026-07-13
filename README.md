# CryoCord CRM / Customer-Operations Application (Frappe Custom App)

A highly secure, upgrade-safe, and defensive custom Frappe application designed for CryoCord’s AI Projects Lab to manage storage-agreement requests and customer operations workflows.

---

## 1. Setup & Installation Steps

Since this application is structured explicitly as an independent custom app, it avoids editing the Frappe or ERPNext core directories, guaranteeing compliance with modern Frappe standards.

```bash
# 1. Access your Frappe bench directory
cd ~/frappe-bench

# 2. Add this custom application directory manually or clone via Git
# (Make sure to run 'export UV_LINK_MODE=copy' if deploying on external file systems)
bench get-app https://github.com

# 3. Install the app onto your specific site
bench --site cryocord.local install-app cryocord_crm

# 4. Synchronize data schemas and apply initial configurations
bench --site cryocord.local migrate
```

---

## 2. Design Rationale & Answers to Core Questions

### Q1: Why reuse a standard ERPNext record instead of creating your own?
We explicitly link to the standard **`Customer`** DocType via a `Link` field in `Storage Agreement Request`. Recreating a separate client database introduces severe data fragmentation, breaks native compatibility with standard ERPNext accounting, invoicing (`Sales Invoice`), and support systems, and creates massive overhead for future integration with enterprise data pipelines.

### Q2: When did you use a child table versus a separate linked DocType, and why?
* **Child Table (`Storage Package Item`)**: Used for the individual requested service/package lines. These rows do not possess an independent business lifecycle outside of the parent contract; they exist strictly as dependent entities inside a single `Storage Agreement Request`.
* **Linked DocType (`Customer`, `User`)**: Used for main entities. These have independent lifetimes, are shared universally across other business flows (like Accounting or HR), and must remain decoupled from specific requests.

### Q3: Frappe Workflow exists — why is server-side validation still necessary?
Frappe Workflows are heavily frontend-driven and enforce status transitions primarily at the UI level. If an attacker bypasses the web UI or uses custom scripts to call the REST API directly (`frappe.client.set_value` or standard updates), a native Frappe Workflow without strict controller enforcement will accept illegal transitions. Our Python layer (`before_save` and `validate`) acts as an immutable backend wall that guarantees protection regardless of the client-side mechanism used.

### Q4: How are permissions enforced beyond hiding fields or buttons?
Permissions are embedded at the server level via the document controller. Even if a malicious actor exposes an action button using JavaScript injection in the browser, the backend Python script catches the session information via `frappe.session.user` and terminates execution with `frappe.throw()`, returning a strict `403 Forbidden` API error.

### Q5: What does your audit trail guarantee, and what does it not?
* **Guarantees**: It guarantees a complete, append-only ledger of every legitimate status change initiated through the application layer, logging the actor, previous state, new state, timestamp, and explicit context.
* **Does NOT Guarantee**: It cannot prevent direct database manipulation by a Database Administrator (DBA) or root-level server actor executing SQL queries (`UPDATE` / `DELETE`) straight through the MariaDB console.
* **Production Hardening**: To achieve tamper-proof status in a true medical/clinical AI context, the audit logging logic should write simultaneously to an external immutable ledger or log aggregation service (e.g., AWS CloudWatch with Write-Once-Read-Many constraints or an isolated logging server over secure HTTPS webhooks).

### Q6: How does your app stay upgrade-safe during ERPNext upgrades?
* Every single custom layout specification and database schema change is housed within our own isolated `apps/cryocord_crm` directory.
* Permissions, customized settings, and global field properties are explicitly exported into the codebase framework as **Fixtures** within `hooks.py`, avoiding localized database modifications that could get overwritten by a `bench update`.

---

## 3. Role & Permission Matrix

| Business Role | Frappe Role | Document Actions Allowed | Allowed Workflow Transitions | Enforcement Level / Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Sales Officer** | `Sales Officer` | Create, Read, Edit Draft | Draft → Pending Approval | Role Permissions Manager & Python validation |
| **Operations Manager** | `Operations Manager` | Read, Update Status | Pending Approval → Approved / Rejected<br>Approved → Closed<br>Rejected → Draft | Python Server-Side `before_save` Transitions Guard |
| **All Users** | `All` | Read Only (Audit Log) | None | Strict JSON configuration (`create: 0, write: 0`) |

*Note: Separation of duties is actively verified inside `storage_agreement_request.py`. If a user with the `Operations Manager` role attempts to approve a record where `owner == frappe.session.user`, the backend Python method throws an explicit permission breach error.*

---

## 4. Production-Readiness Note

### System Migration Behavior (`bench migrate`)
During a `bench migrate` deployment command, the Frappe framework systematically performs database schema synchronization based on the app's `.json` schema maps, compiles UI assets, updates localized site caches, runs system patches, and injects declared fixtures into the database.

### Fixtures vs. Patches
* **Fixtures**: Automatically tracked configurations (e.g., custom Roles, global Custom Fields, Workflow definitions) that sync continuously during every migration step.
* **Patches**: One-off operational execution scripts. A patch is ideal for handling structural data conversions or fixing corrupted records (e.g., shifting historical data column names) during a specific release version, executing exactly once to prevent system overhead.

### Enterprise Backup & Disaster Recovery Blueprint
1. **Pre-Deployment Backup**: Before applying an app update in a production medical/enterprise instance, run an explicit multi-layer backup command:
   ```bash
   bench --site cryocord.local backup --with-files
   ```
2. **Disaster Recovery Strategy**: If an execution failure or fatal migration bug compromises data integrity during a rollout, immediately restore the pre-update environment via:
   ```bash
   bench --site cryocord.local restore /path/to/backup/database.sql.gz \
     --with-private-files /path/to/backup/private_files.tar \
     --with-public-files /path/to/backup/public_files.tar
   ```
