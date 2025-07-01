var tblSale;

function format(d) {
    let html = '<table class="table">';
    html += '<thead class="thead-dark">';
    html += '<tr><th>Producto</th><th>Categoría</th><th>PVP</th><th>Cantidad</th><th>Descuento</th><th>Subtotal</th></tr>';
    html += '</thead><tbody>';
    $.each(d.det, function (key, value) {
        html += '<tr>';
        html += '<td>' + value.prod.name + '</td>';
        html += '<td>' + value.prod.cat.name + '</td>';
        html += '<td>' + value.price + '</td>';
        html += '<td>' + value.cant + '</td>';
        html += '<td>' + value.discount + '</td>';
        html += '<td>' + value.subtotal + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

$(function () {
    tblSale = $('#data').DataTable({
        processing: true,
        serverSide: true,
        scrollX: true,
        autoWidth: false,
        destroy: true,
        deferRender: true,
        ajax: {
            url: window.location.pathname,
            type: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            data: function (d) {
                d.action = 'searchdata';
            },
            dataSrc: function (json) {
                if (json.error) {
                    alert(json.error);
                    return [];
                }
                return json.data;
            }
        },
        columns: [
            {
                className: 'details-control',
                orderable: false,
                data: null,
                defaultContent: ''
            },
            { data: "invoice_number" },
            { data: "cli.full_name" },  // Asegúrate que esto exista
            { data: "date_joined" },
            { data: "subtotal" },
            { data: "iva" },
            { data: "discountall" },
            { data: "total" },
            { data: "type_payment" },
            { data: "days_to_pay" },
            { data: "id" },
        ],
        columnDefs: [
            {
                targets: [4, 5, 6, 7],
                className: 'text-center',
                render: function (data) {
                    return '$' + parseFloat(data).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
                }
            },
            {
                targets: [-1],
                className: 'text-center',
                render: function (data, type, row) {
                    let buttons = '';
                    buttons += '<a href="/ilitia/sale/delete/' + row.id + '/" class="btn btn-danger btn-xs btn-flat"><i class="fas fa-trash-alt"></i></a> ';
                    buttons += '<a href="/ilitia/sale/update/' + row.id + '/" class="btn btn-warning btn-xs btn-flat"><i class="fas fa-edit"></i></a> ';
                    buttons += '<a rel="details" class="btn btn-success btn-xs btn-flat"><i class="fas fa-search"></i></a> ';
                    buttons += '<a href="/ilitia/sale/invoice/pdf/' + row.id + '/" target="_blank" class="btn btn-info btn-xs btn-flat"><i class="fas fa-file-pdf"></i></a> ';
                    return buttons;
                }
            }
        ]
    });

    // Detalles en modal
    $('#data tbody')
        .on('click', 'a[rel="details"]', function () {
            let tr = tblSale.cell($(this).closest('td, li')).index();
            let data = tblSale.row(tr.row).data();

            $('#tblDet').DataTable({
                responsive: true,
                autoWidth: false,
                destroy: true,
                deferRender: true,
                ajax: {
                    url: window.location.pathname,
                    type: 'POST',
                    data: {
                        'action': 'search_details_prod',
                        'id': data.id
                    },
                    headers: {
                        'X-CSRFToken': csrftoken
                    },
                    dataSrc: ""
                },
                columns: [
                    { data: "prod.name" },
                    { data: "prod.cat.name" },
                    { data: "price" },
                    { data: "cant" },
                    { data: "discount" },
                    { data: "subtotal" }
                ],
                columnDefs: [
                    {
                        targets: [-1, -2],
                        className: 'text-center',
                        render: function (data) {
                            return '$' + parseFloat(data).toFixed(2);
                        }
                    }
                ]
            });

            $('#myModelDet').modal('show');
        })
        .on('click', 'td.details-control', function () {
            let tr = $(this).closest('tr');
            let row = tblSale.row(tr);
            if (row.child.isShown()) {
                row.child.hide();
                tr.removeClass('shown');
            } else {
                row.child(format(row.data())).show();
                tr.addClass('shown');
            }
        });
});
