function generate_report() {
    var product_id = $('#product_id').val();

    var parameters = {
        'action': 'search_product_qty',
        'start_date': input_daterange.data('daterangepicker').startDate.format('YYYY-MM-DD'),
        'end_date': input_daterange.data('daterangepicker').endDate.format('YYYY-MM-DD'),
        'product_id': product_id
    };

    $('#data').DataTable({
        responsive: true,
        autoWidth: false,
        destroy: true,
        deferRender: true,
        ajax: {
            url: window.location.pathname,
            type: 'POST',
            data: parameters,
            dataSrc: function (json) {
                // Si el backend devuelve un solo objeto en lugar de una lista
                if (json.error) {
                    alert(json.error);
                    return [];
                }
                return [[
                    json.product_id,
                    json.total_quantity,
                    json.total_subtotal
                ]];
            }
        },
        columns: [
            { title: 'Producto ID' },
            { title: 'Cantidad Vendida' },
            { title: 'Subtotal Vendido' }
        ],
        columnDefs: [
            {
                targets: [-1],
                class: 'text-center',
                orderable: false,
                render: function (data, type, row) {
                    return '$' + parseFloat(data).toFixed(2);
                }
            },
        ],
        paging: false,
        ordering: false,
        searching: false
    });
}

$(function () {
    input_daterange = $('input[name="date_range"]');

    $('#product_id').change(function () {
        generate_report();
    });

    input_daterange.daterangepicker({
        language: 'auto',
        startDate: new Date(),
        locale: {
            format: 'YYYY-MM-DD',
            applyLabel: '<i class="fas fa-chart-pie"></i> Aplicar',
            cancelLabel: '<i class="fas fa-times"></i> Cancelar',
        },
    })
    .on('apply.daterangepicker', function () {
        generate_report();
    }).on('cancel.daterangepicker', function () {
        generate_report();
    });
});
