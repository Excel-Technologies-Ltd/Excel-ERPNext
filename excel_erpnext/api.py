import requests
import base64
from io import BytesIO
from PIL import Image, ImageOps
from weasyprint import HTML
from frappe.utils import today, add_days, cint

# Configuration for API requests
API_BASE_URL = "https://your-frappe-instance/api/resource"  # Replace with your Frappe instance URL
API_HEADERS = {
    "Authorization": "token your_api_key:your_api_secret",  # Replace with your actual API token
    "Content-Type": "application/json"
}

# Insert JSON data into Frappe
def insert_json(data):
    # Insert UOM if it doesn't exist
    for item in data.get("items"):
        uom_name = item.get("uom")
        if not check_existence("UOM", uom_name):
            insert_doc("UOM", {"uom_name": uom_name})

    # Insert Item Group if it doesn't exist
    for item in data.get("items"):
        item_group_name = item.get("item_group")
        if not check_existence("Item Group", item_group_name):
            insert_doc("Item Group", {"item_group_name": item_group_name})

    # Insert Territory if it doesn't exist
    territory_name = data.get("territory")
    if not check_existence("Territory", territory_name):
        insert_doc("Territory", {"territory_name": territory_name})

    # Create company abbreviation
    company_name = data.get("company")
    company_abbr = "".join([word[0].upper() for word in company_name.split()])
    if not check_existence("Company", company_name):
        insert_doc("Company", {
            "company_name": company_name,
            "abbr": company_abbr,
            "default_currency": data.get("currency"),
            "country": "India"
        })

    # Insert Price List if it doesn't exist
    price_list_name = data.get("selling_price_list")
    if not check_existence("Price List", price_list_name):
        insert_doc("Price List", {
            "price_list_name": price_list_name,
            "currency": data.get("currency"),
            "buying": 1,
            "selling": 1,
            "price_not_uom_dependent": 1,
            "enabled": 1
        })

    # Insert Customer Group if it doesn't exist
    customer_group_name = data.get("customer_group")
    if not check_existence("Customer Group", customer_group_name):
        insert_doc("Customer Group", {"customer_group_name": customer_group_name})

    # Insert Currency if it doesn't exist
    currency_name = data.get("currency")
    if not check_existence("Currency", currency_name):
        insert_doc("Currency", {"currency_name": currency_name, "enabled": 1})

    # Insert items
    for item in data.get("items"):
        if not check_existence("Item", item.get("item_code")):
            insert_doc("Item", {
                "item_code": item.get("item_code"),
                "item_name": item.get("item_name"),
                "description": item.get("description"),
                "is_nil_exempt": item.get("is_nil_exempt"),
                "is_non_gst": item.get("is_non_gst"),
                "item_group": item.get("item_group"),
                "image": item.get("image"),
                "qty": item.get("qty"),
                "conversion_factor": item.get("conversion_factor"),
                "stock_uom": item.get("stock_uom"),
                "has_excel_serials": item.get("has_excel_serials")
            })

    # Insert Excel Delivery Note
    delivery_note_data = {
        "doctype": "Excel Delivery Note",
        "naming_series": data.get("naming_series"),
        "customer": data.get("customer"),
        "customer_name": data.get("customer_name"),
        "company": data.get("company"),
        "posting_date": data.get("posting_date"),
        "posting_time": data.get("posting_time"),
        "is_return": data.get("is_return"),
        "contact_email": data.get("contact_email"),
        "currency": data.get("currency"),
        "conversion_rate": data.get("conversion_rate"),
        "selling_price_list": data.get("selling_price_list"),
        "price_list_currency": data.get("price_list_currency"),
        "plc_conversion_rate": data.get("plc_conversion_rate"),
        "total_qty": data.get("total_qty"),
        "base_total": data.get("base_total"),
        "base_net_total": data.get("base_net_total"),
        "total": data.get("total"),
        "net_total": data.get("net_total"),
        "base_grand_total": data.get("base_grand_total"),
        "customer_group": data.get("customer_group"),
        "territory": data.get("territory"),
        "pricing_rules": data.get("pricing_rules"),
        "packed_items": data.get("packed_items"),
        "taxes": data.get("taxes"),
        "sales_team": data.get("sales_team"),
        "isSynced": data.get("isSynced"),
        "status": data.get("status"),
        "items": [
            {
                "item_code": item.get("item_code"),
                "item_name": item.get("item_name"),
                "description": item.get("description"),
                "item_group": item.get("item_group"),
                "image": item.get("image"),
                "qty": item.get("qty"),
                "stock_qty": item.get("stock_qty"),
                "price_list_rate": item.get("price_list_rate"),
                "base_price_list_rate": item.get("base_price_list_rate"),
                "rate": item.get("rate"),
                "amount": item.get("amount"),
                "stock_uom": item.get("stock_uom"),
                "uom": item.get("uom"),
                "conversion_factor": item.get("conversion_factor")
            } for item in data.get("items")
        ]
    }
    insert_doc("Excel Delivery Note", delivery_note_data)


