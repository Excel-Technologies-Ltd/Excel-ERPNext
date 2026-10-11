// function total_calc(frm, cdt, cdn) { 
//     var d = locals[cdt][cdn]; 
//     frappe.model.set_value(cdt, cdn, "eta", frappe.datetime.add_days( d.on_board_date , 15));
//     //refresh_field("eta");
//     frappe.model.set_value(cdt, cdn, "etr", frappe.datetime.add_days( d.eta , 10));
//    // refresh_field("eta");
// }
// frappe.ui.form.on("Excel LC Pipeline", "on_board_date", total_calc);

// function total_calc2(frm, cdt, cdn) { 
//     var d = locals[cdt][cdn]; 
//     frappe.model.set_value(cdt, cdn, "etr", frappe.datetime.add_days( d.eta , 10));
// }
// frappe.ui.form.on("Excel LC Pipeline", "eta", total_calc2);

// frappe.ui.form.on('Excel LC Pipeline', 'on_save',  function(frm) {
//     if (frm.doc.pipeline_status ==='Complete') {
//         frm.set_df_property('pipeline_status', 'read_only', 0);
//         msgprint('The Pipeline Status Should be In Progress!');
//         validate = false;
//     }
// });

frappe.ui.form.on('Excel LC Pipeline', 'before_submit',  function(frm) {
    if (frm.doc.pipeline_status !='In Progress') {
        msgprint('The Pipeline Status Should be In Progress!');
        validate = false;
    }
});

frappe.ui.form.on('Excel LC Pipeline', 'refresh', function(frm) {
    if (frm.doc.pipeline_status === 'Complete' && frm.doc.docstatus != 0) {
        frm.set_df_property('pipeline_status', 'read_only', 1);
    } else {
        frm.set_df_property('pipeline_status', 'read_only', 0);
    }
});

// frappe.ui.form.on("Excel LC Pipeline", "validate", function(frm) {
// var regex = /[^0-9A-ZÖÜÄÈÀÉ\s]/g;
// if (regex.test(frm.doc.lot_no) === true){
//     frappe.msgprint(__("Brand: Only uppercase letters, numbers and spaces are allowed."));
//     frappe.validated = false;
//     }
// });
frappe.ui.form.on("Excel LC Pipeline", {
    onload_post_render: function(frm) {
       $("form>.frappe-control input").css("text-transform", "uppercase");
    }
});

// ---------------------------------------------------------------------------
// Material Request allocation + consolidated Items Summary
// ---------------------------------------------------------------------------

frappe.ui.form.on('Excel LC Pipeline', {
    refresh(frm) {
        add_fetch_mr_button(frm);
        // Self-correct stale Remaining Qty / Summary when opening an editable doc
        // (e.g. saved before this logic existed). Only writes when values actually
        // differ, so it won't gratuitously mark the form dirty.
        if (frm.doc.docstatus === 0) {
            sync_computed_fields(frm);
        }
    },
    validate(frm) {
        // Keep the read-only summary current before save (the server rebuilds it
        // again authoritatively in validate()).
        sync_computed_fields(frm);
    }
});

frappe.ui.form.on('Excel LC Pipeline Item', {
    qty(frm) { sync_computed_fields(frm); },
    rate(frm) { sync_computed_fields(frm); },
    amount(frm) { sync_computed_fields(frm); },
    item_code(frm) { sync_computed_fields(frm); },
    custom_items_add(frm) { sync_computed_fields(frm); },
    custom_items_remove(frm) { sync_computed_fields(frm); }
});

function add_fetch_mr_button(frm) {
    const field = frm.fields_dict.custom_items;
    if (!field || !field.grid) return;
    if (frm.doc.docstatus !== 0) return;  // only editable drafts

    const grid = field.grid;
    const label = __('Fetch Material Requests');
    if (grid.custom_buttons && grid.custom_buttons[label]) return;  // avoid dupes
    grid.add_custom_button(label, () => open_fetch_mr_dialog(frm));
}

