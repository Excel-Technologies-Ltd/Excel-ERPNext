// Copyright (c) 2026, Castlecraft Ecommerce Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Project Wise Profit', {
    
    // Trigger when the work_order field is changed
    work_order: function(frm) {
        if (frm.doc.work_order) {
            
            // 1. Fetch total_cost_amount (iou_voucher) from Live Project Dashboard
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

            // 2. Fetch total_final_bill_amount (invoice_total) from Billing and Collection
            frappe.db.get_value(
                'Billing and Collection',
                { 'work_order': frm.doc.work_order },
                'invoice_total'
            ).then(r => {
                if (r.message && r.message.invoice_total !== undefined) {
                    frm.set_value('total_final_bill_amount', r.message.invoice_total);
                } else {
                    frm.set_value('total_final_bill_amount', 0);
                }
            });

        } else {
            // Reset both values to 0 if the work_order is cleared
            frm.set_value('total_cost_amount', 0);
            frm.set_value('total_final_bill_amount', 0);
        }
    },

    // Trigger calculation if total final bill amount is manually changed (or fetched from DB)
    total_final_bill_amount: function(frm) {
        calculate_profit_and_margin(frm);
    },

    // Trigger calculation automatically whenever total_cost_amount is updated
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
    // Check if final_bill is not zero to prevent a "division by zero" error
    if (final_bill !== 0) {
        margin = (profit_loss / final_bill) * 100;
    }
    
    // Set both values into the form
    frm.set_value({
        'profitloss': profit_loss,
        'margin': margin
    });
}