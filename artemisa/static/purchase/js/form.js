var tblProducts;
var tblSearchProducts;
var vents = {
  items: {
    purchase: '',
    invoice_number: '',
    date: '',
    subtotal: 0.00,
    iva: 0.00,
    discount_total: 0.00,
    total: 0.00,
    type_payment: '',
    days_to_pay: 0,
    down_payment: 0.00,
    observation: '',
    products: []
  },
  get_ids: function() {
    var ids = [];
    $.each(this.items.products, function(key, value) {
      ids.push(value.id);
    });
    return ids;
  },
  calculate_invoice: function() {
    var subtotal = 0.00;
    var iva = ($('input[name="iva"]').val()) || 0;
    var type_payment = ($('select[name="type_payment"]').val()) || 0;
    var discount_total = ($('input[name="discount_total"]').val()) || 0;
    var days_to_pay = ($('input[name="days_to_pay"]').val()) || 0;

    $.each(this.items.products, function(pos, dict) {
      dict.pos = pos;
      var purchase_price = dict.purchase_price || 0;
      var discount = dict.discount || 0;
      var subtotalproduct = dict.cant * parseFloat(purchase_price);
      dict.subtotal = subtotalproduct - ((discount / 100) * subtotalproduct);
      subtotal += dict.subtotal;
    });

    this.items.subtotal = subtotal;
    this.items.iva = parseFloat(iva)* subtotal / 100;
    this.items.total = this.items.subtotal + this.items.iva;
    this.items.discount_total = discount_total;
    this.items.total = this.items.total - this.items.discount_total;
    this.items.type_payment = type_payment;
    this.items.days_to_pay = days_to_pay;

    $('input[name="subtotal"]').val(this.items.subtotal.toLocaleString('es-CO'));
    $('input[name="ivacalc"]').val((this.items.subtotal * (iva / 100)).toLocaleString('es-CO'));
    $('input[name="total"]').val(this.items.total.toLocaleString('es-CO'));
  },

  add: function(item) {
    this.items.products.push(item);
    this.list();
  },

  list: function() {
    this.calculate_invoice();
    tblProducts = $('#tblProducts').DataTable({
      responsive: true,
      autoWidth: false,
      destroy: true,
      data: this.items.products,
      columns: [
        { "data": "id" },
        { "data": "name" },
        { "data": "purchase_price" },
        { "data": "cant" },
        { "data": "discount" },
        { "data": "subtotal" },
      ],
      columnDefs: [
        {
          targets: [0],
          class: 'text-center',
          orderable: false,
          render: function(data, type, row) {
            return '<a rel="remove" class="btn btn-danger btn-xs btn-flat" style="color: white;"><i class="fas fa-trash-alt"></i></a>';
          }
        },
        {
          targets: [-4],
          class: 'text-center',
          orderable: false,
          render: function(data, type, row) {
            return '<input type="text" name="purchase_price" class="form-control form-control-sm input-sm" autocomplete="off" value="' + row.purchase_price + '">';
          }
        },
        {
          targets: [-3],
          class: 'text-center',
          orderable: false,
          render: function(data, type, row) {
            return '<input type="text" name="cant" class="form-control form-control-sm input-sm" autocomplete="off" value="' + row.cant + '">';
          }
        },
        {
          targets: [-2],
          class: 'text-center',
          orderable: false,
          render: function(data, type, row) {
            return '<input type="text" name="discount" class="form-control form-control-sm input-sm" autocomplete="off" value="' + row.discount + '">';
          }
        },
        {
          targets: [-1],
          class: 'text-center',
          orderable: false,
          render: function(data, type, row) {
            return '$' + parseFloat(data).toFixed(2);
          }
        },
      ],
      rowCallback(row, data, displayNum, displayIndex, dataIndex) {

        $(row).find('input[name="purchase_price"]').TouchSpin({
          min:1,
          max: 10000000,
          step: 1,
          prefix: '$',
        });

        $(row).find('input[name="cant"]').TouchSpin({
          min: 1,
          max: data,
          step: 1
        });

        $(row).find('input[name="discount"]').TouchSpin({
          min: 0,
          max: 10,
          step: 1,
          postfix: '%'
        });
      },
      initComplete: function(settings, json) {

      }
    });
  },
};

