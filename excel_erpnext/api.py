import frappe
from frappe.api import get_request_form_data
from frappe.api import get_request_form_data
from frappe import _
from frappe.desk.reportview import get_count as get_filtered_count
from frappe.desk.reportview import get_form_params

import frappe
from io import BytesIO
from weasyprint import HTML
from PIL import Image,ImageOps  # Pillow is already installed
from frappe.utils.pdf import get_pdf

import frappe
from frappe import _
from frappe.www.printview import validate_print_permission
from frappe.translate import print_language
from frappe.utils.pdf import get_pdf

@frappe.whitelist(methods=["POST"])
def insert_json():
    data = get_request_form_data()

    for x in data.get("items"):
        UOM_value = frappe.db.get_value(
            "UOM", x.get("uom"), fieldname="uom_name")

    UOM = frappe.get_doc({
        "doctype": "UOM",
        "uom_name": x.get("uom"),

    })
    if not UOM_value:
        UOM.insert()

    for x in data.get("items"):
        itemsgroup_value = frappe.db.get_value(
            "Item Group", x.get("item_group"), fieldname="item_group_name")

    itemsgroup = frappe.get_doc({
        "doctype": "Item Group",
        "item_group_name": x.get("item_group")

    })

    if not itemsgroup_value:
        itemsgroup.insert()

    territory_value = frappe.db.get_value(
        "Territory", data.get("territory"), fieldname="territory_name")

    territory = frappe.get_doc({
        "doctype": "Territory",
        "territory_name": data.get("territory"),


    })

    if not territory_value:
        territory.insert()

    list_words = data.get("company").split()
    final_acro = ""
    for i in list_words:
        final_acro += i[0].upper()

    for i in range(len(final_acro)):

        company_value = frappe.db.get_value(
            "Company", data.get("company"), fieldname="company_name")

    company = frappe.get_doc({
        "doctype": "Company",
        "company_name": data.get("company"),
        "abbr": final_acro,
        "default_currency": data.get("currency"),
        "country": "India"

    })

    if not company_value:
        company.insert()

    price_list_value = frappe.db.get_value(
        "Price List", data.get("selling_price_list"), fieldname="*")

    price_list = frappe.get_doc({
        "doctype": "Price List",
        "price_list_name": data.get("selling_price_list"),
        "currency": data.get("currency"),
        "buying": 1,
        "selling": 1,
        "price_not_uom_dependent": 1,
        "enabled": 1,

    })

    if not price_list_value:
        price_list.insert()

    customergroup_value = frappe.db.get_value("Customer Group", data.get(
        "customer_group"), fieldname="customer_group_name")

    customergroup = frappe.get_doc({
        "doctype": "Customer Group",
        "customer_group_name": data.get("customer_group")
    })
    if not customergroup_value:
        customergroup.insert()

    currency_value = frappe.db.get_value(
        "Currency", data.get("currency"), fieldname="currency_name")
    currency = frappe.get_doc({
        "doctype": "Currency",
        "currency_name": data.get("currency"),
        "enabled": 1
    })
    if not currency_value:
        currency.insert()

    for z in data.get("items"):
        
     if not frappe.db.exists("Item", z.get("item_code")):
        items = frappe.new_doc("Item")
        items.item_code = z.get("item_code")
        items.item_name = z.get("item_name")
        items.description = z.get("description")
        items.is_nil_exempt = z.get("is_nil_exempt")
        items.is_non_gst = z.get("is_non_gst")
        items.item_group = z.get("item_group")
        items.image = z.get("image")
        items.qty = z.get("qty")
        items.conversion_factor = z.get("image")
        items.stock_uom = z.get("stock_uom")
        items.has_excel_serials = z.get("has_excel_serials")   
        items.save()             
  

        
    doc = frappe.new_doc("Excel Delivery Note")
    doc.naming_series = data.get("naming_series")
    doc.customer = data.get("customer")
    doc.customer_name = data.get("customer_name")
    doc.company = data.get("company")
    doc.posting_date = data.get("posting_date")
    doc.posting_time = data.get("posting_time")
    doc.is_return = data.get("is_return")
    doc.contact_email = data.get("contact_email")
    doc.currency = data.get("currency")
    doc.conversion_rate = data.get("conversion_rate")
    doc.selling_price_list = data.get("selling_price_list")
    doc.price_list_currency = data.get("price_list_currency")
    doc.plc_conversion_rate = data.get("plc_conversion_rate")
    doc.total_qty = data.get("total_qty")
    doc.base_total = data.get("base_total")
    doc.base_net_total = data.get("base_net_total")
    doc.total = data.get("total")
    doc.net_total = data.get("net_total")
    doc.base_grand_total = data.get("base_grand_total")
    doc.customer_group = data.get("customer_group")
    doc.territory = data.get("territory")
    doc.pricing_rules = data.get("pricing_rules")
    doc.packed_items = data.get("packed_items")
    doc.taxes = data.get("taxes")
    doc.sales_team = data.get("sales_team")
    doc.isSynced = data.get("isSynced")   

    doc.status = data.get("status")
    for y in data.get("items"):
        doc.append("items", {"item_code": y.get("item_code"), "item_name": y.get("item_name"), "description": y.get("description"), "item_group": y.get("item_group"), "image": y.get("image") ,"qty": y.get(
            "qty"), "stock_qty": y.get("stock_qty"), "price_list_rate": y.get("price_list_rate"), "base_price_list_rate": y.get("base_price_list_rate"), "rate": y.get("rate"), "amount": y.get("amount"), "stock_uom": y.get("stock_uom"), "uom": y.get("uom"), "conversion_factor": y.get("conversion_factor")})
       
    doc.insert()

