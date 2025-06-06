$(function() {
    $('#data').DataTable({
      responsive: true,
      autoWidth: false,
      destroy: true,
      deferRender: true,
      ajax: {
        url: window.location.pathname,
        type: 'POST',
        data: {
          'action': 'searchdata'
        },
        dataSrc: "",
        headers: {
          'X-CSRFToken': csrftoken
        }
      },
      columns: [
        { "data": "id" },
        { "data": "code" },
        { "data": "name" },
        { "data": "cat.name" },
        { "data": "purchase_price" },
        { "data": "stock" },
        { "data": "sale_price" },
        { "data": "id" },
      ],
      columnDefs: [
        {
          targets: [-3],
          class: 'text-center',
          orderable: false,
          render: function(data, type, row) {
            if (row.stock > 0) {
              return '<span class="badge badge-success">' + data + '</span>'
            }
            return '<span class="badge badge-danger">' + data + '</span>'
          }
        },
        {
          targets: [-2],
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
            var buttons = '<a href="/artemisa/product/update/' + row.id + '/" class="btn btn-warning btn-xs btn-flat"><i class="fas fa-edit"></i></a> ';
            buttons += '<a href="/artemisa/product/delete/' + row.id + '/" type="button" class="btn btn-danger btn-xs btn-flat"><i class="fas fa-trash-alt"></i></a>';
            return buttons;
          }
        },
      ],
      initComplete: function(settings, json) {
  
      }
    });
  });
  