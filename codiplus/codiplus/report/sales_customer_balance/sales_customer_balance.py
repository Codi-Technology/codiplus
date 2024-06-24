
import frappe
from datetime import date
import datetime
from frappe.utils import add_to_date
from frappe.utils import getdate
from frappe.utils import pretty_date, now, add_to_date
from erpnext.accounts.utils import get_balance_on
from operator import itemgetter


def execute(filters=None):
	return Sales_Customer_Balance(filters).run()


class Sales_Customer_Balance(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})


	def run(self):
		self.get_columns()
		self.get_data()

		return self.columns , self.data


	def get_columns(self):
		#add columns wich appear data
		self.columns = [
			{
			"fieldname": "Posting Date",
			"fieldtype": "Data",
			"label": "Posting Date",
			"width": 200

		},
		{
			"fieldname": "Doctype",
			"fieldtype": "Data",
			"label": "Doctype",
			"width": 200

		},
		# {
		# 	"fieldname": "Creation Date",
		# 	"fieldtype": "Data",
		# 	"label": "Creation Date",
		# 	"width": 200

		# },
			{
			"fieldname": "Voucher Number",
			"fieldtype": "Dynamic Link",
			"label": "Voucher Number",
			"options": "Doctype",
			"width": 150
		},
			{
			"fieldname": "Customer",
			"fieldtype": "Link",
			"label": "Customer",
			"options":"Customer",
			"width": 150
		},
		{
			"fieldname": "Invoiced Amount",
			"fieldtype": "Currency",
			"label": "Invoiced Amount",
			"width": 200

		},
		{
			"fieldname": "Paid Amount",
			"fieldtype": "Currency",
			"label": "Paid Amount",
			"width": 200

		},
		{
			"fieldname": "Outstanding Amount",
			"fieldtype": "Currency",
			"label": "Outstanding Amount",
			"width": 200

		},



		]
		return self.columns


	def get_data(self):
		self.conditions, self.values, self.conditions_p, self.values_p, self.conditions_journal, self.values_journal = self.get_conditions(self.filters)

		self.data = []
		#? creaate method to get sales invoices
		data_dict = self.get_data_from_Sales_invoice(self.conditions, self.values)



		#? creaate method to get payment entry
		data_dict_p = self.get_data_from_payment_entry(self.conditions_p, self.values_p)


		#? creaate method to get Gjournal entry
		data_journal = self.get_data_from_journal_entry(self.conditions_journal, self.values_journal)

		data_dict = data_dict + data_dict_p + data_journal
		data_sort = sorted(data_dict, key=itemgetter('Posting Date'))

		# frappe.errprint(f'data_sort --------------> 1111 is ==>{data_sort} ----')


		# data_sort = sorted(data_dict,key = lambda i : i ["Posting Date"])

		#? init dictionary store balance to each customer
		self.balance_dict_cst = {}

		#? call method to sum outstand until from_date
		out_stand_before = self.get_cst_balance_to_fromDate()
		# if  self.filters.get("customer"):
		# 	conditions_d = "1=1 "
		# 	conditions_p = "1=1 "
		# 	conditions_journal = "1=1 "
		# 	values_d = dict()
		# 	values_p = dict()
		# 	values_journal = dict()

		# 	#for sales invoice
		# 	conditions_d += " AND g.party =  %(party)s  AND CAST(g.posting_date AS DATE) <  %(from_date)s "
		# 	values_d["party"] = self.filters.get("customer")
		# 	values_d["from_date"] = self.filters.get("from_date")
		# 	# for payment entry
		# 	conditions_p += " AND party =  %(party)s  AND CAST(p.posting_date AS DATE) <  %(from_date)s "
		# 	values_p["party"] = self.filters.get("customer")
		# 	values_p["from_date"] = self.filters.get("from_date")
		# 	# for journal entry
		# 	conditions_journal += " AND e.party =  %(party)s  AND CAST(j.posting_date AS DATE) <  %(from_date)s "
		# 	values_journal["party"] = self.filters.get("customer")
		# 	values_journal["from_date"] = self.filters.get("from_date")


		# 	#? creaate method to get sales invoices
		# 	data_dict_d2 = self.get_outstand_before_from_date(conditions_d,values_d,"Sales")
		# 	#? creaate method to get payment entry
		# 	data_dict_p2 = self.get_outstand_before_from_date(conditions_p,values_p,"PE")
		# 	#? creaate method to get Gjournal entry
		# 	data_dict_j2 = self.get_outstand_before_from_date(conditions_journal,values_journal,"JE")

		# 	#**addition resul
		# 	data_dict_oldest = data_dict_d2 + data_dict_p2 + data_dict_j2
		# 	#** excute method
		# 	specific_cst_balance = self.execute_query_data(data_dict_oldest)
		# 	specific_cst_balance['out_befor'] = 55555


		#? call exute method query
		specific_cst_balance = self.execute_query_data(data_sort)
		specific_cst_balance['outstand_before'] = out_stand_before
		frappe.errprint(f'all specific_cst_balance is ==>{specific_cst_balance}')
		data_sort.append(specific_cst_balance)


		self.data =data_sort
		# frappe.errprint(f'all data is ==>{self.data}')

		return  self.data

	def get_outstand_before_from_date(self,conditions,values,doctype):
		if doctype == "Sales":
			res = self.get_data_from_Sales_invoice(conditions,values)
		elif doctype == "PE":
			res = self.get_data_from_payment_entry(conditions,values)
		else:
			#? creaate method to get Gjournal entry
			res = self.get_data_from_journal_entry(conditions, values)
		return res


	def execute_query_data(self,data_sort):
		cst_balance_out_stand_before = {'specific_cst_balance':0,'out_stand_before':0}
		for item in data_sort:
			balance = self.balance_dict_cst.setdefault(item['Customer'],0.0)
			if abs(balance) >= 0 :
				if item['Doctype'] == 'Sales Invoice' :
					if item['is_return'] == 0:
						balance = balance + item['Debit']
						self.balance_dict_cst[item['Customer']] = balance
						item['Invoiced Amount'] = item['Debit']
						item['Outstanding Amount'] = balance
					else:
						balance = balance - item['Credit']
						item['Invoiced Amount'] = -item['Credit']
						self.balance_dict_cst[item['Customer']] = balance
						item['Outstanding Amount'] = balance
				elif item['Doctype'] == 'Journal Entry':
					if item['Debit'] > 0.0:
						# frappe.errprint(f'in debit --------------> 222 is ==>{item["Debit"]} ----')
						balance = balance + item['Debit']
						item['Invoiced Amount'] = item['Debit']
						self.balance_dict_cst[item['Customer']] = balance
						item['Outstanding Amount'] = balance
					else:
						# frappe.errprint(f'in credit --------------> 333 is ==>{item["Credit"]} ----')
						balance = balance - item['Credit']
						item['Invoiced Amount'] = 0.0
						item['Paid Amount'] = item['Credit']
						self.balance_dict_cst[item['Customer']] = balance
						item['Outstanding Amount'] = balance
				else:
					balance = balance - item['Paid Amount']
					self.balance_dict_cst[item['Customer']] = balance
					item['Outstanding Amount'] = balance
			else:
				if item['Doctype'] == 'Sales Invoice':
					# self.balance_dict_cst[item['Customer']] = item['Invoiced Amount']
					# item['Outstanding Amount'] = item['Invoiced Amount']
					if item['is_return'] == 0:
						balance = balance + item['Debit']
						item['Invoiced Amount'] = item['Debit']
						self.balance_dict_cst[item['Customer']] = balance
						item['Outstanding Amount'] = balance
					else:
						balance = balance - item['Credit']
						item['Invoiced Amount'] = -item['Credit']
						self.balance_dict_cst[item['Customer']] = balance
						item['Outstanding Amount'] = balance

				elif item['Doctype'] == 'Journal Entry':
					if item['Debit'] > 0.0:
						self.balance_dict_cst[item['Customer']] = item['Debit']
						item['Outstanding Amount'] = item['Debit']
					else:
						self.balance_dict_cst[item['Customer']] = item['Credit']
						item['Outstanding Amount'] = item['Credit']
				else:
					self.balance_dict_cst[item['Customer']] = item['Paid Amount']
					item['Outstanding Amount'] = item['Paid Amount']

		else:#after end foor loop
			if self.filters.get("customer"):
				customer_filter =  self.filters.get("customer")
				# get language
				lang = frappe.db.get_single_value('System Settings', 'language')
				specific_cst_balance = {}
				if  self.balance_dict_cst.get(customer_filter,""):
					cst_balance = self.balance_dict_cst[self.filters["customer"]]
					contact_query = """
						select phone from `tabContact Phone` where parenttype = 'Contact' AND parent IN (select parent from `tabDynamic Link` where parenttype='Contact' AND link_Doctype='Customer' AND link_name ='{cust_name}')
					""".format(cust_name=self.filters.get("customer"))
					contacts_data = frappe.db.sql(contact_query,as_dict=1)
					if  not contacts_data:
						contacts_data = [{'phone': ''}]

					address_query = """
						select address_line1,city from `tabAddress` where  name  IN (select parent from `tabDynamic Link` where parenttype='Address' AND link_Doctype='Customer' AND link_name = '{cust_name}')
					""".format(cust_name=self.filters.get("customer"))
					address_data = frappe.db.sql(address_query,as_dict=1)
					if not address_data:
						address_data = [{'address_line1': '', 'city': ''}]


					# get sales partnre and terriorty
					sales_partner, territory = frappe.db.get_value('Customer', {'name': self.filters.get("customer")}, ['default_sales_partner', 'territory'])
				else:
					cst_balance =  ''
					contacts_data = [{'phone': ''}]
					address_data = [{'address_line1': '', 'city': ''}]
					sales_partner = ''
					territory = ''

				specific_cst_balance = {"cst":cst_balance,"contacts_data":contacts_data,"address_data":address_data,"sales_partner":sales_partner,"territory":territory,'lang':lang}
				# frappe.errprint(f'specific_cst_balance is ******==>{specific_cst_balance}')


			else:
				specific_cst_balance = {"cst":''}
		return specific_cst_balance

	def get_cst_balance_to_fromDate(self):
		if  self.filters.get("customer"):
			conditions_d = "1=1 "
			conditions_p = "1=1 "
			conditions_journal = "1=1 "
			values_d = dict()
			values_p = dict()
			values_journal = dict()

			#for sales invoice
			conditions_d += " AND g.party =  %(party)s  AND CAST(g.posting_date AS DATE) <  %(from_date)s "
			values_d["party"] = self.filters.get("customer")
			values_d["from_date"] = self.filters.get("from_date")
			# for payment entry
			conditions_p += " AND party =  %(party)s  AND CAST(p.posting_date AS DATE) <  %(from_date)s "
			values_p["party"] = self.filters.get("customer")
			values_p["from_date"] = self.filters.get("from_date")
			# for journal entry
			conditions_journal += " AND e.party =  %(party)s  AND CAST(j.posting_date AS DATE) <  %(from_date)s "
			values_journal["party"] = self.filters.get("customer")
			values_journal["from_date"] = self.filters.get("from_date")


			#? creaate method to get sales invoices
			data_dict_d2 = self.get_outstand_before_from_date(conditions_d,values_d,"Sales")
			#? creaate method to get payment entry
			data_dict_p2 = self.get_outstand_before_from_date(conditions_p,values_p,"PE")
			#? creaate method to get Gjournal entry
			data_dict_j2 = self.get_outstand_before_from_date(conditions_journal,values_journal,"JE")

			#**addition resul
			data_dict_oldest = data_dict_d2 + data_dict_p2 + data_dict_j2
			#** excute method
			specific_cst_balance = self.execute_query_data(data_dict_oldest)
			specific_cst_balance['outstand_before'] = specific_cst_balance['cst']
			frappe.errprint(f'all specific_cst_balance is *******==>{specific_cst_balance}')
			return  specific_cst_balance['cst']


	def get_data_from_Sales_invoice(self,conditions = '' ,values = ''):
		query_test1 = """
		select g.name,g.party as `Customer`,g.voucher_type `Doctype`, g.debit as `Debit`, g.credit as `Credit`, s.is_return, g.voucher_no as `Voucher Number`,0.0 as `Paid Amount`,g.posting_date as `Posting Date` from `tabGL Entry` as g, `tabSales Invoice` as s where g.voucher_no = s.name and g.party_type = 'Customer' and g.is_cancelled = 0 and g.party <> '' and g.voucher_type ='Sales Invoice' and {conditions} group by g.voucher_no order by g.posting_date desc;
		""".format(conditions=conditions)
		# query_test = """
		# select d.name as `Voucher Number`,d.posting_date as `Posting Date`, DATE(d.creation) as `Creation Date`,d.customer as `Customer` ,d.grand_total as `Invoiced Amount` ,0.0 as `Paid Amount` ,'Sales Invoice' as `Doctype` from `tabSales Invoice` as d
		# WHERE {conditions} AND d.docstatus = '1'
		# """.format(conditions=conditions)
		data_dict= frappe.db.sql(query_test1,values=values,as_dict=1)
		# frappe.errprint(f'sales is ==>{data_dict}')

		return data_dict

	def get_data_from_payment_entry(self,conditions = '' ,values = ''):
		query_test_p = """
		select p.name as `Voucher Number`, p.posting_date as `Posting Date`,p.paid_amount as `Paid Amount`,DATE(p.creation) as `Creation Date`,
		p.party as `Customer`,0.0  as `Invoiced Amount`,'Payment Entry' as `Doctype`
		from `tabPayment Entry` as p
		WHERE {conditions} AND p.docstatus = '1'
		""".format(conditions=conditions)
		# frappe.errprint(f'query_test_p is ==>{query_test_p}')
		data_dict_p = frappe.db.sql(query_test_p,values=values,as_dict=1)

		return data_dict_p

	def get_data_from_journal_entry(self,conditions = '' ,values = ''):
		query_journal = """
		select DISTINCT j.name as `Voucher Number`,DATE(j.creation) as `Creation Date`,j.posting_date as `Posting Date`,0.0 as `Paid Amount`,j.total_credit as `Invoiced Amount`,e.parent,e.party as `Customer`,e.debit as `Debit`,e.credit as `Credit`,'Journal Entry' as `Doctype`  from `tabJournal Entry` j, `tabJournal Entry Account` e
		WHERE  j.docstatus = '1' AND j.name = e.parent AND e.party <>''  AND {conditions}
		""".format(conditions=conditions)

		#ORDER BY j.posting_date DESC Limit 8
		data_journal = frappe.db.sql(query_journal,values=values,as_dict=1)
		# frappe.errprint(f'data_journal is ==>{data_journal}')

		return data_journal


