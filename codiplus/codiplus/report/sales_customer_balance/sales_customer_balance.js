// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Customer Balance"] = {
	"filters": [
		{
			fieldname: 'from_date',
			label: __('from_date'),
			fieldtype: 'Date',
			// depends_on: 'eval:doc.owner=="admin@admin.com"'
			default: frappe.datetime.get_today(),
			// reqd: 1
		},
		{
			fieldname: 'to_date',
			label: __('To Date'),
			fieldtype: 'Date',
			default: frappe.datetime.get_today(),
			// reqd: 1
		},
		{
			fieldname: "customer",
			label: __("customer"),
			fieldtype: "Link",
			options: "Customer",
		},{
			fieldname: "sales_partner",
			label: __("Sales Partner"),
			fieldtype: "Link",
			options: "Sales Partner",
		},

		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory",
		},
	]
};
