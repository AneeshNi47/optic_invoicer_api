
from reportlab.lib import colors
import textwrap


def draw_header(c, x_position, y_position, invoice):
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(x_position / 2, y_position, invoice.organization.name)
    c.setFont("Helvetica", 12)
    c.drawCentredString(x_position / 2, y_position - 20, "{}, {}, {}".format(
        invoice.organization.address_first_line,
        invoice.organization.country,
        invoice.organization.city
    ))
    c.drawCentredString(x_position / 2, y_position - 40, "{}, {}".format(
        invoice.organization.phone_landline,
        invoice.organization.post_box_number,
    ))
    c.drawCentredString(x_position / 2, y_position - 60, "Services: {}".format(invoice.organization.services))
    return y_position-80

# PDF generator Helper functions
def draw_table_generator(c, num_columns, headers, x_position, y_position, row_height, table_width, data, title=None):
    col_widths = [table_width / num_columns for _ in range(num_columns)]
    c.setLineWidth(1)
    if title is not None:
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x_position + table_width / 2, y_position, title)
        y_position -= row_height

    c.setFont("Helvetica-Bold", 10)
    xlist = [x_position + i * col_widths[0] for i in range(num_columns + 1)]
    ylist = [y_position]
    for i, header in enumerate(headers):
        c.drawCentredString(x_position + col_widths[i] / 2 + i * col_widths[i], y_position - row_height / 2, header)

    y_position -= row_height
    c.setFont("Helvetica", 10)
    for row, item in enumerate(data):
        max_lines = 1
        row_y_position = y_position
        for col, text in enumerate(item):
            text_object = c.beginText(x_position + col * col_widths[col] + 5, row_y_position - row_height / 2)
            text_object.setFont("Helvetica", 10)
            text_object.setFillColor(colors.black)
            width = col_widths[col] - 10
            wrapped_text = textwrap.fill(text, width=20)
            lines = wrapped_text.split('\n')
            num_lines = len(lines)
            if num_lines > max_lines:
                max_lines = num_lines
            text_object.textLines(wrapped_text)
            c.drawText(text_object)
        current_row_height = max_lines * 15
        ylist.append(y_position - current_row_height)
        y_position -= current_row_height

    ylist.insert(1, ylist[0] - row_height)

    xlist = [x_position + i * col_widths[0] for i in range(num_columns + 1)]
    c.grid(xlist, ylist)

    return y_position - 20



def create_custom_grid(c,grid_structure, x_position, y_position, row_height, col_width, data_dict):
    c.setLineWidth(1)
    current_y_position = y_position
    for row in grid_structure:
        current_x_position = x_position
        row_y_position = current_y_position  # Initialize the y-coordinate for the row
        for cell in row:
            if cell is None:
                current_x_position += col_width  # Leave space for the merged cell
                continue
            key, row_span, col_span = cell
            value = data_dict.get(key, '')
            cell_width = col_width * col_span
            text_y_position = row_y_position - row_height/2  # Update text y-coordinate
            if key == "Balance":
                # Draw the key and value
                balance_y_position= text_y_position + row_height-45
                c.setFont("Helvetica-Bold", 20)
                c.drawString(current_x_position + 5, balance_y_position, f"{key}:")
                c.setFont("Helvetica", 20)
                c.drawString(current_x_position + 90, balance_y_position , str(value))
            
            else:
                # Draw the key and value
                c.setFont("Helvetica-Bold", 12)
                c.drawString(current_x_position + 5, text_y_position + row_height / 6, f"{key}:")
                c.setFont("Helvetica", 12)
                c.drawString(current_x_position + 5, text_y_position - (row_height) / 6, str(value))
            
            # Draw the grid cell
            c.rect(current_x_position, row_y_position - row_height, cell_width, row_height, stroke=1, fill=0)
            current_x_position += cell_width
        current_y_position -= row_height
    return current_y_position





def draw_invoice_info(c, height, invoice):
    c.setLineWidth(1)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 130, "Invoice No: ")
    c.drawString(450, height - 130, "{}".format(invoice.date.strftime("%Y-%m-%d")))
    c.drawString(50, height - 170, "Name: ")
    c.drawString(350, height - 170, "Phone: ")

    c.setFont("Helvetica", 12)
    c.drawString(120, height - 130, "{}".format(invoice.invoice_number))
    c.drawString(90, height - 170, " {} {}".format(invoice.customer.first_name, invoice.customer.last_name))
    c.drawString(400, height - 170, "{}".format(invoice.customer.phone))

def draw_tearaway_section(c, invoice, x_position, x_header_position, y_position, row_height, col_width, data_dict):
    c.setLineWidth(1)
    c.setStrokeColorRGB(0, 0, 0)
    line_y_position = y_position + 30
    c.line(x_position, line_y_position, x_position + col_width, line_y_position)

    next_y_position = draw_header(c, x_header_position, y_position, invoice)
    grid_structure = [
        [('Invoice No', 1, 1), ('Delivery Date', 1, 1)],
        [('Total', 1, 1), ('Advance', 1, 1)],
        [('Balance', 1, 2)]
    ]
    y_position = create_custom_grid(c, grid_structure, x_position, next_y_position, row_height, col_width / 2, data_dict)
    return y_position

def draw_footer(c, width, invoice):
    c.setLineWidth(1)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, 10, "© 2023 {}. All rights reserved.".format(invoice.organization.name))




def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
