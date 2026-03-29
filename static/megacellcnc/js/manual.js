(function () {
  var input = document.getElementById('manualSearchInput');
  var main = document.getElementById('manual-main');
  if (!input || !main) return;

  var debounceTimer = null;

  function applySearch(raw) {
    var q = (raw || '').trim().toLowerCase();
    var h2s = Array.prototype.slice.call(main.querySelectorAll('h2'));

    h2s.forEach(function (h2, i) {
      var stop = h2s[i + 1];
      var el = h2;
      var group = [];
      while (el) {
        group.push(el);
        var next = el.nextElementSibling;
        if (!next || next === stop) break;
        el = next;
      }
      var text = group
        .map(function (e) {
          return e.textContent;
        })
        .join('\n')
        .toLowerCase();
      var show = !q || text.indexOf(q) !== -1;
      group.forEach(function (e) {
        if (show) e.classList.remove('manual-section-hidden');
        else e.classList.add('manual-section-hidden');
      });
    });

    var cur = main.firstElementChild;
    while (cur && cur.tagName !== 'H2') {
      if (cur.tagName === 'H1') {
        cur.classList.remove('manual-section-hidden');
      } else {
        var t = cur.textContent.toLowerCase();
        var showHead = !q || t.indexOf(q) !== -1;
        if (showHead) cur.classList.remove('manual-section-hidden');
        else cur.classList.add('manual-section-hidden');
      }
      cur = cur.nextElementSibling;
    }

    var toc = document.getElementById('manualToc');
    if (toc) {
      var items = toc.querySelectorAll('li');
      items.forEach(function (li) {
        var link = li.querySelector('a');
        var label = (link ? link.textContent : li.textContent).toLowerCase();
        if (q && label.indexOf(q) === -1) li.classList.add('toc-hidden');
        else li.classList.remove('toc-hidden');
      });
    }
  }

  input.addEventListener('input', function () {
    clearTimeout(debounceTimer);
    var v = input.value;
    debounceTimer = setTimeout(function () {
      applySearch(v);
    }, 200);
  });

  if (input.value) applySearch(input.value);
})();
