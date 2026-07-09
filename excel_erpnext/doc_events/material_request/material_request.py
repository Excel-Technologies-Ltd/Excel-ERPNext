import frappe
from frappe import _
from frappe.utils import flt

APPROVED_STATE = "Approved"
REJECTED_STATES = frozenset({"Rejected", "Rejected by Finance Officer"})
EXCLUDED_FROM_PROPOSED = REJECTED_STATES | {APPROVED_STATE}


def _get_excel_psi(item_code):
    name = frappe.db.get_value("Excel PSI", {"item_code": item_code}, "name")
    return frappe.get_doc("Excel PSI", name) if name else None


def _warn_missing_psi(item_code):
    frappe.msgprint(
        _("Excel PSI not found for item <b>{0}</b> — PSI not updated.").format(item_code),
        indicator="orange",
        alert=True,
    )


def _items_by_code(items):
    codes = set()
    for item in items or []:
        if item.item_code:
            codes.add(item.item_code)
    return codes


def _sum_qty_where(item_code, extra_condition, extra_values=None):
    rows = frappe.db.sql(
        f"""
        SELECT SUM(mri.qty) AS total
        FROM `tabMaterial Request Item` mri
        INNER JOIN `tabMaterial Request` mr ON mr.name = mri.parent
        WHERE mri.item_code = %(item_code)s
          AND mr.docstatus != 2
          AND {extra_condition}
        """,
        {"item_code": item_code, **(extra_values or {})},
        as_dict=True,
    )
    return flt(rows[0].total) if rows and rows[0].total else 0.0


def _active_requested_qty(item_code):
    """Sum of qty for this item across every Material Request currently in an
    active (pending) workflow state — i.e. not yet Approved and not Rejected.
    Recomputed from scratch every time rather than accumulated as a delta, so it
    can never drift out of sync — no matter what happened on earlier saves
    (including saves made before this logic existed), this always reflects the
    true current state."""
    return _sum_qty_where(
        item_code,
        """mr.custom_workflow_state IS NOT NULL
          AND mr.custom_workflow_state != ''
          AND mr.custom_workflow_state NOT IN %(excluded_states)s""",
        {"excluded_states": tuple(EXCLUDED_FROM_PROPOSED)},
    )


def _approved_requested_qty(item_code):
    """Sum of qty for this item across every Material Request currently Approved —
    the portion that has moved from "proposed" into "under production". Same
    recompute-from-scratch approach as _active_requested_qty, for the same reason:
    it can't drift, regardless of history."""
    return _sum_qty_where(
        item_code,
        "mr.custom_workflow_state = %(approved_state)s",
        {"approved_state": APPROVED_STATE},
    )


def _sync_psi_quantities(item_code):
    psi = _get_excel_psi(item_code)
    if not psi:
        _warn_missing_psi(item_code)
        return

    proposed_qty = _active_requested_qty(item_code)
    under_production_qty = _approved_requested_qty(item_code)

    if (
        flt(psi.proposed_new_order_qty) == proposed_qty
        and flt(psi.under_production) == under_production_qty
    ):
        return

    psi.proposed_new_order_qty = proposed_qty
    psi.under_production = under_production_qty
    psi.flags.ignore_permissions = True
    psi.save()


def on_update(doc, method=None):
    """Mirror Material Request quantities into Excel PSI. Runs on every save, not
    just workflow-state transitions, so item/qty edits made while the request stays
    in the same state are picked up too. Recomputes both proposed_new_order_qty
    (sum of active/pending requests) and under_production (sum of Approved
    requests) from scratch for each item touched by this save, rather than
    adjusting by a delta, so it's self-healing instead of drift-prone. Pipeline is
    owned by Excel LC Pipeline's on_submit/on_cancel — not touched here."""
    doc_before = doc.get_doc_before_save()

    old_codes = _items_by_code(doc_before.items) if doc_before else set()
    new_codes = _items_by_code(doc.items)

    for item_code in old_codes | new_codes:
        _sync_psi_quantities(item_code)


def on_cancel(doc, method=None):
    """Resync this request's items after cancellation — the cancelled request's
    own qty naturally drops out of both the active and approved sums."""
    for item_code in _items_by_code(doc.items):
        _sync_psi_quantities(item_code)
