// ---------- 1) Menu aktif ----------
function highlightActiveNav() {
  const path = window.location.pathname;
  const links = Array.from(
    document.querySelectorAll('.app-nav .nav-link, .app-bottombar .bottombar-link')
  );

  let maxLen = -1;
  const hits = [];
  links.forEach(function (link) {
    const href = link.getAttribute('href');
    if (!href) return;

    const clean = href.replace(/\/+$/, '');
    const matches =
      path === clean || (clean !== '' && path.startsWith(clean + '/'));

    if (matches) {
      hits.push({ link: link, len: clean.length });
      if (clean.length > maxLen) maxLen = clean.length;
    }
  });

  links.forEach(function (link) {
    const isActive = hits.some(function (h) {
      return h.link === link && h.len === maxLen;
    });
    link.classList.toggle('active', isActive);
  });
}

function dressDataTableControls(table) {
  const wrapper = table.closest('.dt-container') || table.closest('.dataTables_wrapper');
  if (!wrapper) return;

  wrapper.querySelectorAll('.dt-length select, .dataTables_length select')
    .forEach(function (sel) {
      sel.setAttribute('aria-label', 'Jumlah baris per halaman');
    });

  wrapper.querySelectorAll('.dt-search input, .dataTables_filter input')
    .forEach(function (input) {
      input.setAttribute('placeholder', 'Cari kata kunci…');
      input.setAttribute('aria-label', 'Cari');
    });
}

function initDataTables(scope) {
  const root = scope || document;
  root.querySelectorAll('table.table-datatable').forEach(function (table) {
    if (table.dataset.datatableInit === '1') return;
    if (typeof $.fn.DataTable === 'undefined') return;

    const isServerSide = table.dataset.serverSide === 'true';
    const ajaxUrl = table.dataset.ajaxUrl;

    const columnsConfig = []
    const $ths = $(table).find('thead th');

    $ths.each(function () {
      const $th = $(this);
      const key = $th.data('key');
      const label = $th.text().trim();
      const cellClass = $th.data('class') || '';
      const isOrderable = $th.data('orderable') !== false;
      const fmt = $th.data('fmt') || '';

      columnsConfig.push({
        data: key || null,
        name: key || '',
        orderable: isOrderable,
        className: cellClass,
        createdCell: function (td, cellData, rowData, rowIndex, colIndex) {
          $(td).attr('data-label', label);
        },
        render: function (data, type, row, meta) {
          if (row._custom_cells && row._custom_cells[key]) return row._custom_cells[key];
          if (type === 'display' && (fmt === 'date' || fmt === 'datetime')) {
            const d = new Date(data);
            if (!isNaN(d.getTime())) {
              const options = {
                day: '2-digit',
                month: 'short',
                year: 'numeric'
              };

              if (fmt === 'datetime') {
                options.hour = '2-digit';
                options.minute = '2-digit';
              }
              return new Intl.DateTimeFormat('id-ID', options).format(d);
            }
          }

          if (type === 'display'){
            if (fmt === 'idr' && data !== null && data !== undefined) {
              const num = parseFloat(data);
              if (!isNaN(num)) {
                return new Intl.NumberFormat('id-ID', {
                  style: 'currency',
                  currency: 'IDR',
                  maximumFractionDigits: 0
                }).format(num); // Output: Rp 150.000
              }
            }

            // 2. Format Currency Dolar (USD)
            if (fmt === 'usd' && data !== null && data !== undefined) {
              const num = parseFloat(data);
              if (!isNaN(num)) {
                return new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD'
                }).format(num); // Output: $150.00
              }
            }
          }

          return data !== null && data !== undefined ? data : '';
        }
      });
    })

    const dtOptions = {
      language: {
        search: '',
        searchPlaceholder: 'Cari kata kunci…',
        lengthMenu: 'Tampil _MENU_ baris',
        info: 'Menampilkan _START_–_END_ dari _TOTAL_ data',
        infoEmpty: 'Tidak ada data',
        infoFiltered: '(difilter dari _MAX_)',
        zeroRecords: 'Tidak ada data yang cocok',
        emptyTable: 'Belum ada data.',
        paginate: {
          first: '«',
          last: '»',
          next: '›',
          previous: '‹',
        },
      },
      stateSave: true,
      order: [[0, 'desc']],
      stateDuration: 7200,
      searchDelay: 1000,
      pageLength: 25,
      pagingType: 'simple_numbers',
      lengthMenu: [[5, 10, 25, 50, -1], [5, 10, 25, 50, 'Semua']],
      initComplete: function () {
        dressDataTableControls(table);
      },
    };

    // Tambahkan opsi Server-Side jika data-server-side="true"
    if (isServerSide && ajaxUrl) {
      dtOptions.serverSide = true;
      dtOptions.processing = true;
      dtOptions.ajax = {
        url: ajaxUrl,
        type: 'GET',
        cache: false,
        data: function (d) {
          const startDate = $('#start_date').val();
          const endDate = $('#end_date').val();
          if (startDate) d.start_date = startDate;
          if (endDate) d.end_date = endDate;

          const status_active = $('#status_active').is(':checked');
          const status_completed = $('#status_completed').is(':checked');
          if (status_active) d.status_active = status_active
          if (status_completed) d.status_completed = status_completed
        }
      };
      dtOptions.columns = columnsConfig;
    };

    $(table).DataTable(dtOptions);
    table.dataset.datatableInit = '1';
  });
}

