import frappe
from frappe import _

APPROVED_STATE = "Approved"
REJECTED_STATES = frozenset({"Rejected", "Rejected by Finance Officer"})


def _get_excel_psi(item_code):
    name = frappe.db.get_value("Excel PSI", {"item_code": item_code}, "name")
    return frappe.get_doc("Excel PSI", name) if name else None


def _adjust_psi(psi, **deltas):
    for field, delta in deltas.items():
        psi.set(field, max(0.0, (psi.get(field) or 0.0) + delta))
    psi.flags.ignore_permissions = True
    psi.save()


def _warn_missing_psi(item_code):
    frappe.msgprint(
        _("Excel PSI not found for item <b>{0}</b> — PSI not updated.").format(item_code),
        indicator="orange",
        alert=True,
    )


def on_update(doc, method=None):
    """Detect workflow state transitions and mirror quantities into Excel PSI."""
    doc_before = doc.get_doc_before_save()

    # On first insert doc_before is None — treat old state as empty string
    old_state = (doc_before.get("custom_workflow_state") if doc_before else "").strip() or ""
    new_state = (doc.custom_workflow_state or "").strip()

    if old_state == new_state:
        return

    old_is_initial = not old_state or old_state in REJECTED_STATES
    old_is_active = bool(old_state) and old_state not in REJECTED_STATES and old_state != APPROVED_STATE
    old_is_approved = old_state == APPROVED_STATE

    new_is_rejected = new_state in REJECTED_STATES
    new_is_approved = new_state == APPROVED_STATE
    new_is_active = bool(new_state) and not new_is_rejected and not new_is_approved

    for item in doc.items:
        psi = _get_excel_psi(item.item_code)
        if not psi:
            _warn_missing_psi(item.item_code)
            continue

        qty = item.qty

        if old_is_initial and new_is_active:
            # MR enters pipeline for the first time (or re-enters after rejection)
            _adjust_psi(psi, proposed_new_order_qty=+qty, pipeline=+qty)

        elif old_is_active and new_is_approved:
            # Final approval: move from proposed → under_production; pipeline stays
            _adjust_psi(psi, proposed_new_order_qty=-qty, under_production=+qty)

        elif old_is_active and new_is_rejected:
            # Rejected while pending: remove from both trackers
            _adjust_psi(psi, proposed_new_order_qty=-qty, pipeline=-qty)

        elif old_is_approved and new_is_rejected:
            # Edge-case reversal: approved → rejected (if workflow allows it)
            _adjust_psi(psi, under_production=-qty, pipeline=-qty)


def on_cancel(doc, method=None):
    """Reverse Excel PSI quantities when a Material Request is cancelled."""
    state = (doc.custom_workflow_state or "").strip()

    if not state or state in REJECTED_STATES:
        return  # Nothing was ever written to PSI

    for item in doc.items:
        psi = _get_excel_psi(item.item_code)
        if not psi:
            continue

        qty = item.qty

        if state == APPROVED_STATE:
            # Was fully approved: reverse under_production + pipeline
            _adjust_psi(psi, under_production=-qty, pipeline=-qty)
        else:
            # Was in an active pending state: reverse proposed + pipeline
            _adjust_psi(psi, proposed_new_order_qty=-qty, pipeline=-qty)