# Check if a document exists
def check_existence(doctype, name):
    url = f"{API_BASE_URL}/{doctype}/{name}"
    response = requests.get(url, headers=API_HEADERS)
    return response.status_code == 200

# Insert a document
def insert_doc(doctype, data):
    url = f"{API_BASE_URL}/{doctype}"
    response = requests.post(url, headers=API_HEADERS, json=data)
    if response.status_code == 200:
        print(f"{doctype} {data.get('name', '')} inserted successfully.")
    else:
        print(f"Error inserting {doctype}: {response.text}")

# Convert document to image and return as base64 inline HTML
def show_pdf_as_image(doctype, name, format=None, no_letterhead=0, language=None, letterhead=None, image_format="PNG"):
    try:
        # Get the HTML content of the document
        html_content = get_print_content(doctype, name, format, no_letterhead, language, letterhead)

        # Convert HTML to PNG
        png_bytes = BytesIO()
        document = HTML(string=html_content)
        document.render().write_png(png_bytes, resolution=96)

        # Process image
        png_bytes.seek(0)
        image = Image.open(png_bytes)
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        image = ImageOps.crop(image, border=20)

        # Convert image to base64
        output_image_bytes = BytesIO()
        image.save(output_image_bytes, format=image_format.upper())
        base64_image = base64.b64encode(output_image_bytes.getvalue()).decode('utf-8')
        
        # Render HTML with embedded image
        html = f"""
            <html>
                <body>
                    <img src="data:image/{image_format.lower()};base64,{base64_image}" />
                </body>
            </html>
        """
        return html

    except Exception as e:
        print(f"Error in show_pdf_as_image: {str(e)}")
        return f"Error: {str(e)}"

# Get print content via API
def get_print_content(doctype, name, format, no_letterhead, language, letterhead):
    url = f"{API_BASE_URL}/printview"
    params = {
        "doctype": doctype,
        "name": name,
        "format": format,
        "no_letterhead": no_letterhead,
        "language": language,
        "letterhead": letterhead
    }
    response = requests.get(url, headers=API_HEADERS, params=params)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error fetching print content: {response.text}")
        return ""
import frappe
from frappe import _
from frappe.translate import print_language
from pdf2image import convert_from_bytes
import io
@frappe.whitelist(allow_guest=True)
def download_pdf(doctype, name, format=None, doc=None, no_letterhead=0, language=None, letterhead=None):
	doc = doc or frappe.get_doc(doctype, name)


	with print_language(language):
		pdf_file = frappe.get_print(
			doctype, name, format, doc=doc, as_pdf=True, letterhead=letterhead, no_letterhead=no_letterhead
		)

	frappe.local.response.filename = "{name}.pdf".format(name=name.replace(" ", "-").replace("/", "-"))
	frappe.local.response.filecontent = pdf_file
	frappe.local.response.type = "pdf"
 
 
import frappe
from frappe import _
from frappe.translate import print_language
from pdf2image import convert_from_bytes
import io



@frappe.whitelist(allow_guest=True)
def download_image(doctype, name, format=None, doc=None, no_letterhead=0, language=None, letterhead=None):
    doc = doc or frappe.get_doc(doctype, name)

    # Generate the PDF
    with print_language(language):
        pdf_file = frappe.get_print(
            doctype, name, format, doc=doc, as_pdf=True, letterhead=letterhead, no_letterhead=no_letterhead
        )

    # Convert PDF to Image (PNG)
    images = convert_from_bytes(pdf_file)  # This returns a list of PIL images for each PDF page
    if not images:
        frappe.throw(_("Could not generate image from PDF."))

    # Take the first page image if only one is needed
    image = images[0]
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    image_content = image_bytes.getvalue()

    # Set headers and response for image content
    frappe.local.response.filename = f"{name}.png"
    frappe.local.response.filecontent = image_content
    # frappe.local.response.type = "image/png"  # Required for custom headers to take effect
    frappe.local.response.headers = {
        "Content-Type": "image/png",
        "Content-Disposition": f"inline; filename={name}.png"
    }

