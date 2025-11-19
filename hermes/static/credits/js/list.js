var tblSale;

function format(d) {
  var html = '<table class="table">';
  html += '<thead class="thead-dark">';
  html += '<tr><th scope="col">Producto</th>';
  html += '<th scope="col">Categoría</th>';
  html += '<th scope="col">Precio</th>';
  html += '<th scope="col">Cantidad</th>';
  html += '<th scope="col">Descuento</th>';
  html += '<th scope="col">Subtotal</th></tr>';
  html += '</thead>';
  html += '<tbody>';
  $.each(d.det, function(key, value) {
    html += '<tr>'
    html += '<td>' + value.prod.name + '</td>'
    html += '<td>' + value.prod.cat.name + '</td>'
    html += '<td>' + value.price + '</td>'
    html += '<td>' + value.cant + '</td>'
    html += '<td>' + value.discount + '</td>'
    html += '<td>' + value.subtotal + '</td>'
    html += '</tr>';
  });
  html += '</tbody>';
  return html;
}

$(function() {

  tblSale = $('#data').DataTable({
    serverSide: true,
    processing: true,
    order: [[3, 'desc']],
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
      {
        "className": 'details-control',
        "orderable": false,
        "data": null,
        "defaultContent": ''
      },
      { "data": "invoice_number" },
      { "data": "cli.full_name" },
      { "data": "date_joined" },
      { "data": "total" },
      { "data": "total_paid" },
      { "data": "id" },
    ],
    columnDefs: [
      {
        targets: [4, 5],
        class: 'text-center',
        orderable: false,
        render: function(data, type, row) {
          return '$' + parseFloat(data).toFixed(2);
        }
      },
      {
        targets: [-1],
        class: 'text-center',
        orderable: false,
        render: function(data, type, row) {
          var buttons = '<a rel="details" class="btn btn-info btn-xs btn-flat"><i class="fas fa-search"></i></a> ';
          buttons += '<a href="/hermes/credits/' + row.id + '/detail/" class="btn btn-secondary btn-xs btn-flat"><i class="fas fa-file-alt"></i></a>';
          return buttons;
        }
      },
    ],
    initComplete: function(settings, json) {

    }
  });

  $('#data tbody')
    .on('click', 'a[rel="details"]', function() {
      var tr = tblSale.cell($(this).closest('td, li')).index();
      var data = tblSale.row(tr.row).data();

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
          { "data": "payment_date" },
          { "data": "amount" },
          { "data": "observation" },
        ],
        columnDefs: [
          {
            targets: [1],
            class: 'text-center',
            render: function(data, type, row) {
              return '$' + parseFloat(data).toFixed(2);
            }
          },
          {
            targets: [2],
            render: function(data, type, row) {
              return data || '-';
            }
          },
        ],
        initComplete: function(settings, json) {

        }
      });

      $('#myModelDet').modal('show');
    })
    .on('click', 'td.details-control', function() {
      var tr = $(this).closest('tr');
      var row = tblSale.row(tr);
      if (row.child.isShown()) {
        row.child.hide();
        tr.removeClass('shown');
      } else {
        row.child(format(row.data())).show();
        tr.addClass('shown');
      }
    });

});