#! filters
	def get_conditions(self,filters):
		conditions = "1=1 "
		conditions_p = "1=1 "
		values_d = dict()
		values_p = dict()
		conditions_journal = "1=1 "
		values_journal = dict()

		if filters.get("customer"):
			#for sales invoice
			conditions += " AND g.party =  %(party)s "
			values_d["party"] = filters.get("customer")
			# for payment entry
			conditions_p += " AND party =  %(party)s "
			values_p["party"] = filters.get("customer")
			# for journal entry
			conditions_journal += " AND e.party =  %(party)s "
			values_journal["party"] = filters.get("customer")

		# if filters.get("to_date"):
		# 		conditions += " AND CAST(d.posting_date AS DATE) <=  %(to_date)s "
		# 		values_d["to_date"] = filters.get("to_date")

		# 		conditions_p += " AND CAST(p.posting_date AS DATE) <=  %(to_date)s "
		# 		values_p["to_date"] = filters.get("to_date")

		# 		conditions_journal += " AND CAST(j.posting_date AS DATE) <=  %(to_date)s "
		# 		values_journal["to_date"] = filters.get("to_date")

		if filters.get("from_date"):
			if filters.get("from_date") and filters.get("to_date"):
				# max_interval = add_to_date(filters.get("from_date"), months=3)
				# if filters.get("to_date") <= max_interval:
				conditions += " AND CAST(g.posting_date AS DATE) >= %(from_date)s  AND CAST(g.posting_date AS DATE) <= %(to_date)s"
				values_d["from_date"] = filters.get("from_date")
				values_d["to_date"] = filters.get("to_date")
				#for payment
				conditions_p += " AND CAST(p.posting_date AS DATE) >= %(from_date)s  AND CAST(p.posting_date AS DATE) <= %(to_date)s"
				values_p["from_date"] = filters.get("from_date")
				values_p["to_date"] = filters.get("to_date")
				# for journal
				conditions_journal += " AND CAST(j.posting_date AS DATE) >= %(from_date)s  AND CAST(j.posting_date AS DATE) <= %(to_date)s"
				values_journal["from_date"] = filters.get("from_date")
				values_journal["to_date"] = filters.get("to_date")
				# else:
				# 	frappe.throw(title='Notification',msg='Max Interval Date should be less than 3 month')

			elif filters.get("from_date"):
				conditions += " AND CAST(g.posting_date AS DATE) =  %(from_date)s "
				values_d["from_date"] = filters.get("from_date")

				conditions_p += " AND CAST(p.posting_date AS DATE) =  %(from_date)s "
				values_p["from_date"] = filters.get("from_date")

				conditions_journal += " AND CAST(j.posting_date AS DATE) =  %(from_date)s "
				values_journal["from_date"] = filters.get("from_date")

		if filters.get("sales_partner") or filters.get("territory"):
			#?for both Territory and sales person
			if filters.get("sales_partner") and filters.get("territory"):
				# for saes invoice
				conditions += " AND g.party IN (select name from tabCustomer where default_sales_partner = %(sales_partner)s AND territory =  %(territory)s ) "
				values_d["territory"] = filters.get("territory")
				values_d["sales_partner"] = filters.get("sales_partner")
				# for Payment
				conditions_p += " AND p.party IN (select name from tabCustomer where default_sales_partner = %(sales_partner)s AND territory =  %(territory)s) "
				values_p["territory"] = filters.get("territory")
				values_p["sales_partner"] = filters.get("sales_partner")
				# for journal entry
				conditions_journal += " AND e.party IN (select name from tabCustomer where default_sales_partner = %(sales_partner)s AND territory =  %(territory)s)"
				values_journal["territory"] = filters.get("territory")
				values_journal["sales_partner"] = filters.get("sales_partner")

			#** for sales partner
			elif filters.get("sales_partner"):
				conditions += " AND g.party IN (select name from tabCustomer where default_sales_partner = %(sales_partner)s ) "
				values_d["sales_partner"] = filters.get("sales_partner")
				# for Payment
				conditions_p += " AND p.party IN (select name from tabCustomer where default_sales_partner = %(sales_partner)s ) "
				values_p["sales_partner"] = filters.get("sales_partner")
				# for journal entry
				conditions_journal += " AND e.party IN (select name from tabCustomer where default_sales_partner = %(sales_partner)s ) "
				values_journal["sales_partner"] = filters.get("sales_partner")

			#**
			elif  filters.get("territory"):
				# for saes invoice
				conditions += " AND g.party IN (select name from tabCustomer where territory =  %(territory)s ) "
				values_d["territory"] = filters.get("territory")
				# for Payment
				conditions_p += " AND p.party IN (select name from tabCustomer where territory =  %(territory)s) "
				values_p["territory"] = filters.get("territory")
				# for journal entry
				conditions_journal += " AND e.party IN (select name from tabCustomer where territory =  %(territory)s)"
				values_journal["territory"] = filters.get("territory")

		return conditions, values_d, conditions_p, values_p, conditions_journal, values_journal