// ---------- 3) Sort mobile (mode kartu) ----------
function initMobileSorting(scope) {
  const root = scope || document;
  root.querySelectorAll('table.table-datatable').forEach(function (table) {
    if (table.dataset.mobileSortBound === '1') return;
    if (typeof $.fn.DataTable === 'undefined') return;

    const wrap = table.closest('.tabel-component');
    if (!wrap || !wrap.classList.contains('tabel-mobile')) return;

    const api = $(table).DataTable();
    if (!api) return;
    table.dataset.mobileSortBound = '1';

    const headers = Array.from(
      table.querySelectorAll('thead th')
    ).map(function (th, idx) {
      return {
        label: (th.textContent || '').replace(/\s+/g, ' ').trim(),
        idx: idx,
      };
    });

    let orderable = [];
    try {
      orderable = api.columns().orderable() || [];
    } catch (e) {
      orderable = [];
    }

    const sortable = headers.map(function (_h, i) {
      const ok = orderable[i];
      return ok === undefined ? true : ok;
    });

    const bar = document.createElement('div');
    bar.className =
      'dt-mobile-sort d-md-none d-flex flex-wrap align-items-center gap-1 mb-2';

    const caption = document.createElement('span');
    caption.className = 'small text-secondary me-1';
    caption.textContent = 'Urutkan:';
    bar.appendChild(caption);

    const chips = [];
    headers.forEach(function (h) {
      if (!h.label || !sortable[h.idx]) return;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'dt-sort-chip';
      btn.dataset.col = String(h.idx);

      const label = document.createElement('span');
      label.className = 'dt-sort-label';
      label.textContent = h.label;

      const arrow = document.createElement('span');
      arrow.className = 'dt-sort-arrow';
      arrow.textContent = '↕';

      btn.appendChild(label);
      btn.appendChild(arrow);

      btn.addEventListener('click', function () {
        const order = api.order();
        const current = order && order[0] ? order[0] : [h.idx, 'asc'];
        let dir;
        if (current[0] === h.idx) {
          dir = current[1] === 'asc' ? 'desc' : 'asc';
        } else {
          dir = 'asc';
        }
        api.order([[h.idx, dir]]).draw();
      });

      bar.appendChild(btn);
      chips.push(btn);
    });

    function refreshSortChips() {
      const order = api.order();
      const currentIdx = order && order[0] ? order[0][0] : null;
      const currentDir = order && order[0] ? order[0][1] : 'asc';
      chips.forEach(function (btn) {
        const idx = parseInt(btn.dataset.col, 10);
        const active = idx === currentIdx;
        btn.classList.toggle('active', active);
        const arrow = btn.querySelector('.dt-sort-arrow');
        arrow.textContent = active ? (currentDir === 'asc' ? '↑' : '↓') : '↕';
      });
    }

    api.on('order.dt', refreshSortChips);
    const wrapper =
      table.closest('.dt-container') || table.closest('.dataTables_wrapper');
    const searchEl = wrapper
      ? wrapper.querySelector('.dt-search, .dataTables_filter')
      : null;
    const searchRow = searchEl
      ? searchEl.closest('.dt-layout-row, .dataTables_wrapper')
      : null;
    if (searchRow && searchRow.parentNode) {
      searchRow.insertAdjacentElement('afterend', bar);
    } else {
      table.before(bar);
    }
    refreshSortChips();
  });
}

