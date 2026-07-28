// Copyright (c) 2026, Castlecraft Ecommerce Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Billing and Collection', {
    refresh: function(frm) {
        // Optional: Recalculate totals when the document is opened
        calculate_totals(frm);
    },
    
    // Trigger calculation when a row is ADDED
    // REPLACE 'billing_and_collections' with the actual fieldname
    billing_and_collections_add: function(frm, cdt, cdn) {
        calculate_totals(frm);
    },
    
    // Trigger calculation when a row is REMOVED
    // REPLACE 'billing_and_collections' with the actual fieldname
    billing_and_collections_remove: function(frm, cdt, cdn) {
        calculate_totals(frm);
    }
});

frappe.ui.form.on('Billing and Collection Details', {
    invoice_amount: function(frm, cdt, cdn) {
        calculate_outstanding(frm, cdt, cdn);
    },
    
    collection_amount: function(frm, cdt, cdn) {
        calculate_outstanding(frm, cdt, cdn);
    }
});

// Calculate Outstanding for a specific row
function calculate_outstanding(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    let invoice_amt = flt(row.invoice_amount);
    let collection_amt = flt(row.collection_amount);
    let outstanding_amt = invoice_amt - collection_amt;
    
    // Update the row's outstanding field
    frappe.model.set_value(cdt, cdn, 'outstanding', outstanding_amt).then(() => {
        // Once the row is updated, update the parent totals
        calculate_totals(frm);
    });
}

// Calculate Grand Totals for the Parent Document
function calculate_totals(frm) {
    let total_invoice = 0;
    let total_collection = 0;
    let total_outstanding = 0;
    
    // REPLACE 'billing_and_collections' with the actual fieldname of the table
    let child_table = frm.doc.billing_and_collections;

    // Loop through each row in the table and add to the totals
    if (child_table && child_table.length > 0) {
        child_table.forEach(row => {
            total_invoice += flt(row.invoice_amount);
            total_collection += flt(row.collection_amount);
            total_outstanding += flt(row.outstanding);
        });
    }

    // Set the values on the parent document
    frm.set_value('invoice_total', total_invoice);
    frm.set_value('collection_total', total_collection);
    frm.set_value('outstanding_total', total_outstanding);
}