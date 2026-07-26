// Copyright (c) 2026, Castlecraft Ecommerce Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Live Project Dashboard', {
	refresh: function(frm) {
		fetch_iou_totals(frm);
	},
	wo_number: function(frm) {
		fetch_iou_totals(frm);
	}
});

function fetch_iou_totals(frm) {
	if (!frm.doc.wo_number) {
		calculate_totals(frm);
		return;
	}

	frappe.call({
		method: 'excel_erpnext.excel_erpnext.doctype.live_project_dashboard.live_project_dashboard.get_iou_totals',
		args: {
			wo_number: frm.doc.wo_number
		},
		callback: function(r) {
			if (r.message) {
				frm.set_value({
					approved_iou: r.message.approved_iou,
					pending_iou: r.message.pending_iou,
					iou_voucher: r.message.iou_voucher,
				});
			}
			calculate_totals(frm);
		}
	});
}

function calculate_totals(frm) {
	let total_running_cost = flt(frm.doc.others_cost)
		+ flt(frm.doc.material_cost)
		+ flt(frm.doc.sub_contractor_cost)
		+ flt(frm.doc.labor_cost)
		+ flt(frm.doc.team_cost);

	let actual_cost = total_running_cost;

	let profitloss_amount = flt(frm.doc.total_wo_value) - actual_cost;

	let profit_percentage = flt(frm.doc.total_wo_value)
		? (profitloss_amount / flt(frm.doc.total_wo_value)) * 100
		: 0;

	let remaining_budget = flt(frm.doc.total_budget_cost) - actual_cost;

	let remaining_iou = actual_cost - (flt(frm.doc.approved_iou) + flt(frm.doc.pending_iou));

	let pending_voucher = flt(frm.doc.approved_iou) - flt(frm.doc.iou_voucher);

	frm.set_value({
		total_running_cost: total_running_cost,
		actual_cost: actual_cost,
		profitloss_amount: profitloss_amount,
		profit_percentage: profit_percentage,
		remaining_budget: remaining_budget,
		remaining_iou: remaining_iou,
		pending_voucher: pending_voucher,
	});
}
