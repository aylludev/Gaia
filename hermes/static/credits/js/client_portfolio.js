var tblClients;

$(function() {

  tblClients = $('#data').DataTable({
    serverSide: true,
    processing: true,
    order: [[0, 'asc']],
    scrollX: true,
    autoWidth: false,
    destroy: true,
    deferRender: true,
    ajax: {
      url: window.location.pathname,
      type: 'POST',
      data: function(d) {
        d.action = 'searchdata';
        return d;
      },
      headers: {
        'X-CSRFToken': csrftoken
      },
      error: function(xhr, error, code) {
        console.log('Error AJAX:', xhr, error, code);
        console.log('Response:', xhr.responseText);
      }
    },
    columns: [
      { "data": "full_name" },
      { "data": "dni" },
      { "data": "cellphone" },
      { "data": "total_sales" },
      { "data": "total_debt" },
      { "data": "id" },
    ],
    columnDefs: [
      {
        targets: [3],
        class: 'text-center',
        orderable: false,
        render: function(data, type, row) {
          return '<span class="badge badge-warning">' + data + '</span>';
        }
      },
      {
        targets: [4],
        class: 'text-center',
        orderable: false,
        render: function(data, type, row) {
          return '<strong class="text-danger">$' + parseFloat(data).toFixed(2) + '</strong>';
        }
      },
      {
        targets: [-1],
        class: 'text-center',
        orderable: false,
        render: function(data, type, row) {
          var buttons = '<a rel="details" class="btn btn-info btn-xs btn-flat" title="Ver facturas pendientes"><i class="fas fa-search"></i></a> ';
          return buttons;
        }
      },
    ],
    initComplete: function(settings, json) {

    }
  });

  $('#data tbody')
    .on('click', 'a[rel="details"]', function() {
      var tr = tblClients.cell($(this).closest('td, li')).index();
      var data = tblClients.row(tr.row).data();

      $('#tblDet').DataTable({
        responsive: true,
        autoWidth: false,
        destroy: true,
        deferRender: true,
        ajax: {
          url: window.location.pathname,
          type: 'POST',
          data: {
            'action': 'get_client_sales',
            'id': data.id
          },
          headers: {
            'X-CSRFToken': csrftoken
          },
          dataSrc: ""
        },
        columns: [
          { "data": "invoice_number" },
          { "data": "date_joined" },
          { "data": "total" },
          { "data": "pending" },
          { "data": "id" },
        ],
        columnDefs: [
          {
            targets: [2],
            class: 'text-center',
            render: function(data, type, row) {
              return '$' + parseFloat(data).toFixed(2);
            }
          },
          {
            targets: [3],
            class: 'text-center',
            render: function(data, type, row) {
              return '<strong class="text-danger">$' + parseFloat(data).toFixed(2) + '</strong>';
            }
          },
          {
            targets: [-1],
            class: 'text-center',
            render: function(data, type, row) {
              return '<a href="/hermes/sale/' + row.id + '/salepayment/create/" class="btn btn-success btn-xs" title="Registrar pago"><i class="fas fa-dollar-sign"></i></a> ' +
                     '<a href="/hermes/sale/' + row.id + '/salepayment/detail/" class="btn btn-secondary btn-xs" title="Ver detalle"><i class="fas fa-file-alt"></i></a>';
            }
          },
        ],
        initComplete: function(settings, json) {

        }
      });

      $('#myModelDet').modal('show');
    });

});