// ---------- 4) Anti double-submit ----------
function bindAntiDoubleSubmit(scope) {
  const root = scope || document;
  root.querySelectorAll('form[data-disable-on-submit]').forEach(function (form) {
    if (form.dataset.disableBound === '1') return;
    form.addEventListener('submit', function () {
      const buttons = form.querySelectorAll('button[type="submit"]');
      buttons.forEach(function (btn) {
        btn.disabled = true;
        btn.setAttribute('data-original-html', btn.innerHTML);
        btn.innerHTML = 'Memproses…';
      });
    });
    form.dataset.disableBound = '1';
  });
}

function tooltipAction(scope) {
  const root = scope || document;
  const tooltipTriggerList = root.querySelectorAll('[data-bs-toggle="tooltip"]');

  tooltipTriggerList.forEach(function (tooltipTriggerEl) {
    new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Inisialisasi Semua Popover
  const popoverTriggerList = root.querySelectorAll('[data-bs-toggle="popover"]');
  popoverTriggerList.forEach(function (popoverTriggerEl) {
    new bootstrap.Popover(popoverTriggerEl);
  });
}

function filterBtn(){
  const $table = $('table.table-datatable');
  $('#btn-filter').on('click', function () {
    if ($.fn.DataTable.isDataTable($table)) {
      $table.DataTable().ajax.reload();
    }
  });
  // Event Klik Tombol Reset
  $('#btn-reset').on('click', function () {
    $('#start_date').val('');
    $('#end_date').val('');

    if ($.fn.DataTable.isDataTable($table)) {
      $table.DataTable().ajax.reload();
    }
    
  });
}

function updateWaktu() {
  const sekarang = new Date();
  const jam = String(sekarang.getHours()).padStart(2, '0');
  const menit = String(sekarang.getMinutes()).padStart(2, '0');
  const detik = String(sekarang.getSeconds()).padStart(2, '0');

  const timer = document.getElementById('jam');
  if (timer) document.getElementById('jam').textContent = `${jam}:${menit}:${detik}`;
}

updateWaktu();
setInterval(updateWaktu, 1000);


// Inisialisasi saat halaman dimuat & setelah swap htmx
function initApp(scope) {
  highlightActiveNav();
  initDataTables(scope);
  initMobileSorting(scope);
  bindAntiDoubleSubmit(scope);
  tooltipAction(scope);
  filterBtn()
  updateWaktu()
}

document.addEventListener('DOMContentLoaded', function () { initApp(document); });
document.addEventListener('htmx:afterSwap', function (evt) { initApp(evt.target); });
document.addEventListener('htmx:pushedIntoHistory', highlightActiveNav);
window.addEventListener('popstate', highlightActiveNav);

window.addEventListener('pageshow', function (event) {
    const currentPath = window.location.pathname;
    const uuidPattern = /[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/;

    const isTabelList = (currentPath.includes('/withdrawal/') || currentPath.includes('/deposit/')) 
                        && !uuidPattern.test(currentPath);

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    const dataChanged = getCookie('data_changed');
    if (isTabelList && dataChanged === 'true') {
        document.cookie = "data_changed=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        window.location.reload();
    }
});

document.body.addEventListener('htmx:historyRestore', function(evt) {
  const currentPath = evt.detail.path || window.location.pathname;
  const uuidPattern = /[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/;
  // const isDetail = (currentPath.includes('/withdrawal/') || currentPath.includes('/deposit/')) 
  //                   && uuidPattern.test(currentPath);

  // if (isDetail) {
  //     evt.preventDefault(); 
  //     window.location.reload();
  // }
});

document.addEventListener('htmx:afterSettle', function(evt) {

});