# -*- coding: utf-8 -*-
from classes import *
from xmlgenerator import *

xmlgen = Blueprint('xmlgen', __name__, url_prefix='/xmlgen')

@xmlgen.route('/', methods=['GET', 'POST'])
def gerar_xml():

    sel_op = ''
    sel = ''
    result = ''
    operacao = ''
    data = []
    data2 = []

    op_type = request.form.get("op_type")
    txt_order = request.form.get("txt_order")

    df = pd.read_csv('operacoes.csv', sep=';')
    df = df.sort_values(by=['op_type'])

    for x, y in df[['op_type', 'operacao']].values:

        if op_type == x:
            sel = 'selected'
            operacao = y
        else:

            sel = ''
            sel_op += '<option value="' + x + '" ' + sel + '>' + x + '</option>'


    if request.method == "POST":
        try:

            conn_pweb = cx_Oracle.connect()  # DEVE-SE PREENCHER CONEXÃO
            conn_sieb8 = cx_Oracle.connect() # DEVE-SE PREENCHER CONEXÃO

            querys8 = ("""SELECT sap.x_cnl, asset_integ_id, sap.x_cnl_code, sap.x_street_type, sap.ADDR, sap.x_number,
                   sap.x_neighborhood, sap.city, sap.state, x_street_code, soi.X_ACCESS_TECHNOLOGY, so.X_GVT_GERA_BA ,x_order_type,
                      substr(SERVICE_NUM, 0,2)
                    from siebel.s_order so,
                    siebel.s_order_item soi,
                    siebel.s_prod_int spi,
                    siebel.s_org_ext soe,
                    siebel.s_addr_per sap
                    where so.ROW_ID = soi.ORDER_ID
                    and soi.PROD_ID = spi.ROW_ID
                    and so.bill_accnt_id = soe.row_id
                    and soi.x_serv_addr_id = sap.ROW_ID
                    and sap.X_ACCOUNT_ID = soe.ROW_ID
                    and soi.PROD_ID in ('1-7HWB','1-5WPB','1-C1SQ','1-F7ISQ')
                    and so.INTEGRATION_ID in ('{}')
                    AND spi.name = 'Linha Telefônica';""".format(txt_order))

            df_s8 = pd.read_sql(querys8, conn_sieb8)

            # Passa os dados do banco para um array

            for row in df_s8:
                data.append(row)

            tecnologia = data[10]
            geraBA = data[11]
            ot = data[12]

            # Verifica qual consulta deve ser executada.

            if tecnologia == "METALICO":
                querypwb = ("""
                    SELECT substr(substr(xml_translate,instr(xml_translate,'</can:serviceId>') -1 ),0,1),
                    substr(substr(xml_translate,instr(xml_translate,'</can:serviceId>') -10 ),0,8),
                    substr(substr(xml_translate,instr(xml_translate,'</can:telephonicArea>') -2 ),0,2),
                    substr(substr(xml_translate,instr(xml_translate,'</can:provisioningCode>') -6 ),0,6),
                    substr(substr(xml_translate,instr(xml_translate,'</can:centralOffice>') -2 ),0,2),
                    substr(substr(xml_translate,instr(xml_translate,'</can:customerOrderType>') -6 ),0,6),
                    RESERVA , substr(substr(xml_translate,instr(xml_translate,'</can:mediaType>') -4 ),0,4),
                    substr(substr(xml_translate,instr(xml_translate,'</can:serviceId>') -5 ),0,5)
                    FROM omanagement_owner.reserves
                    WHERE
                    reserva IS NOT NULL
                    AND   pon IN ('{}')
                    AND DESIGNADOR LIKE '%013';
                    """.format(txt_order))

            else:
                querypwb = ("""
                    SELECT
                    substr(substr(xml_translate, instr(xml_translate, '</can:serviceId>') - 1 ), 0, 1),
                    substr(substr(xml_translate, instr(xml_translate, '</can:serviceId>') - 10), 0, 8),
                    substr(substr(xml_translate, instr(xml_translate, '</can:telephonicArea>') - 2), 0, 2),
                    substr(substr(xml_translate, instr(xml_translate, '</can:provisioningCode>') - 6), 0, 6),
                    substr(substr(xml_translate, instr(xml_translate, '</can:centralOffice>') - 2), 0, 2),
                    substr(substr(xml_translate, instr(xml_translate, '</can:customerOrderType>') - 6), 0, 6),
                    RESERVA, substr(substr(xml_translate, instr(xml_translate, '</can:mediaType>') - 5), 0, 5),
                    substr(substr(xml_translate, instr(xml_translate, '</can:serviceId>') - 5), 0, 5)
                    FROM omanagement_owner.reserves
                    WHERE reserva IS NOT NULL
                    AND pon IN('{}')
                    AND DESIGNADOR LIKE '%013';
                    """.format(txt_order))

            df_pwb = pd.read_sql(querypwb, conn_pweb)

            for row in df_pwb:
                data2.append(row)

            data2.append(txt_order)

            # Verifica se é uma reserva e qual a tecnologia

            if tecnologia == "METALICO":

                productTopologyType = "ADSL"
                productTopologyCategory = ""

                if operacao == "res":

                    if geraBA == "SIM" and ot == "Mudança de Oferta" or ot == "Edição de Oferta":
                        operationType = "ALTPRO"

                    elif geraBA == "NAO" and ot == "Mudança de Oferta" or ot == "Edição de Oferta":
                        operationType = "ALTPED"

                    elif ot == "Mudança de Endereço":
                        operationType = "MUDEND"

                    elif operacao == "res" and ot == "Venda de Oferta":
                        operationType = "INSADI"

                else:

                    operationType = data2[5]
                    productTopologyType = data2[7]
                    productTopologyCategory = data2[8]

            else:

                productTopologyType = "FIBRA"
                productTopologyCategory = "VOIP2"
                data[13] = ""

                if operacao == "res":

                    if geraBA == "SIM" and ot == "Mudança de Oferta" or ot == "Edição de Oferta":
                        operationType = "ALTPRO"
                    elif geraBA == "NAO" and ot == "Mudança de Oferta" or ot == "Edição de Oferta":
                        operationType = "ALTPED"
                    elif ot == "Mudança de Endereço":
                        operationType = "MUDEND"
                    elif operacao == "res" and ot == "Venda de Oferta":
                        operationType = "INSADI"

                else:

                    operationType = data2[5]
                    productTopologyType = data2[7]
                    productTopologyCategory = data2[8]

            # Preenchimento dos parâmetros do xml a ser gerado

            xmlSig = XML(data[0], data[1], data[2], data[3], data[4],
                      data[5], data[6], data[7], data[8], data[9],
                      data[10], data[11], data[12], data[13], data2[0],
                      data2[1], data2[2], data2[3], data2[4], data2[6],
                      operationType, productTopologyType, productTopologyCategory,
                      "N", txt_order)

            # Verifica o tipo de operação selecionada

            if operacao == "res":
                result = xmlSig.sigReserve()

            elif operacao == "can":
                result = xmlSig.sigCancel()

            elif operacao == "con":
                result = xmlSig.sigConfirm()

            elif operacao == "ocu":
                result = xmlSig.sigActivate()

            elif operacao == "OPERACAO":
                flash("Operacao inválida!")

            return render_template("xmlgen.html", sel_op=sel_op, result=result)

        except Exception as e:
            flash(e)
            return render_template("xmlgen.html", sel_op=sel_op)

    return render_template("xmlgen.html", sel_op=sel_op)



