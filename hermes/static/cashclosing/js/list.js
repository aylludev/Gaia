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
    ],
    initComplete: function(settings, json) {

    }
  });
});