function get_focused_item_code(frm) {
    const grid = frm.fields_dict.custom_items.grid;
    const selected = grid.get_selected_children ? grid.get_selected_children() : [];
    if (selected && selected.length === 1 && selected[0].item_code) {
        return selected[0].item_code;
    }
    if (grid.open_grid_row && grid.open_grid_row.doc && grid.open_grid_row.doc.item_code) {
        return grid.open_grid_row.doc.item_code;
    }
    return null;
}

function open_fetch_mr_dialog(frm) {
    const d = new frappe.ui.Dialog({
        title: __('Fetch Material Requests'),
        size: 'large',
        fields: [
            {
                fieldname: 'item_code',
                fieldtype: 'Link',
                options: 'Item',
                label: __('Item Code'),
                reqd: 1,
                onchange: () => load_mr_rows(d)
            },
            { fieldname: 'results', fieldtype: 'HTML' }
        ],
        primary_action_label: __('Allocate Selected'),
        primary_action: () => allocate_selected_mr(frm, d)
    });

    d._mr_rows = [];
    const prefill = get_focused_item_code(frm);
    d.show();
    if (prefill) {
        d.set_value('item_code', prefill);  // onchange triggers load_mr_rows
    }
}

function load_mr_rows(d) {
    const item_code = d.get_value('item_code');
    const $wrap = d.fields_dict.results.$wrapper;
    if (!item_code) { $wrap.empty(); d._mr_rows = []; return; }

    frappe.call({
        method: 'excel_erpnext.api.lc_pipeline_allocation.get_material_requests_for_item',
        args: { item_code },
        freeze: true,
        callback: (r) => {
            const rows = r.message || [];
            d._mr_rows = rows;
            if (!rows.length) {
                $wrap.html(
                    `<div class="text-muted" style="padding:8px 0;">${
                        __('No eligible Material Requests with available quantity for this item.')
                    }</div>`
                );
                return;
            }
            let html = `<table class="table table-bordered" style="margin-bottom:0;">
                <thead><tr>
                    <th style="width:32px;"></th>
                    <th>${__('Material Request')}</th>
                    <th class="text-right">${__('Request Qty')}</th>
                    <th class="text-right">${__('Pipeline Qty')}</th>
                    <th class="text-right">${__('Remaining Qty')}</th>
                    <th style="width:140px;">${__('Allocation Qty')}</th>
                </tr></thead><tbody>`;
            rows.forEach((row, i) => {
                html += `<tr>
                    <td><input type="checkbox" class="mr-check" data-i="${i}"></td>
                    <td>${frappe.utils.escape_html(row.material_request)}</td>
                    <td class="text-right">${format_number(row.request_qty)}</td>
                    <td class="text-right">${format_number(row.pipeline_qty)}</td>
                    <td class="text-right">${format_number(row.remaining_qty)}</td>
                    <td><input type="number" class="form-control input-sm mr-alloc" data-i="${i}"
                        min="0" step="any" max="${row.remaining_qty}" value="${row.remaining_qty}"></td>
                </tr>`;
            });
            html += '</tbody></table>';
            $wrap.html(html);

            // Checking a row with no explicit edit keeps its default (remaining);
            // typing an allocation auto-checks the row.
            $wrap.find('.mr-alloc').on('input', function () {
                $wrap.find(`.mr-check[data-i="${$(this).data('i')}"]`).prop('checked', true);
            });
        }
    });
}

