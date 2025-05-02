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
      headers: {
        'X-CSRFToken': csrftoken
      },
      dataSrc: ""
    },
    columns: [
      { "data": "id" },
      { "data": "created_by.username" },
      { "data": "created_by.full_name" },
      { "data": "last_login" },
      { "data": "date" },
      { "data": "total_cash" },
      { "data": "observations" },
    ],
    columnDefs: [
      {
        targets: [-1],
        class: 'text-center',
        orderable: false,
        render: function(data, type, row) {
          var buttons = '<a href="/artemisa/provider/update/' + row.id + '/" class="btn btn-warning btn-xs btn-flat"><i class="fas fa-edit"></i></a> ';
          buttons += '<a href="/artemisa/provider/delete/' + row.id + '/" type="button" class="btn btn-danger btn-xs btn-flat"><i class="fas fa-trash-alt"></i></a>';
          return buttons;
        }
      },
    ],
    initComplete: function(settings, json) {

    }
  });
});
