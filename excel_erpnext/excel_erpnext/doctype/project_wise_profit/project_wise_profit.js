// Copyright (c) 2026, Castlecraft Ecommerce Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Project Wise Profit', {
    
    // Trigger when the work_order field is changed
    work_order: function(frm) {
        if (frm.doc.work_order) {
            // Fetch iou_voucher from Live Project Dashboard where wo_number == work_order
            frappe.db.get_value(
                'Live Project Dashboard', 
                { 'wo_number': frm.doc.work_order }, 
                'iou_voucher'
            ).then(r => {
                if (r.message && r.message.iou_voucher !== undefined) {
                    frm.set_value('total_cost_amount', r.message.iou_voucher);
                } else {
                    frm.set_value('total_cost_amount', 0);
                }
            });
        } else {
            frm.set_value('total_cost_amount', 0);
        }
    },

    // Trigger calculation if total final bill amount is manually changed
    total_final_bill_amount: function(frm) {
        calculate_profit_and_margin(frm);
    },

    // Trigger calculation automatically whenever total_cost_amount is updated (either manually or via the DB fetch)
    total_cost_amount: function(frm) {
        calculate_profit_and_margin(frm);
    }
});

function calculate_profit_and_margin(frm) {
    // flt() ensures that empty values are treated as 0 instead of causing NaN errors
    let final_bill = flt(frm.doc.total_final_bill_amount);
    let total_cost = flt(frm.doc.total_cost_amount);
    
    // 1. Calculate Profit/Loss
    let profit_loss = final_bill - total_cost;
    
    // 2. Calculate Margin
    let margin = 0;
    // Check if final_bill is not zero to prevent a "division by zero" error (Infinity/NaN)
    if (final_bill !== 0) {
        margin = (profit_loss / final_bill) * 100;
    }
    
    // Set both values into the form
    frm.set_value({
        'profitloss': profit_loss,
        'margin': margin
    });
}