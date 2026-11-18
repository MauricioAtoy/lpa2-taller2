from flask import Flask, render_template, request, send_file, abort
import requests
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from io import BytesIO
import os

app = Flask(__name__)
BACKEND_URL = os.getenv('BACKEND_URL', 'http://backend:8000')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar-pdf', methods=['POST'])
def generar_pdf():
    try:
        id_factura = request.form['id_factura']
        response = requests.get(f'{BACKEND_URL}/facturas/v1/{id_factura}')
        
        if response.status_code != 200:
            abort(404, description="Factura no encontrada")
            
        factura = response.json()
        
        # TODO: Crear buffer y doc para la creación del PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=20 * mm, rightMargin=20 * mm,
            topMargin=20 * mm, bottomMargin=20 * mm,
            title=f"Factura {factura['numero_factura']}",
        )
        elements = []        

        # TODO: Adicionar el Título, ID
        elements.append(Paragraph("FACTURA", styles['Title']))
        elements.append(Paragraph(f"<b>No.:</b> {factura['numero_factura']}", styles['Normal']))
        elements.append(Paragraph(f"<b>Fecha de emisión:</b> {factura['fecha_emision']}", styles['Normal']))
        elements.append(Spacer(1, 8 * mm))
        
        # TODO: Agregar Información de la Empresa
        emp = factura['empresa']
        elements.append(Paragraph("Empresa", styles['Heading2']))
        elements.append(Paragraph(emp['nombre'], styles['Normal']))
        elements.append(Paragraph(emp['direccion'].replace("\n", "<br/>"), styles['Normal']))
        elements.append(Paragraph(f"Tel: {emp['telefono']}", styles['Normal']))
        elements.append(Paragraph(f"Email: {emp['email']}", styles['Normal']))
        elements.append(Spacer(1, 6 * mm))

        # TODO: Agregar Información del Cliente
        cli = factura['cliente']
        elements.append(Paragraph("Cliente", styles['Heading2']))
        elements.append(Paragraph(cli['nombre'], styles['Normal']))
        elements.append(Paragraph(cli['direccion'].replace("\n", "<br/>"), styles['Normal']))
        elements.append(Paragraph(f"Tel: {cli['telefono']}", styles['Normal']))
        elements.append(Spacer(1, 8 * mm))

        # TODO: Adicionar el Detalle de la Factura: cantidad, descripción, precio unitario y total
        data = [["Cant.", "Descripción", "Precio unit.", "Total"]]
        for item in factura['detalle']:
            data.append([
                str(item['cantidad']),
                Paragraph(item['descripcion'], styles['Normal']),
                moneda(item['precio_unitario']),
                moneda(item['total']),
            ])

        tabla = Table(data, colWidths=[18 * mm, 80 * mm, 36 * mm, 36 * mm], repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(tabla)
        elements.append(Spacer(1, 6 * mm))

        # TODO: Adicionar Subtotal, impuesto y Total
        totales = Table([
            ["Subtotal:", moneda(factura['subtotal'])],
            ["Impuesto (IVA 21%):", moneda(factura['impuesto'])],
            ["TOTAL:", moneda(factura['total'])],
        ], colWidths=[130 * mm, 40 * mm])
        totales.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ]))
        elements.append(totales)

        # Generar el doc y limpiar el buffer
        doc.build(elements)
        buffer.seek(0)
        
        # TODO: Retornar a la página el PDF para visualizar y descargar
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f"factura_{factura['numero_factura']}.pdf",
        )
        
    except requests.exceptions.ConnectionError:
        abort(503, description="Error de conexión con el servidor")
    except Exception as e:
        abort(500, description=str(e))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)