function allocate_selected_mr(frm, d) {
    const rows = d._mr_rows || [];
    const $wrap = d.fields_dict.results.$wrapper;
    const errors = [];
    const to_add = [];

    $wrap.find('.mr-check:checked').each(function () {
        const i = parseInt($(this).data('i'), 10);
        const src = rows[i];
        const alloc = flt($wrap.find(`.mr-alloc[data-i="${i}"]`).val());
        if (alloc <= 0) {
            errors.push(__('{0}: allocation must be greater than zero.', [src.material_request]));
            return;
        }
        if (alloc > flt(src.remaining_qty) + 1e-9) {
            errors.push(__('{0}: allocation ({1}) exceeds remaining ({2}).',
                [src.material_request, alloc, src.remaining_qty]));
            return;
        }
        to_add.push({ src, alloc });
    });

    if (errors.length) { frappe.msgprint({ title: __('Invalid Allocation'), message: errors.join('<br>'), indicator: 'red' }); return; }
    if (!to_add.length) { frappe.msgprint(__('Select at least one Material Request row (or enter an allocation quantity).')); return; }

    const added = [];
    to_add.forEach(({ src, alloc }) => {
        const child = frm.add_child('custom_items', {
            item_code: src.item_code,
            item_name: src.item_name,
            custom_material_request: src.material_request,
            custom_material_request_item: src.material_request_item,
            custom_request_qty: src.request_qty,
            // Remaining Qty on the row reflects Request - allocated Quantity.
            custom_remaining_qty: flt(src.request_qty) - alloc,
            qty: alloc
        });
        added.push(child);
    });

    frm.refresh_field('custom_items');
    // Cascade row amount via the model so the existing totals Client Script and the
    // summary both recompute.
    added.forEach((c) => frappe.model.set_value(c.doctype, c.name, 'amount', flt(c.qty) * flt(c.rate)));
    sync_computed_fields(frm);
    frm.dirty();
    d.hide();
    frappe.show_alert({ message: __('Added {0} allocation row(s).', [added.length]), indicator: 'green' });
}

// Group custom_items by item_code -> desired summary rows.
//   Proposed Quantity = sum(Request Qty)  (fallback to qty for manual rows)
//   LC Quantity       = sum(Quantity)     (allocated on this LC)
//   Remaining         = Proposed - LC
function compute_summary_rows(frm) {
    const groups = {};
    const order = [];
    (frm.doc.custom_items || []).forEach((row) => {
        if (!row.item_code) return;
        if (!groups[row.item_code]) { groups[row.item_code] = { proposed: 0, lc: 0, rate_usd: 0 }; order.push(row.item_code); }
        groups[row.item_code].proposed += (flt(row.custom_request_qty) || flt(row.qty));
        groups[row.item_code].lc += flt(row.qty);
        groups[row.item_code].rate_usd += flt(row.rate);
    });
    return order.map((item_code) => {
        const g = groups[item_code];
        return {
            item: item_code,
            proposed_quantity: g.proposed,
            lc_quantity: g.lc,
            remaining_quantity: g.proposed - g.lc,
            rate_usd: g.rate_usd,
            rate_bdt: 0
        };
    });
}

// Recompute per-row Remaining Qty (Request - Quantity) and the summary table,
// writing ONLY when a value actually differs so the form isn't dirtied needlessly.
function sync_computed_fields(frm) {
    let changed = false;

    (frm.doc.custom_items || []).forEach((row) => {
        if (flt(row.custom_request_qty)) {
            const want = flt(row.custom_request_qty) - flt(row.qty);
            if (flt(row.custom_remaining_qty) !== want) {
                row.custom_remaining_qty = want;
                changed = true;
            }
        }
    });

    const desired = compute_summary_rows(frm);
    const current = frm.doc.custom_items_summary || [];
    let summary_differs = current.length !== desired.length;
    if (!summary_differs) {
        for (let i = 0; i < desired.length; i++) {
            const c = current[i], d = desired[i];
            if (c.item !== d.item
                || flt(c.proposed_quantity) !== d.proposed_quantity
                || flt(c.lc_quantity) !== d.lc_quantity
                || flt(c.remaining_quantity) !== d.remaining_quantity
                || flt(c.rate_usd) !== d.rate_usd) {
                summary_differs = true;
                break;
            }
        }
    }
    if (summary_differs) {
        frm.clear_table('custom_items_summary');
        desired.forEach((d) => frm.add_child('custom_items_summary', d));
        changed = true;
    }

    if (changed) {
        frm.refresh_field('custom_items');
        frm.refresh_field('custom_items_summary');
    }
}