#     return
import frappe
from frappe import _
from frappe.translate import print_language
from pdf2image import convert_from_bytes
import io
import base64

@frappe.whitelist(allow_guest=True)
def render_html_image(doctype, name, format=None, doc=None, no_letterhead=0, language=None, letterhead=None):
    doc = doc or frappe.get_doc(doctype, name)

    # Generate the PDF
    with print_language(language):
        pdf_file = frappe.get_print(
            doctype, name, format, doc=doc, as_pdf=True, letterhead=letterhead, no_letterhead=no_letterhead
        )

    # Convert PDF to Image (PNG)
    images = convert_from_bytes(pdf_file)
    if not images:
        frappe.throw(_("Could not generate image from PDF."))

    # Take the first page image if only one is needed
    image = images[0]
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    image_content = image_bytes.getvalue()

    # Convert the image content to a base64 string
    image_base64 = base64.b64encode(image_content).decode('utf-8')

    # Prepare the HTML content with the embedded image
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{name} Image</title>
    </head>
    <body>
        <h1>Image for {name}</h1>
        <img src="data:image/png;base64,{image_base64}" alt="Rendered Image">
    </body>
    </html>
    """

    # Set response headers to render HTML
    frappe.local.response.filecontent = html_content
    frappe.local.response.type = "pdf"  # Set response type to HTML

    return

@frappe.whitelist()
def update_item_bottom_price(item_code, price):
    try:
        # Check if the item price exists for the specified criteria
        check_item_price = frappe.db.exists('Item Price', {"item_code": item_code, "price_list": 'Bottom Price',"selling":1})
        print("check_item_price",check_item_price)
        if not check_item_price:
            new_doc= frappe.get_doc({"doctype":"Item Price","item_code":item_code,"price_list":"Bottom Price","selling":1,"price_list_rate":price})
            new_doc.insert()
            frappe.db.commit()
            return {"status": "success", "message": "Price created successfully","item":new_doc}
        
        # Update the price if the item exists
        item_price= frappe.get_doc('Item Price', check_item_price)
        print(item_price)
        item_price.price_list_rate = price
        item_price.save()
        frappe.db.commit()
        # frappe.db.set_value('Item Price', check_item_price, 'price_list_rate', price)
        # frappe.db.commit()
        return {"status": "success", "message": "Price updated successfully","item":item_price}
    
    except frappe.exceptions.DoesNotExistError:
        return {"status": "error", "message": "Item Price document does not exist"}
    except frappe.exceptions.ValidationError as e:
        return {"status": "error", "message": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

    
    
@frappe.whitelist()
def generate_token(email):
    """
    Generate API key and secret for a user based on their email.

    Args:
        email (str): The email of the user (sent in the request body).

    Returns:
        dict: A dictionary containing the API key and secret.

    Raises:
        frappe.ValidationError: If the email is invalid or the user is disabled.
    """
    allowed_roles = ["System Manager"]  # Define allowed roles
    user_roles = frappe.get_roles(frappe.session.user)

    if not any(role in allowed_roles for role in user_roles):
        frappe.throw(
            "You are not authorized to access this resource", frappe.PermissionError
        )

    # Check if the user exists with the provided email
    user = frappe.db.get_value("User", {"email": email}, "name")
    if not user:
        frappe.throw("Invalid email")

    # Fetch the user document
    user_doc = frappe.get_doc("User", user)

    # Validate if the user is active
    if not user_doc.enabled:
        frappe.throw("User is disabled")

    # Generate API key and secret if not already generated
    if not user_doc.api_key:
        user_doc.api_key = frappe.generate_hash(length=15)
    if not user_doc.api_secret:
        user_doc.api_secret = frappe.generate_hash(length=15)
        user_doc.save(ignore_permissions=True)

    # Return the API key and secret
    return {
        "api_key": user_doc.api_key,
        "api_secret": user_doc.get_password("api_secret"),
    }

@frappe.whitelist(allow_guest=True)
def get_All_Sales_And_Taxes_Details():
    # Get all Sales Taxes and Charges Template records with their child table data
    sales_templates = frappe.get_all(
        "Sales Taxes and Charges Template",
        fields=["name", "title", "is_default", "company", "disabled"],
        as_list=False,
    )
    
    # Fetch child table (taxes) data for each template
    for template in sales_templates:
        taxes = frappe.get_all(
            "Sales Taxes and Charges",
            filters={"parent": template.name},
            fields=["idx", "description", "rate", "tax_amount", "total", "tax_amount_after_discount_amount", "base_tax_amount", "base_total", "parent", "base_tax_amount_after_discount_amount"],
            order_by="idx"
        )
        template["taxes"] = taxes
    
    return sales_templates

@frappe.whitelist()
def get_sales_and_delivery_data_by_id(sales_invoice_id):
    # Construct SQL query
    query = """
    SELECT 
        sii.item_code,
        SUM(sii.qty) AS sales_qty,
        SUM(sii.stock_qty) AS sales_stock_qty,
        sii.parent AS sales_invoice_id,
        COALESCE(SUM(dni.qty), 0) AS delivery_qty,
        COALESCE(SUM(dni.stock_qty), 0) AS delivery_stock_qty,
        (SUM(sii.qty) - COALESCE(SUM(dni.qty), 0)) AS remaining,
        sii.warehouse as warehouse
    FROM 
        `tabSales Invoice Item` sii
    LEFT JOIN 
        `tabDelivery Note Item` dni
        ON sii.item_code = dni.item_code
        AND dni.against_sales_invoice = %s
        AND dni.qty > 0
    WHERE 
        sii.parent = %s
    GROUP BY 
        sii.item_code, sii.parent;
    """
    
    # Execute the query and fetch data
    data = frappe.db.sql(query, (sales_invoice_id, sales_invoice_id), as_dict=True)
    
    return data
    
    
@frappe.whitelist()
def get_cheque_in_hand(sales_person_email=None, start_date='2025-01-01', end_date='2025-12-31'):
    """
    Get transaction amounts grouped by sales person.

    :param sales_person_email: Single sales person email or list of sales person emails (optional)
    :param start_date: Start date for filtering transactions (required)
    :param end_date: End date for filtering transactions (required)
    :return: Dictionary with transaction data grouped by sales person
    """
    
    # Ensure required parameters are present
    if not start_date or not end_date:
        frappe.throw('start_date and end_date are required parameters')
    
    # Base SQL query
    sql_query = """
        SELECT 
            pmnt.name,
            pmnt.reference_no,
            pmnt.paid_amount,
            cu.excel_sales_person_name,
            cu.customer_name,
            cu.excel_sales_person_email,
            st.sales_person
        FROM 
            `tabPayment Entry` AS pmnt
        LEFT JOIN 
            `tabCustomer` AS cu ON pmnt.party = cu.name
        LEFT JOIN 
            `tabSales Team` AS st ON cu.name = st.parent
        WHERE 
            pmnt.mode_of_payment = 'Cheque in Hand'
        AND pmnt.docstatus = 0
        AND pmnt.reference_date BETWEEN %(start_date)s AND %(end_date)s
    """
    
    # Parameters dictionary
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    if sales_person_email:
        if isinstance(sales_person_email, str):  # Convert single item string to a list
            sales_person_email = [sales_person_email]
        elif not isinstance(sales_person_email, list):  # Ensure sales_person_email is a list
            frappe.throw("Invalid 'sales_person_email' format. It should be a list of emails.")
        
        # Add filter for sales person email
        sql_query += " AND cu.excel_sales_person_email IN %(sales_person_email)s"
        params["sales_person_email"] = tuple(sales_person_email)
    
    # Execute query
    try:
        result = frappe.db.sql(sql_query, params, as_dict=True)
        
        # Group results by sales person
        # grouped_result = {}
        # for row in result:
        #     sales_person = row["sales_person"]
        #     if sales_person not in grouped_result:
        #         grouped_result[sales_person] = []
        #     grouped_result[sales_person].append({
        #         "name": row["name"],
        #         "reference_no": row["reference_no"],
        #         "paid_amount": row["paid_amount"],
        #         "excel_sales_person_name": row["excel_sales_person_name"],
        #         "customer_name": row["customer_name"],
        #         "excel_sales_person_email": row["excel_sales_person_email"]
        #     })
        
        # Return response
        frappe.response['message'] = {
            'data': result,
            'total_count': len(result)  # Total number of records
        }
    
    except Exception as e:
        frappe.response['message'] = f"Error executing query: {str(e)}"
        frappe.log_error(f"Error in get_cheque_in_hand: {str(e)}")



@frappe.whitelist()
def get_cheque_collection(sales_person_email, start_date=None, end_date=None):
    """
    Get cheque collections for a given sales person within a date range.

    :param sales_person_email: Email of the sales person (required)
    :param start_date: Start date for filtering transactions (default: today)
    :param end_date: End date for filtering transactions (default: today)
    :return: List of cheque collections
    """
    
    if not sales_person_email:
        frappe.throw("sales_person_email is required")

    # Default to today's date if no dates are provided
    if not start_date:
        start_date = frappe.utils.today()
    if not end_date:
        end_date = frappe.utils.today()

    # SQL Query
    sql_query = """
        SELECT 
            pmnt.name,
            pmnt.reference_no,
            pmnt.paid_amount,
            cu.excel_sales_person_name,
            cu.customer_name,
            cu.excel_sales_person_email
        FROM 
            `tabPayment Entry` AS pmnt
        LEFT JOIN 
            `tabCustomer` AS cu ON pmnt.party = cu.name
        WHERE 
            pmnt.party_type = 'Customer'
            AND pmnt.docstatus = 1
            AND pmnt.posting_date BETWEEN %(start_date)s AND %(end_date)s
            AND cu.excel_sales_person_email = %(sales_person_email)s
    """

    # Query parameters
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "sales_person_email": sales_person_email
    }

    # Execute the query
    try:
        result = frappe.db.sql(sql_query, params, as_dict=True)
        
        # Return response
        frappe.response['message'] = {
            "data": result,
            "total_count": len(result)
        }

    except Exception as e:
        frappe.response['message'] = f"Error executing query: {str(e)}"
        frappe.log_error(f"Error in get_cheque_collection: {str(e)}")



@frappe.whitelist()
def get_doctype_count():
    """
    Get the count of records for a given Doctype.

    :return: Count of records in the specified Doctype
    """
    
    # Fetch Doctype from request
    doctype = frappe.form_dict.get("doctype")
    
    if not doctype:
        frappe.throw("Doctype name missing")
    
    try:
        # Get the count of records in the specified Doctype using get_list
        count = len(frappe.get_list(doctype, filters={}, ignore_permissions=False))
        
        # Return response
        frappe.response['message'] = {doctype: count}
    
    except Exception as e:
        frappe.response['message'] = f"Error fetching count: {str(e)}"
        frappe.log_error(f"Error in get_doctype_count: {str(e)}")


@frappe.whitelist(allow_guest=True)
def get_stock_reconciliation(customer=None, start_date=None, end_date=None, items=None):
    """
    Get sales invoice item details based on customer, start_date, end_date, and optional item codes.

    :return: List of sales invoice items matching the criteria.
    """


    # Check if required parameters are present
    if not customer or not start_date or not end_date:
        frappe.throw('Customer, start_date, and end_date are required parameters')

    # Base SQL query
    sql_query = """
        SELECT sii.*
        FROM `tabSales Invoice` as si
        LEFT JOIN `tabSales Invoice Item` as sii ON si.name = sii.parent
        WHERE 
            si.customer = %(customer)s
            AND si.docstatus = 1
            AND si.name LIKE '%%SINV%%'
            AND si.posting_date BETWEEN %(start_date)s AND %(end_date)s
    """

    # Parameters dictionary
    params = {
        "customer": customer,
        "start_date": start_date,
        "end_date": end_date
    }

    # Handle 'items' correctly
    if items:
        if isinstance(items, str):  # Convert single item string to a list
            items = [items]
        elif not isinstance(items, list):  # Ensure items is a list
            frappe.throw("Invalid 'items' format. It should be a list of item codes.")

        sql_query += " AND sii.item_code IN %(items)s"
        params["items"] = tuple(items)  # Convert to tuple for SQL compatibility

    # Execute the query safely
    try:
        result = frappe.db.sql(sql_query, params, as_dict=True)
        frappe.response['message'] = result
    except Exception as e:
        frappe.response['message'] = f"Error executing query: {str(e)}"
        frappe.log_error(f"Error in get_stock_reconciliation: {str(e)}")


@frappe.whitelist()
def monthly_sales_by_sales_person(sales_person_email="akramul.sales@excelbd.com", interval_days=100):
    interval_days = cint(interval_days)

    query = """
    SELECT 
        cu.excel_sales_person_email AS sales_person,
        DATE_FORMAT(si.posting_date, '%%Y-%%m') AS sales_month,
        SUM(si.grand_total) AS total_sales
    FROM `tabSales Invoice` AS si
    LEFT JOIN `tabCustomer` AS cu 
        ON si.customer = cu.name
    WHERE si.docstatus = 1
    AND si.name LIKE '%%SINV%%'
    AND cu.excel_sales_person_email = %(sales_person_email)s
    AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL %(interval_days)s DAY)
    GROUP BY cu.excel_sales_person_email, sales_month
    ORDER BY sales_month DESC
    """

    data = frappe.db.sql(query, {
        'sales_person_email': sales_person_email,
        'interval_days': interval_days
    }, as_dict=True)

    return data


@frappe.whitelist()
def non_billed_brands(sales_person_email="akramul.sales@excelbd.com", interval_days=30):
    """
    Fetches non-billed brands for a sales person within a given interval.
    
    :param sales_person_email: The sales person's email (linked via excel_sales_person_email in Customer)
    :param interval_days: Number of days to check for recent invoices (default 30 days)
    :return: List of dicts containing brand, last_invoice_date, and sales_person
    """
    
    query = """
        SELECT 
            sii.brand,
            MAX(si.posting_date) AS last_invoice_date,
            sp.name AS sales_person
        FROM `tabSales Invoice` AS si
        LEFT JOIN `tabSales Invoice Item` AS sii 
            ON si.name = sii.parent
        LEFT JOIN `tabCustomer` AS cu 
            ON si.customer = cu.name
        LEFT JOIN `tabSales Person` AS sp 
            ON cu.excel_sales_person_email = sp.excel_sales_person_email
        WHERE cu.excel_sales_person_email = %(sales_person_email)s
        AND si.docstatus = 1
        AND si.name LIKE '%%SINV%%'
        AND NOT EXISTS (
            SELECT 1 
            FROM `tabSales Invoice` AS si_check
            WHERE si_check.customer = si.customer
            AND si_check.docstatus = 1
            AND si_check.name LIKE '%%SINV%%'
            AND si_check.posting_date >= DATE_SUB(CURDATE(), INTERVAL %(interval_days)s DAY)
        )
        GROUP BY sii.brand, sp.name
        ORDER BY last_invoice_date DESC
    """

    data = frappe.db.sql(
        query, 
        {"sales_person_email": sales_person_email, "interval_days": interval_days}, 
        as_dict=True
    )

    return data


@frappe.whitelist()
def non_billed_customers(sales_person_email="akramul.sales@excelbd.com", interval_days=30):
    
    """
    Fetch customers assigned to a sales person who haven't been billed within the last given days.

    :param sales_person_email: Email of the sales person (linked via excel_sales_person_email in Customer)
    :param interval_days: Number of days to check for recent invoices (default is 30 days)
    :return: List of dicts with customer, customer_name, last_invoice_date, and sales_person
    """
    interval_days = cint(interval_days)
    query = """
        SELECT 
            cu.name AS customer, 
            cu.customer_name AS customer_name, 
            (
                SELECT MAX(si.posting_date) 
                FROM `tabSales Invoice` AS si 
                WHERE si.customer = cu.name 
                AND si.docstatus = 1
                AND si.name LIKE '%%SINV%%'
            ) AS last_invoice_date,
            sp.name AS sales_person
        FROM `tabCustomer` AS cu
        LEFT JOIN `tabSales Person` AS sp 
            ON cu.excel_sales_person_email = sp.excel_sales_person_email
        WHERE cu.excel_sales_person_email = %(sales_person_email)s
        AND NOT EXISTS (
            SELECT 1 
            FROM `tabSales Invoice` AS si
            WHERE si.customer = cu.name
            AND si.docstatus = 1
            AND si.name LIKE '%%SINV%%'
            AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL %(interval_days)s DAY)
        )
    """

    data = frappe.db.sql(
        query, 
        {"sales_person_email": sales_person_email, "interval_days": interval_days}, 
        as_dict=True
    )

    return data
