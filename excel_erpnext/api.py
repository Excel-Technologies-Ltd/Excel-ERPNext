import requests
import base64
from io import BytesIO
from PIL import Image, ImageOps
from weasyprint import HTML

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