function formatRepo(repo) {
  if (repo.loading) {
    return repo.text;
  }

  if (!Number.isInteger(repo.id)) {
    return repo.text;
  }

  var option = $(
    '<div class="wrapper container">' +
    '<div class="col-lg-12 text-left shadow-sm">' +
    '<p style="margin-bottom: 0;">' +
    '<b>Nombre:</b> ' + repo.name + '<br>' +
    '<b>Stock:</b> ' + repo.stock + '<br>' +
    '<b>Precio de compra:</b> <span class="badge badge-warning">$' + repo.purchase_price + '</span>' +
    '</p>' +
    '</div>' +
    '</div>' +
    '</div>');

  return option;
}

$(function() {

  $('.select2').select2({
    theme: "bootstrap4",
    language: 'es'
  });

  $('#date').datetimepicker({
    format: 'YYYY-MM-DD',
    date: moment().format("YYYY-MM-DD"),
    locale: 'es',
    //minDate: moment().format("YYYY-MM-DD")
  });


  $("input[name='discount_total']").on('input', function() {
    vents.calculate_invoice();
  })

  $("input[name='iva']").TouchSpin({
    min: 0,
    max: 19,
    step: 1,
    boostat: 5,
    decimals: 2,
    maxboostedstep: 10,
    postfix: '%',
    initval: $("#id_iva").val()
  }).on('change', function() {
    vents.calculate_invoice();
  })

  $('select[name="type_payment"]').on('change', function() {
    console.log($(this).val());
    if ($(this).val() === "CASH") {
      $("#down_payment").fadeOut();  // Muestra el campo con animación
    } else {
      $("#down_payment").fadeIn();// Oculta el campo con animación
    }
    vents.calculate_invoice()
  });

  $("input[name='down_payment']").on('change', function() {
    vents.calculate_invoice();
  })
  // search clients

  $('select[name="provider"]').select2({
    theme: "bootstrap4",
    language: 'es',
    allowClear: true,
    ajax: {
      delay: 250,
      type: 'POST',
      url: window.location.pathname,
      headers: {
        'X-CSRFToken': csrftoken,
      },
      data: function(params) {
        return {
          term: params.term,
          action: 'search_clients'
        };
      },
      processResults: function(data) {
        return {
          results: data
        };
      },
    },
    placeholder: 'Ingrese una descripción',
    minimumInputLength: 1,
  });

  $('.btnAddClient').on('click', function() {
    $('#myModalClient').modal('show');
  });

  $('#myModalClient').on('hidden.bs.modal', function(e) {
    $('#frmClient').trigger('reset');
  })

  $('#frmClient').on('submit', function(e) {
    e.preventDefault();
    var parameters = new FormData(this);
    parameters.append('action', 'create_client');
    submit_with_ajax(window.location.pathname, 'Notificación',
      '¿Estas seguro de crear al siguiente cliente?', parameters, function(response) {
        //console.log(response);
        var newOption = new Option(response.full_name, response.id, false, true);
        $('select[name="provider"]').append(newOption).trigger('change');
        $('#myModalClient').modal('hide');
      });
  });

  // search products
  $('.btnRemoveAll').on('click', function() {
    if (vents.items.products.length === 0) return false;
    alert_action('Notificación', '¿Estas seguro de eliminar todos los items de tu detalle?', function() {
      vents.items.products = [];
      vents.list();
    }, function() {

    });
  });

  // event cant
  $('#tblProducts tbody')
    .on('click', 'a[rel="remove"]', function() {
      var tr = tblProducts.cell($(this).closest('td, li')).index();
      alert_action('Notificación', '¿Estas seguro de eliminar el producto de tu detalle?',
        function() {
          vents.items.products.splice(tr.row, 1);
          vents.list();
        }, function() {

        });
    })
    .on('change', 'input[name="purchase_price"]', function() {
      var purchase_price = parseFloat($(this).val());
      var tr = tblProducts.cell($(this).closest('td, li')).index();
      vents.items.products[tr.row].purchase_price = purchase_price;
      vents.calculate_invoice();
      $('td:eq(5)', tblProducts.row(tr.row).node()).html('$' + vents.items.products[tr.row].subtotal.toFixed(2));
    })
    .on('change', 'input[name="cant"]', function() {
      console.clear();
      var cant = parseInt($(this).val());
      var tr = tblProducts.cell($(this).closest('td, li')).index();
      vents.items.products[tr.row].cant = cant;
      vents.calculate_invoice();
      $('td:eq(5)', tblProducts.row(tr.row).node()).html('$' + vents.items.products[tr.row].subtotal.toFixed(2));
    })
    .on('change', 'input[name="discount"]', function() {
      console.clear();
      var discount = parseInt($(this).val());
      var tr = tblProducts.cell($(this).closest('td, li')).index();
      vents.items.products[tr.row].discount = discount;
      vents.calculate_invoice();
      $('td:eq(5)', tblProducts.row(tr.row).node()).html('$' + vents.items.products[tr.row].subtotal.toFixed(2));
    });

  $('.btnClearSearch').on('click', function() {
    $('input[name="search"]').val('').focus();
  });

  $('.btnSearchProducts').on('click', function() {
    tblSearchProducts = $('#tblSearchProducts').DataTable({
      responsive: true,
      autoWidth: false,
      destroy: true,
      deferRender: true,
      ajax: {
        url: window.location.pathname,
        type: 'POST',
        data: {
          'action': 'search_products',
          'ids': JSON.stringify(vents.get_ids()),
          'term': $('select[name="search"]').val()
        },
        dataSrc: "",
        headers: {
          'X-CSRFToken': csrftoken,
        },
      },
      columns: [
        { "data": "name" },
        { "data": "stock" },
        { "data": "purchase_price" },
        { "data": "id" },
      ],
      columnDefs: [
        {
          targets: [-3],
          class: 'text-center',
          render: function(data, type, row) {
            return '<span class="badge badge-secondary">' + data + '</span>';
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
            var buttons = '<a rel="add" class="btn btn-success btn-xs btn-flat"><i class="fas fa-plus"></i></a> ';
            return buttons;
          }
        },
      ],
      initComplete: function(settings, json) {

      }
    });
    $('#myModalSearchProducts').modal('show');
  });

  $('#tblSearchProducts tbody')
    .on('click', 'a[rel="add"]', function() {
      var tr = tblSearchProducts.cell($(this).closest('td, li')).index();
      var product = tblSearchProducts.row(tr.row).data();
      product.cant = 1;
      product.subtotal = 0.00;
      vents.add(product);
      tblSearchProducts.row($(this).parents('tr')).remove().draw();
    });

  // event submit
  $('#frmSale').on('submit', function(e) {
    e.preventDefault();

    if (vents.items.products.length === 0) {
      message_error('Debe al menos tener un item en su detalle de venta');
      return false;
    }

    var down_payment = (($('input[name="down_payment"]').val()) || 0).replace(/\./g, '').replace(/,/g, '.');  // Quita puntos y cambia la coma decimal
    vents.items.date = $('input[name="date"]').val();
    vents.items.provider = $('select[name="provider"]').val();
    vents.items.down_payment = down_payment;
    vents.items.observation = $('input[name="observation"]').val();
    vents.items.invoice_number = $('input[name="invoice_number"]').val();

    var parameters = new FormData();
    parameters.append('action', $('input[name="action"]').val());
    parameters.append('vents', JSON.stringify(vents.items));
    submit_with_ajax(window.location.pathname, 'Notificación',
      '¿Estas seguro de realizar la siguiente acción?', parameters, function(response) {
        alert_action('Notificación', '¿Desea revisar la boleta de venta?', function() {
          window.open('/artemisa/purchase/detail/' + response.id + '/', '_blank');
          location.href = '/artemisa/purchase/list/';
        }, function() {
          location.href = '/artemisa/purchase/list/';
        });
      });
  });

  $('select[name="search"]').select2({
    theme: "bootstrap4",
    language: 'es',
    allowClear: true,
    ajax: {
      delay: 250,
      type: 'POST',
      headers: { 'X-CSRFToken': csrftoken, },
      url: window.location.pathname,
      data: function(params) {
        var queryParameters = {
          term: params.term,
          action: 'search_autocomplete',
          ids: JSON.stringify(vents.get_ids())
        }
        return queryParameters;
      },
      processResults: function(data) {
        return {
          results: data
        };
      },
    },
    placeholder: 'Ingrese una descripción',
    minimumInputLength: 1,
    templateResult: formatRepo,
  }).on('select2:select', function(e) {
    var data = e.params.data;
    if (!Number.isInteger(data.id)) {
      return false;
    }
    data.cant = 1;
    data.discount = 0;
    data.subtotal = 0.00;
    vents.add(data);
    $(this).val('').trigger('change.select2');
  });

  // Esto se puso aqui para que funcione bien el editar y calcule bien los valores del iva. // sino tomaría el valor del iva de la base debe
  // coger el que pusimos al inicializarlo.
  vents.list();
});

