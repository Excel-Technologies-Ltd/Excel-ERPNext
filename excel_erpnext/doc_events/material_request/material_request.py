import frappe
from frappe import _
from frappe.utils import flt

APPROVED_STATE = "Approved"
REJECTED_STATES = frozenset({"Rejected", "Rejected by Finance Officer"})
EXCLUDED_FROM_PROPOSED = REJECTED_STATES | {APPROVED_STATE}


def _get_excel_psi(item_code):
    name = frappe.db.get_value("Excel PSI", {"item_code": item_code}, "name")
    return frappe.get_doc("Excel PSI", name) if name else None


def _create_excel_psi(item_code):
    """Excel PSI is named after item_code (autoname: field:item_code), so a
    Material Request referencing an item with no PSI yet gets one created rather
    than silently skipping the sync."""
    item = frappe.db.get_value(
        "Item", item_code, ["item_name", "item_group", "brand"], as_dict=True
    )
    if not item:
        return None

    psi = frappe.new_doc("Excel PSI")
    psi.item_code = item_code
    psi.item_name = item.item_name
    psi.item_group = item.item_group
    psi.item_brand = item.brand
    psi.flags.ignore_permissions = True
    psi.insert()
    return psi


def _get_or_create_excel_psi(item_code):
    psi = _get_excel_psi(item_code)
    if psi:
        return psi
    return _create_excel_psi(item_code)


def _qty_by_item(items):
    """item_code -> total qty across a Material Request's item rows."""
    totals = {}
    for item in items or []:
        if not item.item_code:
            continue
        totals[item.item_code] = totals.get(item.item_code, 0.0) + flt(item.qty)
    return totals


def _bucket(workflow_state, docstatus):
    """Which Excel PSI qty bucket a Material Request's items fall into, given its
    workflow state and docstatus. None means neither bucket (no state yet,
    rejected, or cancelled)."""
    if docstatus == 2:
        return None
    if workflow_state == APPROVED_STATE:
        return "approved"
    if workflow_state and workflow_state not in EXCLUDED_FROM_PROPOSED:
        return "active"
    return None


def _sync_psi_deltas(doc, doc_before):
    """Adjust Excel PSI's proposed_new_order_qty and under_production by exactly
    what this save changed, rather than recomputing either total from scratch.
    A scratch recompute would stomp on contributions this Material Request never
    owned in the first place: under_production in particular is also mutated
    directly by Excel LC Pipeline (see excel_lc_pipeline.on_submit/on_cancel),
    which carries part of it into Backlog outside of any qty this function can
    see — recomputing from Material Requests alone would undo that. Applying
    only the delta this save introduced leaves everything else untouched."""
    old_bucket = _bucket(doc_before.custom_workflow_state, doc_before.docstatus) if doc_before else None
    new_bucket = _bucket(doc.custom_workflow_state, doc.docstatus)

    old_qty = _qty_by_item(doc_before.items) if doc_before else {}
    new_qty = _qty_by_item(doc.items)

    for item_code in set(old_qty) | set(new_qty):
        old_active = old_qty.get(item_code, 0.0) if old_bucket == "active" else 0.0
        new_active = new_qty.get(item_code, 0.0) if new_bucket == "active" else 0.0
        old_approved = old_qty.get(item_code, 0.0) if old_bucket == "approved" else 0.0
        new_approved = new_qty.get(item_code, 0.0) if new_bucket == "approved" else 0.0

        proposed_delta = new_active - old_active
        under_production_delta = new_approved - old_approved

        if not proposed_delta and not under_production_delta:
            continue

        psi = _get_or_create_excel_psi(item_code)
        if not psi:
            frappe.msgprint(
                _("Item <b>{0}</b> not found — Excel PSI not created.").format(item_code),
                indicator="orange",
                alert=True,
            )
            continue

        psi.proposed_new_order_qty = max(0.0, flt(psi.proposed_new_order_qty) + proposed_delta)
        psi.under_production = max(0.0, flt(psi.under_production) + under_production_delta)
        psi.flags.ignore_permissions = True
        psi.save()


def validate(doc, method=None):
    """Push each Material Request item rate into Excel PSI FOB.

    Skipped once the request was already submitted *before* this save (docstatus 1
    on doc_before) -- rate isn't allow_on_submit, so changing linked PSI on a
    re-save of an already-submitted request is avoided. The save that transitions
    a request into Approved for the first time is still covered, since
    doc_before.docstatus is still 0 at that point.
    """
    doc_before = doc.get_doc_before_save()
    if doc_before and doc_before.docstatus == 1:
        return

    for item in doc.items:
        if not item.item_code:
            continue

        rate = flt(item.rate)
        item.amount = flt(item.qty) * rate

        if rate <= 0:
            continue

        psi = _get_or_create_excel_psi(item.item_code)
        if not psi:
            continue

        if flt(psi.fob) == rate:
            continue

        psi.fob = rate
        psi.flags.ignore_permissions = True
        psi.save()


def on_update(doc, method=None):
    """Mirror Material Request quantities into Excel PSI. Runs on every save, not
    just workflow-state transitions, so item/qty edits made while the request stays
    in the same state are picked up too. Pipeline/Backlog stay owned by Excel LC
    Pipeline's on_submit/on_cancel — not touched here."""
    _sync_psi_deltas(doc, doc.get_doc_before_save())


def on_cancel(doc, method=None):
    """cancel() saves the doc with docstatus=2, so get_doc_before_save() still
    gives us the pre-cancel state (e.g. Approved/docstatus 1) to remove this
    request's qty out of whichever bucket it was contributing to."""
    _sync_psi_deltas(doc, doc.get_doc_before_save())