@frappe.whitelist(allow_guest=True)
def get_list():
    args = get_form_params()
    docs = frappe.get_list(**args)

    frappe.local.response = frappe._dict(
    {
        "docs": docs,
        "length": get_filtered_count(),
    }    
)
    


@frappe.whitelist(allow_guest=True)
def download_pdf_as_image(doctype, name, format=None, doc=None, no_letterhead=0, language=None, letterhead=None, image_format="PNG"):
    """
    Converts a document to an image by generating HTML and rendering it as an image using WeasyPrint.
    Optimizes the image size and crops extra white space.
    
    :param doctype: The DocType of the document to be converted to an image.
    :param name: The name of the document.
    :param format: The Print Format to use (optional).
    :param no_letterhead: Whether to exclude the letterhead (default 0).
    :param language: Language for the output (optional).
    :param letterhead: Letterhead to use (optional).
    :param image_format: The format of the output image (PNG/JPEG), default is PNG.
    
    :returns: Image file in the requested format (PNG by default).
    """

    # Generate the HTML content for the document
    doc = doc or frappe.get_doc(doctype, name)

    with print_language(language):
        html_content = frappe.get_print(
            doctype, name, format, doc=doc, as_pdf=False, letterhead=letterhead, no_letterhead=no_letterhead
        )

    # Set a larger width to accommodate content, e.g., 1280px
    output_width = 1280  # You can increase this if needed
    scale_factor = 2  # Scale factor for better resolution

    # Render the HTML to PNG using WeasyPrint with a fixed width
    png_bytes = BytesIO()
    document = HTML(string=html_content)

    # Render the document and calculate dimensions
    rendered_pages = document.render()

    # Dynamically calculate width and height based on content, convert to integers
    output_height = int(rendered_pages.pages[0].height * (output_width / rendered_pages.pages[0].width))
    output_width = int(output_width)

    # Write the PNG image to the BytesIO object with fixed width
    document.write_png(png_bytes, resolution=96)

    # Open the image with Pillow and add a white background if needed
    png_bytes.seek(0)
    image = Image.open(png_bytes)
    if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
        background = Image.new('RGB', image.size, (255, 255, 255))  # Create white background
        background.paste(image, mask=image.split()[3])  # Paste the image on top of the white background
        image = background 
    # Crop white space if needed
    image = ImageOps.crop(image, border=20)  # You can adjust the crop margin to remove excess white space

    # Save the final image with adjusted size
    output_image_bytes = BytesIO()
    image.save(output_image_bytes, format=image_format.upper())

    # Set the correct content type and return the image as binary
    frappe.local.response.filename = f"{name}.{image_format.lower()}"
    frappe.local.response.filecontent = output_image_bytes.getvalue()
    frappe.local.response.type = "download"
    frappe.local.response.headers = {
        "Content-Type": f"image/{image_format.lower()}",
        "Content-Disposition": f'inline; filename="{name}.{image_format.lower()}"'
    }

    return output_image_bytes.getvalue()  # Return the binary image data



@frappe.whitelist(allow_guest=True)
def hello():
    return "Hello"