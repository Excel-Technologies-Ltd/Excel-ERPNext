// Copyright (c) 2026, Castlecraft Ecommerce Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Excel Party Set Up Form', {
	refresh: function (frm) {
		frm.trigger('toggle_conditional_fields');
	},

	bank_loan: function (frm) {
		frm.trigger('toggle_conditional_fields');
		if (frm.doc.bank_loan !== 'Yes') {
			frm.set_value('bank_name', '');
		}
	},

	business_with_other_partners: function (frm) {
		frm.trigger('toggle_conditional_fields');
		if (frm.doc.business_with_other_partners !== 'Others') {
			frm.set_value('party_name', '');
		}
	},

	toggle_conditional_fields: function (frm) {
		frm.toggle_reqd('bank_name', frm.doc.bank_loan === 'Yes');
		frm.toggle_reqd('party_name', frm.doc.business_with_other_partners === 'Others');
	}
});
